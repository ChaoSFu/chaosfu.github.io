# -*- coding: utf-8 -*-
"""
生成历史趋势数据
从存档中读取最近N天的数据，生成历史趋势 JSON
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict

def load_archive(archive_dir, date_str):
    """加载指定日期的存档数据"""
    archive_file = Path(archive_dir) / f"{date_str}.json"
    if not archive_file.exists():
        return None

    try:
        with open(archive_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  读取存档 {date_str} 失败: {e}")
        return None

def generate_history(archive_dir, days=7):
    """
    生成最近N天的历史趋势数据

    返回:
    {
        "dates": ["2025-11-01", "2025-11-02", ...],
        "market_trend": [
            {"date": "2025-11-01", "advice": "OFFENSE", "broad_strength": -0.18, "risk_on": false},
            ...
        ],
        "indices_trend": {
            "hs300": [0.006, -0.012, ...],
            "csi1000": [0.002, 0.015, ...],
            "shcomp": [0.004, -0.008, ...]
        },
        "hot_boards": [
            {
                "code": "BK1019",
                "name": "化学原料",
                "trend": [0.027, 0.035, ...],  # 每日涨跌幅
                "avg_score": 2.5,
                "days_on_list": 5  # 连续上榜天数
            },
            ...
        ],
        "board_rotation": {
            "2025-11-01": ["化学原料", "光伏设备", ...],
            ...
        }
    }
    """
    print(f"📊 生成最近 {days} 天的历史趋势数据...")
    print("=" * 60)

    # 获取日期列表（倒序：从今天往前推）
    dates = []
    today = date.today()
    for i in range(days):
        d = today - timedelta(days=i)
        dates.append(d.isoformat())
    dates = list(reversed(dates))  # 正序排列

    # 加载所有存档数据
    archives = {}
    for date_str in dates:
        data = load_archive(archive_dir, date_str)
        if data:
            archives[date_str] = data
            print(f"  ✅ {date_str}: {len(data.get('boards', []))} 个板块")
        else:
            print(f"  ⚠️  {date_str}: 无存档数据")

    if not archives:
        print("\n❌ 无可用的历史数据")
        return None

    # 提取市场趋势
    market_trend = []
    for date_str in dates:
        if date_str in archives:
            market = archives[date_str].get('market', {})
            market_trend.append({
                'date': date_str,
                'advice': market.get('advice', 'NEUTRAL'),
                'broad_strength': market.get('broad_strength', 0),
                'risk_on': market.get('risk_on', False)
            })

    # 提取指数趋势
    indices_trend = {
        'hs300': [],
        'csi1000': [],
        'shcomp': []
    }
    for date_str in dates:
        if date_str in archives:
            indices = archives[date_str].get('indices', {})
            indices_trend['hs300'].append(indices.get('hs300', {}).get('ret', None))
            indices_trend['csi1000'].append(indices.get('csi1000', {}).get('ret', None))
            indices_trend['shcomp'].append(indices.get('shcomp', {}).get('ret', None))
        else:
            indices_trend['hs300'].append(None)
            indices_trend['csi1000'].append(None)
            indices_trend['shcomp'].append(None)

    # 统计热门板块（出现在Top10的板块）
    board_stats = defaultdict(lambda: {
        'name': '',
        'trend': [],
        'scores': [],
        'dates': []
    })

    board_rotation = {}

    for date_str in dates:
        if date_str not in archives:
            continue

        boards = archives[date_str].get('boards', [])
        top10 = boards[:10]

        # 记录当日Top10
        board_rotation[date_str] = [b['name'] for b in top10]

        # 统计每个板块
        for board in top10:
            code = board['code']
            board_stats[code]['name'] = board['name']
            board_stats[code]['trend'].append(board['ret'])
            board_stats[code]['scores'].append(board.get('score', 0))
            board_stats[code]['dates'].append(date_str)

    # 计算热门板块（至少出现2天）
    hot_boards = []
    for code, stats in board_stats.items():
        if len(stats['dates']) >= 2:  # 至少出现2天
            avg_score = sum(stats['scores']) / len(stats['scores'])
            hot_boards.append({
                'code': code,
                'name': stats['name'],
                'trend': stats['trend'],
                'dates': stats['dates'],
                'avg_score': round(avg_score, 2),
                'days_on_list': len(stats['dates']),
                'avg_ret': round(sum(stats['trend']) / len(stats['trend']) * 100, 2)  # 平均涨幅(%)
            })

    # 按出现天数和平均分排序
    hot_boards.sort(key=lambda x: (x['days_on_list'], x['avg_score']), reverse=True)

    print(f"\n✅ 历史数据统计:")
    print(f"   有效天数: {len(archives)}/{days}")
    print(f"   热门板块: {len(hot_boards)} 个")

    return {
        'dates': dates,
        'available_dates': list(archives.keys()),
        'market_trend': market_trend,
        'indices_trend': indices_trend,
        'hot_boards': hot_boards[:20],  # Top 20
        'board_rotation': board_rotation,
        'generated_at': date.today().isoformat()
    }

def detect_new_boards(archive_dir, lookback_days=10):
    """
    检测新上榜的板块（前N个交易日都未进入前10）

    参数:
        archive_dir: 存档目录
        lookback_days: 回溯天数，默认10个交易日

    返回:
        {
            'industry': set(['BK1019', ...]),  # 新上榜的行业板块代码
            'concept': set(['BK0961', ...])     # 新上榜的概念板块代码
        }
    """
    today = date.today()

    # 获取今天的数据
    today_data = load_archive(archive_dir, today.isoformat())
    if not today_data:
        return {'industry': set(), 'concept': set()}

    # 获取今天的Top10板块（分类型）
    today_industry = set()
    today_concept = set()

    if 'industry_boards' in today_data:
        # 新格式
        today_industry = {b['code'] for b in today_data.get('industry_boards', [])[:10]}
        today_concept = {b['code'] for b in today_data.get('concept_boards', [])[:10]}
    elif 'boards' in today_data:
        # 旧格式兼容
        for b in today_data.get('boards', [])[:10]:
            if b.get('type') == 'concept':
                today_concept.add(b['code'])
            else:
                today_industry.add(b['code'])

    # 统计过去N天出现在Top10的板块
    historical_industry = set()
    historical_concept = set()

    for i in range(1, lookback_days + 1):
        past_date = today - timedelta(days=i)
        past_data = load_archive(archive_dir, past_date.isoformat())

        if past_data:
            if 'industry_boards' in past_data:
                # 新格式
                historical_industry.update(b['code'] for b in past_data.get('industry_boards', [])[:10])
                historical_concept.update(b['code'] for b in past_data.get('concept_boards', [])[:10])
            elif 'boards' in past_data:
                # 旧格式
                for b in past_data.get('boards', [])[:10]:
                    if b.get('type') == 'concept':
                        historical_concept.add(b['code'])
                    else:
                        historical_industry.add(b['code'])

    # 找出新上榜的板块（今天在Top10，但过去N天都不在）
    new_industry = today_industry - historical_industry
    new_concept = today_concept - historical_concept

    if new_industry or new_concept:
        print(f"\n🆕 检测到新上榜板块（前{lookback_days}个交易日未进入前10）:")
        if new_industry:
            print(f"  - 行业板块: {len(new_industry)} 个")
        if new_concept:
            print(f"  - 概念板块: {len(new_concept)} 个")

    return {
        'industry': new_industry,
        'concept': new_concept
    }

def save_history(history_data, output_path):
    """保存历史数据到 JSON 文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
    print(f"✅ 历史数据已保存: {output_path}")

def main():
    import argparse
    ap = argparse.ArgumentParser(description='生成历史趋势数据')
    ap.add_argument('--archive-dir', default='site/data/archive', help='存档目录')
    ap.add_argument('--days', type=int, default=7, help='历史天数')
    ap.add_argument('--out', default='site/data/history.json', help='输出文件')
    args = ap.parse_args()

    history = generate_history(args.archive_dir, args.days)

    if history:
        save_history(history, args.out)

        print("\n" + "=" * 60)
        print("📊 热门板块 Top 5:")
        for i, board in enumerate(history['hot_boards'][:5], 1):
            print(f"  {i}. {board['name']} - 上榜{board['days_on_list']}天, 平均涨幅{board['avg_ret']}%")
    else:
        print("\n❌ 历史数据生成失败")

if __name__ == '__main__':
    main()
