#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从东方财富获取板块历史数据
使用板块轮动API：RPT_BOARD_WHEEL
"""

import urllib.request
import urllib.parse
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

def fetch_board_wheel_history(days=10, top_n=20):
    """
    获取板块轮动历史数据（涨幅榜）

    参数:
        days: 获取最近N个交易日
        top_n: 每日获取Top N个板块（会按BK代码分类为行业和概念）

    返回:
        (industry_history, concept_history) - 按日期分组的行业和概念板块数据
    """
    base_url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"

    params = {
        'reportName': 'RPT_BOARD_WHEEL',
        'columns': 'BOARD_CODE,BOARD_NAME,TRADE_DATE,INDICATORID,INDICATORID_RANK,COMMON_TYPE3',
        'filter': f'(COMMON_TYPE1="001")(COMMON_TYPE2="2")(COMMON_TYPE3="01")(INDICATORID_RANK<={top_n})',
        'source': 'SECURITIES',
        'client': 'APP',
        'sortColumns': 'TRADE_DATE,INDICATORID_RANK',
        'sortTypes': '-1,1',  # 日期降序，排名升序
        'pageNumber': '1',
        'pageSize': str(days * top_n + 100),  # 多取一些，确保有足够数据
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://emdata.eastmoney.com/'
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        if not data.get('success'):
            print(f"❌ API返回失败: {data.get('message')}")
            return {}

        records = data.get('result', {}).get('data', [])
        print(f"  获取到 {len(records)} 条原始记录")

        # 按日期分组，并按BK代码分类
        industry_by_date = defaultdict(list)
        concept_by_date = defaultdict(list)

        for r in records:
            trade_date = r['TRADE_DATE'][:10]  # 只取日期部分 YYYY-MM-DD
            code = r['BOARD_CODE']

            board_data = {
                'code': code,
                'name': r['BOARD_NAME'],
                'rank': r['INDICATORID_RANK'],
                'score': float(r['INDICATORID']) if r['INDICATORID'] else 0,
            }

            # 按BK代码前缀分类
            if code.startswith('BK1'):
                # BK1xxx = 行业板块
                industry_by_date[trade_date].append(board_data)
            elif code.startswith('BK0'):
                # BK0xxx = 概念板块
                concept_by_date[trade_date].append(board_data)

        # 只保留最近N个交易日，每类取前10个
        sorted_dates = sorted(set(list(industry_by_date.keys()) + list(concept_by_date.keys())), reverse=True)[:days]

        industry_result = {}
        concept_result = {}

        for date in sorted_dates:
            # 按得分降序排序，取前10个
            if date in industry_by_date:
                industry_result[date] = sorted(industry_by_date[date], key=lambda x: -x['score'])[:10]
            if date in concept_by_date:
                concept_result[date] = sorted(concept_by_date[date], key=lambda x: -x['score'])[:10]

        print(f"  提取出 {len(sorted_dates)} 个交易日的数据")
        print(f"    行业板块: {sum(len(boards) for boards in industry_result.values())} 条")
        print(f"    概念板块: {sum(len(boards) for boards in concept_result.values())} 条")

        return industry_result, concept_result

    except Exception as e:
        print(f"❌ 获取失败: {e}")
        return {}

def main():
    print("📊 获取板块历史数据（最近10个交易日）")
    print("=" * 60)

    # 获取板块历史（自动分类为行业和概念）
    print("\n🔄 从东方财富获取板块轮动数据...")
    industry_history, concept_history = fetch_board_wheel_history(days=10, top_n=30)

    # 显示结果
    print("\n" + "=" * 60)
    print("📈 数据概览")
    print("=" * 60)

    all_dates = sorted(set(list(industry_history.keys()) + list(concept_history.keys())), reverse=True)

    print(f"\n共获取 {len(all_dates)} 个交易日的数据:")
    for i, date in enumerate(all_dates[:10], 1):
        industry_count = len(industry_history.get(date, []))
        concept_count = len(concept_history.get(date, []))
        print(f"  {i}. {date}: 行业 {industry_count}个, 概念 {concept_count}个")

    # 显示示例数据
    if all_dates:
        latest_date = all_dates[0]
        print(f"\n📋 示例: {latest_date}")

        if latest_date in industry_history:
            print(f"\n  行业板块 Top 5:")
            for board in industry_history[latest_date][:5]:
                print(f"    {board['rank']}. {board['code']} - {board['name']} (得分: {board['score']:.2f})")

        if latest_date in concept_history:
            print(f"\n  概念板块 Top 5:")
            for board in concept_history[latest_date][:5]:
                print(f"    {board['rank']}. {board['code']} - {board['name']} (得分: {board['score']:.2f})")

    return industry_history, concept_history

def save_to_archive(industry_history, concept_history, archive_dir):
    """
    将历史数据保存到archive目录

    注意：这些历史数据不包含详细的市场指标和个股信息，
    仅包含板块排名和得分，用于填充历史记录
    """
    print("\n💾 保存历史数据到archive目录...")
    os.makedirs(archive_dir, exist_ok=True)

    all_dates = sorted(set(list(industry_history.keys()) + list(concept_history.keys())), reverse=True)

    saved_count = 0
    for date in all_dates:
        # 构建存档数据格式（简化版）
        archive_data = {
            'date': date,
            'source': 'history_backfill',  # 标记这是历史回填数据
            'market': {
                'risk_on': True,  # 默认值
                'broad_strength': 0,
                'advice': 'NEUTRAL'
            },
            'industry_boards': [],
            'concept_boards': [],
            'indices': {
                'hs300': {'ret': 0},
                'csi1000': {'ret': 0},
                'shcomp': {'ret': 0}
            },
            'disclaimer': '本数据为历史回填数据，仅包含板块排名信息，不包含详细指标和个股数据。'
        }

        # 添加行业板块
        for board in industry_history.get(date, []):
            archive_data['industry_boards'].append({
                'code': board['code'],
                'name': board['name'],
                'type': 'industry',
                'ret': board['score'] / 100,  # 得分转为百分比
                'pop': 0,  # 历史数据无此字段
                'persistence': 0,
                'dispersion': 0,
                'breadth': 0,
                'score': board['score'],
                'stance': 'BUY' if board['score'] > 0 else 'WATCH',
                'is_new': False,
                'core_stocks': []
            })

        # 添加概念板块
        for board in concept_history.get(date, []):
            archive_data['concept_boards'].append({
                'code': board['code'],
                'name': board['name'],
                'type': 'concept',
                'ret': board['score'] / 100,
                'pop': 0,
                'persistence': 0,
                'dispersion': 0,
                'breadth': 0,
                'score': board['score'],
                'stance': 'BUY' if board['score'] > 0 else 'WATCH',
                'is_new': False,
                'core_stocks': []
            })

        # 保存到文件
        archive_file = os.path.join(archive_dir, f"{date}.json")

        # 检查文件是否已存在
        if os.path.exists(archive_file):
            print(f"  ⏭️  {date}: 已存在，跳过")
            continue

        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ {date}: 行业 {len(archive_data['industry_boards'])}个, 概念 {len(archive_data['concept_boards'])}个")
        saved_count += 1

    print(f"\n✅ 成功保存 {saved_count} 个交易日的历史数据")
    return saved_count

if __name__ == '__main__':
    industry_history, concept_history = main()

    # 保存到archive
    if industry_history or concept_history:
        archive_dir = 'stock-analysis/data/archive'
        save_to_archive(industry_history, concept_history, archive_dir)
    else:
        print("\n❌ 没有获取到历史数据，跳过保存")
