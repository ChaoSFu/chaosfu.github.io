# -*- coding: utf-8 -*-
"""
东方财富数据抓取模块
数据源：东方财富网公开 API
"""
import requests
import pandas as pd
from datetime import date, datetime
import time
import json

# 配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://data.eastmoney.com/'
}

def fetch_board_data():
    """
    获取板块涨跌幅排行数据
    API: 东方财富板块排行接口
    """
    url = "http://push2.eastmoney.com/api/qt/clist/get"

    params = {
        'fid': 'f3',        # 排序字段：f3=涨跌幅
        'po': '1',          # 排序：1=降序
        'pz': '100',        # 每页数量
        'pn': '1',          # 页码
        'np': '1',          # 不分页
        'fltt': '2',        # 过滤条件
        'invt': '2',        #
        'fs': 'm:90+t:2',   # 市场分类：90=板块，t:2=行业板块
        'fields': 'f12,f14,f2,f3,f5,f6,f8,f104,f105,f106,f128,f136,f137,f138'
        # f12=code, f14=name, f2=price, f3=pct_change, f5=volume, f6=turnover
        # f104=上涨家数, f105=下跌家数, f128=领涨股, f136=涨速, f137=换手率
    }

    try:
        print(f"  [板块] 请求东方财富板块数据...")
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('rc') != 0 or 'data' not in data:
            print(f"  [板块] ⚠️  API返回异常: {data}")
            return None

        boards = data['data']['diff']
        print(f"  [板块] ✅ 成功获取 {len(boards)} 个板块数据")

        # 转换为 DataFrame
        records = []
        today = date.today().isoformat()

        for item in boards:
            # f3: 涨跌幅(%), f2: 最新价, f5: 成交量, f6: 成交额
            # f104: 上涨家数, f138: 涨停家数
            pct = item.get('f3', 0) / 100.0  # 百分比转小数
            price = item.get('f2', 0)

            records.append({
                'date': today,
                'bk_code': item.get('f12', ''),
                'bk_name': item.get('f14', ''),
                'close': price,
                'prev_close': price / (1 + pct) if pct != -1 else price,
                'turnover': item.get('f6', 0),  # 成交额(元)
                'up_count': item.get('f104', 0),  # 上涨家数
                'limit_up': item.get('f138', 0),  # 涨停家数
            })

        df = pd.DataFrame(records)
        return df

    except requests.exceptions.RequestException as e:
        print(f"  [板块] ❌ 请求失败: {e}")
        return None
    except Exception as e:
        print(f"  [板块] ❌ 数据解析失败: {e}")
        return None


def fetch_board_stocks(board_code, top_n=10):
    """
    获取指定板块的成分股数据
    """
    url = "http://push2.eastmoney.com/api/qt/clist/get"

    params = {
        'fid': 'f3',
        'po': '1',
        'pz': str(top_n),
        'pn': '1',
        'np': '1',
        'fltt': '2',
        'invt': '2',
        'fs': f'b:{board_code}',  # 板块代码
        'fields': 'f12,f14,f2,f3,f5,f6,f7,f8,f15,f16,f17,f18'
        # f12=code, f14=name, f2=price, f3=pct, f5=volume, f6=turnover
        # f7=amplitude, f8=turnover_rate, f15=high, f16=low, f17=open
    }

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('rc') != 0 or 'data' not in data:
            return []

        stocks = data['data'].get('diff', [])

        records = []
        today = date.today().isoformat()

        for item in stocks:
            pct = item.get('f3', 0) / 100.0
            price = item.get('f2', 0)

            records.append({
                'date': today,
                'bk_code': board_code,
                'ts_code': item.get('f12', ''),
                'name': item.get('f14', ''),
                'close': price,
                'prev_close': price / (1 + pct) if pct != -1 else price,
                'turnover': item.get('f6', 0),
                'turnover_ratio': item.get('f8', 0),
                'amplitude': item.get('f7', 0),
            })

        return records

    except Exception as e:
        print(f"  [个股] ⚠️  获取板块 {board_code} 成分股失败: {e}")
        return []


def fetch_index_data():
    """
    获取主要指数数据（沪深300、中证1000、上证指数）
    """
    url = "http://push2.eastmoney.com/api/qt/ulist.np/get"

    # secids 格式: 市场代码.指数代码
    # 1.000300=沪深300, 1.000852=中证1000, 1.000001=上证指数
    params = {
        'secids': '1.000300,1.000852,1.000001',
        'fields': 'f12,f14,f2,f3,f4,f5,f6'
        # f3=涨跌幅, f4=涨跌额
    }

    try:
        print(f"  [指数] 请求东方财富指数数据...")
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('rc') != 0 or 'data' not in data:
            print(f"  [指数] ⚠️  API返回异常")
            return None

        indices = data['data']['diff']
        print(f"  [指数] ✅ 成功获取 {len(indices)} 个指数数据")

        # 映射：东方财富代码 -> 我们的代码
        code_map = {
            '000300': 'HS300',
            '000852': 'CSI1000',
            '000001': 'SHCOMP'
        }

        records = []
        today = date.today().isoformat()

        for item in indices:
            code = item.get('f12', '')
            if code in code_map:
                records.append({
                    'date': today,
                    'index_code': code_map[code],
                    'ret': item.get('f3', 0) / 100.0  # 涨跌幅转小数
                })

        df = pd.DataFrame(records)
        return df

    except Exception as e:
        print(f"  [指数] ❌ 请求失败: {e}")
        return None


def load_eastmoney_data(top_boards=20, stocks_per_board=10):
    """
    加载东方财富完整数据

    参数:
        top_boards: 抓取前N个板块
        stocks_per_board: 每个板块抓取前N只个股

    返回:
        (boards_df, stocks_df, indices_df)
    """
    print("📡 开始从东方财富获取实时数据...")
    print("=" * 50)

    # 1. 获取板块数据
    boards_df = fetch_board_data()
    if boards_df is None or boards_df.empty:
        raise Exception("板块数据获取失败")

    # 只保留前N个板块
    boards_df = boards_df.head(top_boards)
    print(f"\n  ✅ 已筛选 Top {len(boards_df)} 板块")

    # 延迟，避免请求过快
    time.sleep(0.5)

    # 2. 获取每个板块的成分股
    print(f"\n  [个股] 开始获取板块成分股（每板块 Top {stocks_per_board}）...")
    all_stocks = []

    for idx, row in boards_df.iterrows():
        bk_code = row['bk_code']
        bk_name = row['bk_name']

        stocks = fetch_board_stocks(bk_code, top_n=stocks_per_board)
        all_stocks.extend(stocks)

        print(f"    {idx+1}/{len(boards_df)} {bk_name}({bk_code}): {len(stocks)} 只个股")

        # 延迟，避免请求过快
        if idx < len(boards_df) - 1:
            time.sleep(0.3)

    stocks_df = pd.DataFrame(all_stocks)
    print(f"  ✅ 共获取 {len(stocks_df)} 只个股数据")

    time.sleep(0.5)

    # 3. 获取指数数据
    print()
    indices_df = fetch_index_data()
    if indices_df is None or indices_df.empty:
        raise Exception("指数数据获取失败")

    print("\n" + "=" * 50)
    print("✅ 数据获取完成！")
    print(f"   板块: {len(boards_df)} 个")
    print(f"   个股: {len(stocks_df)} 只")
    print(f"   指数: {len(indices_df)} 个")

    return boards_df, stocks_df, indices_df


if __name__ == "__main__":
    # 测试
    try:
        boards, stocks, indices = load_eastmoney_data(top_boards=10, stocks_per_board=5)
        print("\n" + "=" * 50)
        print("📊 数据预览:")
        print("\n板块 Top 5:")
        print(boards[['bk_name', 'close', 'turnover', 'up_count']].head())
        print("\n个股 Top 5:")
        print(stocks[['name', 'close', 'turnover_ratio']].head())
        print("\n指数:")
        print(indices)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
