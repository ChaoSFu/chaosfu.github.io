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

def generate_main_indices_history(archives, dates):
    """
    生成主要指数的历史OHLC数据（从archive中读取）

    返回:
    {
        "dates": ["2025-11-01", "2025-11-02", ...],
        "main_indices": {
            "HS300": [
                {"open": 3200.5, "close": 3220.8, "low": 3195.2, "high": 3230.1, "ret": 0.006, "volume": 1800000},
                ...
            ],
            "CSI500": [...],
            "CSI1000": [...],
            "CSI2000": [...]
        }
    }
    """
    # 主要指数列表
    main_index_codes = ['HS300', 'CSI500', 'CSI1000', 'CSI2000']

    main_indices = {code: [] for code in main_index_codes}

    for date_str in dates:
        if date_str not in archives:
            # 如果该日期没有数据,填充空数据
            for code in main_index_codes:
                main_indices[code].append(None)
            continue

        indices = archives[date_str].get('indices', {})

        for code in main_index_codes:
            index_data = indices.get(code, {})
            if index_data and isinstance(index_data, dict):
                # 提取OHLC数据
                main_indices[code].append({
                    'open': index_data.get('open', 0),
                    'close': index_data.get('close', 0),
                    'low': index_data.get('low', 0),
                    'high': index_data.get('high', 0),
                    'ret': index_data.get('ret', 0),
                    'volume': index_data.get('volume', 0)
                })
            else:
                # 数据缺失
                main_indices[code].append(None)

    return {
        'dates': dates,
        'main_indices': main_indices
    }


def generate_main_indices_history_from_api(days=30):
    """
    从东方财富API获取主要指数的真实历史K线数据

    参数:
        days: 获取最近N天的K线数据，默认30天

    返回:
    {
        "dates": ["2025-11-01", "2025-11-02", ...],
        "main_indices": {
            "HS300": [
                {"open": 3200.5, "close": 3220.8, "low": 3195.2, "high": 3230.1, "ret": 0.006, "volume": 1800000},
                ...
            ],
            "CSI500": [...],
            "CSI1000": [...],
            "CSI2000": [...]
        }
    }
    """
    print(f"📊 从东方财富API获取主要指数历史K线数据（最近{days}天）...")
    print("=" * 60)

    try:
        from eastmoney import fetch_index_kline
    except ImportError:
        print("❌ 无法导入eastmoney模块")
        return None

    # 主要指数列表
    main_index_codes = ['HS300', 'CSI500', 'CSI1000', 'CSI2000']

    # 存储所有指数的K线数据
    all_klines = {}
    dates_set = set()

    # 获取每个指数的K线数据
    for code in main_index_codes:
        df = fetch_index_kline(code, days=days)
        if df is not None and not df.empty:
            all_klines[code] = df
            dates_set.update(df['date'].tolist())
            print(f"  ✅ {code}: {len(df)} 条数据")
        else:
            print(f"  ⚠️  {code}: 获取失败")
            all_klines[code] = None

    if not dates_set:
        print("❌ 没有获取到任何K线数据")
        return None

    # 按日期排序
    dates = sorted(list(dates_set))

    # 组织数据结构
    main_indices = {code: [] for code in main_index_codes}

    for date_str in dates:
        for code in main_index_codes:
            if all_klines[code] is None:
                main_indices[code].append(None)
                continue

            # 查找该日期的数据
            df = all_klines[code]
            row = df[df['date'] == date_str]

            if not row.empty:
                data = row.iloc[0]
                main_indices[code].append({
                    'open': float(data['open']),
                    'close': float(data['close']),
                    'low': float(data['low']),
                    'high': float(data['high']),
                    'ret': float(data['ret']),
                    'volume': float(data['volume'])
                })
            else:
                main_indices[code].append(None)

    print(f"\n✅ K线数据汇总:")
    print(f"   日期范围: {dates[0]} ~ {dates[-1]}")
    print(f"   总天数: {len(dates)}")

    return {
        'dates': dates,
        'main_indices': main_indices
    }

def generate_history(archive_dir, days=7):
    """
    生成最近N个交易日的历史趋势数据

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
    print(f"📊 生成最近 {days} 个交易日的历史趋势数据...")
    print("=" * 60)

    # 获取存档目录中的所有可用日期（交易日）
    archive_path = Path(archive_dir)
    available_files = sorted(archive_path.glob("*.json"), reverse=True)  # 倒序排列

    # 提取日期并过滤掉非日期格式的文件
    all_dates = []
    for f in available_files:
        date_str = f.stem
        try:
            # 验证是否为有效的日期格式 YYYY-MM-DD
            date.fromisoformat(date_str)
            all_dates.append(date_str)
        except ValueError:
            continue

    # 取最近N个交易日
    dates = all_dates[:days]
    dates = list(reversed(dates))  # 正序排列

    print(f"  找到 {len(all_dates)} 个交易日的存档数据")
    print(f"  使用最近 {len(dates)} 个交易日")

    # 加载所有存档数据
    archives = {}
    for date_str in dates:
        data = load_archive(archive_dir, date_str)
        if data:
            archives[date_str] = data
            boards_count = len(data.get('industry_boards', [])) + len(data.get('concept_boards', []))
            if boards_count == 0:
                boards_count = len(data.get('boards', []))
            print(f"  ✅ {date_str}: {boards_count} 个板块")
        else:
            print(f"  ⚠️  {date_str}: 无法读取数据")

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

    # 提取指数趋势（支持5个新指数）
    indices_trend = {
        'CSI100': [],     # 中证100（超大盘）
        'HS300': [],      # 沪深300（大盘）
        'CSI500': [],     # 中证500（中盘）
        'CSI1000': [],    # 中证1000（小盘）
        'CSI2000': [],    # 中证2000（微盘）
        'SHCOMP': [],     # 上证指数
        # 保留旧的小写key用于兼容
        'hs300': [],
        'csi1000': [],
        'shcomp': []
    }

    for date_str in dates:
        if date_str in archives:
            indices = archives[date_str].get('indices', {})

            # 新的大写格式（优先使用）
            indices_trend['CSI100'].append(indices.get('CSI100', {}).get('ret', None))
            indices_trend['HS300'].append(indices.get('HS300', {}).get('ret', None))
            indices_trend['CSI500'].append(indices.get('CSI500', {}).get('ret', None))
            indices_trend['CSI1000'].append(indices.get('CSI1000', {}).get('ret', None))
            indices_trend['CSI2000'].append(indices.get('CSI2000', {}).get('ret', None))
            indices_trend['SHCOMP'].append(indices.get('SHCOMP', {}).get('ret', None))

            # 旧的小写格式（向后兼容）
            indices_trend['hs300'].append(indices.get('hs300', {}).get('ret', None))
            indices_trend['csi1000'].append(indices.get('csi1000', {}).get('ret', None))
            indices_trend['shcomp'].append(indices.get('shcomp', {}).get('ret', None))
        else:
            # 所有指数设为None
            for key in indices_trend.keys():
                indices_trend[key].append(None)

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

    # 生成主要指数的历史OHLC数据
    # 优先使用archive数据，保持与板块数据的一致性
    main_indices_history = generate_main_indices_history(archives, dates)

    # 生成最近10天的每日详细数据
    daily_records = []
    recent_dates = dates[-10:] if len(dates) >= 10 else dates  # 取最近10天

    for date_str in reversed(recent_dates):  # 倒序：最新的在前面
        if date_str in archives:
            archive_data = archives[date_str]

            # 提取数据（兼容新旧格式）
            daily_record = {
                'date': date_str,
                'market': archive_data.get('market', {}),
                'indices': archive_data.get('indices', {})
            }

            # 处理板块数据
            if 'industry_boards' in archive_data and 'concept_boards' in archive_data:
                # 新格式：已经分类好了
                daily_record['industry_boards'] = archive_data.get('industry_boards', [])[:10]
                daily_record['concept_boards'] = archive_data.get('concept_boards', [])[:10]
            elif 'boards' in archive_data:
                # 旧格式：按板块代码分类
                # BK0xxx = 概念板块, BK1xxx = 行业板块
                boards = archive_data.get('boards', [])
                industry = []
                concept = []

                for b in boards:
                    code = b.get('code', '')

                    # 如果有明确的 type 字段，使用它
                    if 'type' in b:
                        if b['type'] == 'concept':
                            concept.append(b)
                        else:
                            industry.append(b)
                    # 否则根据板块代码前缀判断
                    elif code.startswith('BK0'):
                        # BK0xxx 通常是概念板块
                        b_copy = b.copy()
                        b_copy['type'] = 'concept'
                        concept.append(b_copy)
                    elif code.startswith('BK1'):
                        # BK1xxx 通常是行业板块
                        b_copy = b.copy()
                        b_copy['type'] = 'industry'
                        industry.append(b_copy)
                    else:
                        # 未知类型，默认归类为行业
                        b_copy = b.copy()
                        b_copy['type'] = 'industry'
                        industry.append(b_copy)

                daily_record['industry_boards'] = industry[:10]
                daily_record['concept_boards'] = concept[:10]
            else:
                daily_record['industry_boards'] = []
                daily_record['concept_boards'] = []

            daily_records.append(daily_record)

    print(f"\n✅ 历史数据统计:")
    print(f"   有效天数: {len(archives)}/{days}")
    print(f"   热门板块: {len(hot_boards)} 个")
    print(f"   每日记录: {len(daily_records)} 天")

    return {
        'dates': dates,
        'available_dates': list(archives.keys()),
        'market_trend': market_trend,
        'indices_trend': indices_trend,
        'main_indices_history': main_indices_history,  # 新增：主要指数历史OHLC数据
        'hot_boards': hot_boards[:20],  # Top 20
        'board_rotation': board_rotation,
        'daily_records': daily_records,  # 新增：每日详细数据
        'generated_at': date.today().isoformat()
    }

def detect_new_boards(archive_dir, today_industry_boards=None, today_concept_boards=None, lookback_days=10):
    """
    检测新上榜的板块（前N个交易日都未进入前10）

    参数:
        archive_dir: 存档目录
        today_industry_boards: 今天的行业板块列表（可选，如果提供则不从存档读取）
        today_concept_boards: 今天的概念板块列表（可选，如果提供则不从存档读取）
        lookback_days: 回溯天数，默认10个交易日

    返回:
        {
            'industry': set(['BK1019', ...]),  # 新上榜的行业板块代码
            'concept': set(['BK0961', ...])     # 新上榜的概念板块代码
        }
    """
    # 获取存档目录中的所有可用日期（交易日），按时间倒序
    archive_path = Path(archive_dir)
    available_files = sorted(archive_path.glob("*.json"), reverse=True)

    all_dates = []
    for f in available_files:
        date_str = f.stem
        try:
            date.fromisoformat(date_str)
            all_dates.append(date_str)
        except ValueError:
            continue

    # 获取今天的Top10板块（分类型）
    today_industry = set()
    today_concept = set()

    if today_industry_boards is not None and today_concept_boards is not None:
        # 使用传入的今天的板块列表
        today_industry = {b['code'] for b in today_industry_boards[:10]}
        today_concept = {b['code'] for b in today_concept_boards[:10]}
    elif len(all_dates) > 0:
        # 从存档中读取最新交易日的数据（用于向后兼容）
        latest_date = all_dates[0]
        today_data = load_archive(archive_dir, latest_date)
        if not today_data:
            return {'industry': set(), 'concept': set()}

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
    else:
        return {'industry': set(), 'concept': set()}

    # 统计过去N个交易日出现在Top10的板块
    historical_industry = set()
    historical_concept = set()

    # 取过去N个交易日（从存档中的所有日期开始）
    past_dates = all_dates[:lookback_days]

    for past_date_str in past_dates:
        past_data = load_archive(archive_dir, past_date_str)

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
    ap.add_argument('--use-api', action='store_true', help='使用东方财富API获取真实K线数据（而不是从archive读取）')
    ap.add_argument('--kline-days', type=int, default=30, help='获取K线数据的天数（当--use-api时使用）')
    args = ap.parse_args()

    history = generate_history(args.archive_dir, args.days)

    if history:
        # 如果使用API获取K线数据，替换main_indices_history
        if args.use_api:
            print("\n" + "=" * 60)
            print("🔄 使用东方财富API获取真实K线数据...")
            main_indices_history_api = generate_main_indices_history_from_api(days=args.kline_days)
            if main_indices_history_api:
                history['main_indices_history'] = main_indices_history_api
                print("✅ 成功替换为真实K线数据")
            else:
                print("⚠️  API获取失败，使用archive数据")

        save_history(history, args.out)

        print("\n" + "=" * 60)
        print("📊 热门板块 Top 5:")
        for i, board in enumerate(history['hot_boards'][:5], 1):
            print(f"  {i}. {board['name']} - 上榜{board['days_on_list']}天, 平均涨幅{board['avg_ret']}%")

        print("\n📊 主要指数K线数据:")
        if 'main_indices_history' in history:
            mih = history['main_indices_history']
            print(f"  日期范围: {mih['dates'][0]} ~ {mih['dates'][-1]}")
            print(f"  总天数: {len(mih['dates'])}")
            for code in ['HS300', 'CSI500', 'CSI1000', 'CSI2000']:
                if code in mih['main_indices']:
                    valid_count = sum(1 for x in mih['main_indices'][code] if x is not None)
                    print(f"  {code}: {valid_count}/{len(mih['dates'])} 条有效数据")
    else:
        print("\n❌ 历史数据生成失败")

if __name__ == '__main__':
    main()
