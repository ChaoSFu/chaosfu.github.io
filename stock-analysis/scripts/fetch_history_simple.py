#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用urllib获取东方财富板块历史数据（不依赖requests）
"""

import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta

def fetch_board_history_datacenter(board_code, board_type='industry', days=10):
    """
    尝试使用数据中心API获取板块历史数据

    参数:
        board_code: 板块代码，如 BK0538
        board_type: 'industry' 或 'concept'
        days: 获取最近N天的数据
    """
    # 东方财富数据中心API（根据类似产品推测）
    base_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"

    # 推测参数（需要实际测试）
    params = {
        'reportName': 'RPT_WEB_PLATE_TREND',  # 板块趋势报表
        'columns': 'ALL',
        'filter': f'(BOARD_CODE="{board_code}")',
        'pageNumber': '1',
        'pageSize': str(days + 10),
        'sortTypes': '-1',
        'sortColumns': 'TRADE_DATE',
        'source': 'WEB',
        'client': 'WEB',
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        print(f"DEBUG [datacenter] - URL: {url[:150]}...")
        print(f"DEBUG [datacenter] - Response keys: {list(data.keys())}")

        if 'result' in data and data['result'] is not None:
            result = data['result']
            if 'data' in result:
                return result['data']

        print(f"⚠️  [datacenter] API返回: {json.dumps(data, ensure_ascii=False)[:300]}")
        return []

    except Exception as e:
        print(f"❌ [datacenter] 获取失败: {e}")
        return []

def fetch_board_history(board_code, days=10):
    """
    获取板块历史K线数据（使用K线API）

    参数:
        board_code: 板块代码，如 BK0538
        days: 获取最近N天的数据
    """
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days+10)  # 多取几天确保有足够交易日

    # 构建URL
    base_url = "https://push2delay.eastmoney.com/api/qt/stock/kline/get"
    params = {
        'secid': f'90.{board_code}',  # 90 = 板块
        'fields1': 'f1,f2,f3,f4,f5',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
        # f51=日期, f52=开盘, f53=收盘, f54=最高, f55=最低, f56=成交量, f57=成交额, f58=涨跌幅
        'klt': '101',  # 日K
        'fqt': '0',    # 不复权
        'beg': start_date.strftime('%Y%m%d'),
        'end': end_date.strftime('%Y%m%d'),
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        }

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        print(f"DEBUG - URL: {url}")
        print(f"DEBUG - Response RC: {data.get('rc')}")
        print(f"DEBUG - Response keys: {list(data.keys())}")

        if data.get('rc') == 0 and 'data' in data:
            data_obj = data['data']
            print(f"DEBUG - Data keys: {list(data_obj.keys()) if isinstance(data_obj, dict) else 'not a dict'}")
            if isinstance(data_obj, dict):
                print(f"DEBUG - Data content: {json.dumps(data_obj, ensure_ascii=False)[:300]}")

            klines = data_obj.get('klines', []) if isinstance(data_obj, dict) else []
            print(f"DEBUG - Klines count: {len(klines)}")
            return klines
        else:
            print(f"⚠️  API返回异常: {json.dumps(data, ensure_ascii=False)[:500]}")
            return []

    except Exception as e:
        print(f"❌ 获取失败: {e}")
        return []

def parse_kline(kline_str):
    """
    解析K线字符串
    格式: "日期,开盘,收盘,最高,最低,成交量,成交额,涨跌幅,..."
    """
    parts = kline_str.split(',')
    if len(parts) < 8:
        return None

    return {
        'date': parts[0],
        'open': float(parts[1]),
        'close': float(parts[2]),
        'high': float(parts[3]),
        'low': float(parts[4]),
        'volume': float(parts[5]),
        'turnover': float(parts[6]),
        'pct_change': float(parts[7]),  # 涨跌幅（百分比）
    }

if __name__ == '__main__':
    # 测试：获取化学制品板块的历史数据
    print("🧪 测试获取板块历史数据...\n")

    test_code = 'BK0538'  # 化学制品

    # 先尝试数据中心API
    print("=" * 60)
    print("方法1: 数据中心API")
    print("=" * 60)
    data_center_result = fetch_board_history_datacenter(test_code, days=15)
    if data_center_result:
        print(f"✅ 成功！获取到 {len(data_center_result)} 条数据")
        if len(data_center_result) > 0:
            print(f"示例数据: {json.dumps(data_center_result[0], ensure_ascii=False, indent=2)}")
    else:
        print("未获取到数据\n")

    # 再尝试K线API
    print("\n" + "=" * 60)
    print("方法2: K线API")
    print("=" * 60)
    klines = fetch_board_history(test_code, days=15)

    print(f"板块代码: {test_code}")
    print(f"获取到 {len(klines)} 条K线数据\n")

    if klines:
        print("最近5个交易日:")
        for kline_str in klines[-5:]:
            kline = parse_kline(kline_str)
            if kline:
                print(f"  {kline['date']}: 涨跌幅 {kline['pct_change']:.2f}%, 成交额 {kline['turnover']/1e8:.2f}亿")
