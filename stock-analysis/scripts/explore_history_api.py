#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探索东方财富板块历史数据API
URL: https://emdata.eastmoney.com/appdc/bkld/index.html
"""

import requests
import json
from datetime import datetime, timedelta

# 尝试不同的API endpoint
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://emdata.eastmoney.com/'
}

def explore_api():
    """探索可能的API endpoint"""

    # 尝试1: 板块历史数据接口（根据类似网站的经验）
    possible_endpoints = [
        # 板块历史涨跌幅
        "https://push2.eastmoney.com/api/qt/stock/kline/get",
        "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "https://datacenter.eastmoney.com/securities/api/data/get",
        # 板块列表
        "https://emdata.eastmoney.com/pc/bk/getbklist",
        "https://emdata.eastmoney.com/pc/bk/history",
    ]

    print("🔍 探索东方财富板块历史数据API...\n")

    # 先尝试获取一个具体板块的历史数据
    # BK0538 = 化学制品（从之前的数据知道）
    test_board_code = "BK0538"

    # 尝试K线接口
    print("=" * 60)
    print("尝试1: K线接口（获取板块历史涨跌幅）")
    print("=" * 60)

    url = "https://push2.eastmoney.com/api/qt/stock/kline/get"

    # 计算日期范围（最近10个交易日，约15天）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=15)

    params = {
        'secid': f'90.{test_board_code}',  # 90 = 板块市场代码
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt': '101',  # K线类型：101=日K
        'fqt': '0',    # 复权类型：0=不复权
        'beg': start_date.strftime('%Y%m%d'),
        'end': end_date.strftime('%Y%m%d'),
    }

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()

        print(f"请求URL: {response.url}\n")
        print(f"状态码: {response.status_code}")
        print(f"返回数据: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...\n")

        if data.get('rc') == 0 and 'data' in data:
            klines = data['data'].get('klines', [])
            print(f"✅ 成功！获取到 {len(klines)} 条历史数据")
            print(f"示例数据: {klines[:3]}\n")
            return True
    except Exception as e:
        print(f"❌ 失败: {e}\n")

    return False

if __name__ == '__main__':
    explore_api()
