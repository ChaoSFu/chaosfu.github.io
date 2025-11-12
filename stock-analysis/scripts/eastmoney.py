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

def is_valid_concept_board(board_name):
    """
    判断是否是有效的概念板块（过滤掉选股条件类的伪概念）

    排除规则：
    - 包含"昨日"、"连板"、"涨停"、"一字"等短线选股条件
    - 包含"次新股"、"破净"、"ST"等特殊状态
    - 包含"创业板"、"科创板"、"北交所"等市场分类
    """
    # 黑名单关键词
    blacklist_keywords = [
        '昨日', '今日', '连板', '涨停', '跌停', '一字',
        '次新股', '破净', 'ST', '*ST', '退市',
        '创业板', '科创板', '科创50', '科创100', '北交所', '沪市', '深市',
        '融资融券', '转融券', '股权转让',
        '大盘', '中盘', '小盘', '微盘',
        '_含一字', '_含ST', '_含创业',
        '高送转', '高股息', '低市盈',
        '业绩预增', '业绩爆雷', '业绩暴增',
        '沪深300', '中证', '上证', '深证',
        '指数', '成份股'
    ]

    # 检查是否包含黑名单关键词
    for keyword in blacklist_keywords:
        if keyword in board_name:
            return False

    return True


def fetch_board_data(board_type='industry'):
    """
    获取板块涨跌幅排行数据
    API: 东方财富板块排行接口

    参数:
        board_type: 'industry' 行业板块, 'concept' 概念板块
    """
    url = "https://push2.eastmoney.com/api/qt/clist/get"

    # t:2=行业板块, t:3=概念板块
    fs_type = 'm:90+t:2' if board_type == 'industry' else 'm:90+t:3'

    params = {
        'fid': 'f3',        # 排序字段：f3=涨跌幅
        'po': '1',          # 排序：1=降序
        'pz': '100',        # 每页数量
        'pn': '1',          # 页码
        'np': '1',          # 不分页
        'fltt': '2',        # 过滤条件
        'invt': '2',        #
        'fs': fs_type,      # 市场分类：90=板块，t:2=行业，t:3=概念
        'fields': 'f12,f14,f2,f3,f5,f6,f8,f104,f105,f106,f128,f136,f137,f138'
        # f12=code, f14=name, f2=price, f3=pct_change, f5=volume, f6=turnover
        # f104=上涨家数, f105=下跌家数, f128=领涨股, f136=涨速, f137=换手率
    }

    try:
        board_name = "行业板块" if board_type == 'industry' else "概念板块"
        print(f"  [{board_name}] 请求东方财富数据...")
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('rc') != 0 or 'data' not in data:
            print(f"  [{board_name}] ⚠️  API返回异常: {data}")
            return None

        boards = data['data']['diff']
        print(f"  [{board_name}] ✅ 成功获取 {len(boards)} 个板块数据")

        # 转换为 DataFrame
        records = []
        today = date.today().isoformat()
        filtered_count = 0

        for item in boards:
            bk_name = item.get('f14', '')

            # 如果是概念板块，需要过滤掉选股条件类的伪概念
            if board_type == 'concept' and not is_valid_concept_board(bk_name):
                filtered_count += 1
                continue

            # f3: 涨跌幅(%), f2: 最新价, f5: 成交量, f6: 成交额
            # f104: 上涨家数, f138: 涨停家数
            pct = item.get('f3', 0) / 100.0  # 百分比转小数
            price = item.get('f2', 0)

            records.append({
                'date': today,
                'bk_code': item.get('f12', ''),
                'bk_name': bk_name,
                'bk_type': board_type,  # 添加板块类型标识
                'close': price,
                'prev_close': price / (1 + pct) if pct != -1 else price,
                'turnover': item.get('f6', 0),  # 成交额(元)
                'up_count': item.get('f104', 0),  # 上涨家数
                'limit_up': item.get('f138', 0),  # 涨停家数
            })

        if filtered_count > 0:
            print(f"  [{board_name}] ⚠️  已过滤 {filtered_count} 个选股条件类板块")

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
    url = "https://push2.eastmoney.com/api/qt/clist/get"

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
    获取主要指数数据（中证100/沪深300/中证500/中证1000/中证2000）
    移除上证50，保留上证指数用于对比
    """
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"

    # secids 格式: 市场代码.指数代码
    # 1.000903=中证100, 1.000300=沪深300
    # 1.000905=中证500, 1.000852=中证1000
    # 2.932000=中证2000 (注意：中证2000使用市场代码2)
    # 1.000001=上证指数（用于对比）
    params = {
        'secids': '1.000903,1.000300,1.000905,1.000852,2.932000,1.000001',
        'fields': 'f12,f14,f2,f3,f4,f5,f6,f15,f16,f17'
        # f2=最新价, f3=涨跌幅, f4=涨跌额, f5=成交量, f6=成交额
        # f15=最高, f16=最低, f17=开盘
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

        # 映射：东方财富代码 -> 我们的代码（移除上证50）
        code_map = {
            '000903': 'CSI100',      # 中证100
            '000300': 'HS300',       # 沪深300
            '000905': 'CSI500',      # 中证500
            '000852': 'CSI1000',     # 中证1000
            '932000': 'CSI2000',     # 中证2000
            '000001': 'SHCOMP'       # 上证指数
        }

        # 指数中文名称
        name_map = {
            'CSI100': '中证100',
            'HS300': '沪深300',
            'CSI500': '中证500',
            'CSI1000': '中证1000',
            'CSI2000': '中证2000',
            'SHCOMP': '上证指数'
        }

        records = []
        today = date.today().isoformat()

        for item in indices:
            code = item.get('f12', '')
            if code in code_map:
                index_code = code_map[code]
                pct = item.get('f3', 0) / 100.0  # 涨跌幅转小数
                price = item.get('f2', 0)

                # 获取OHLC数据
                open_price = item.get('f17', 0) if item.get('f17') else price
                high = item.get('f15', 0) if item.get('f15') else price
                low = item.get('f16', 0) if item.get('f16') else price

                records.append({
                    'date': today,
                    'index_code': index_code,
                    'index_name': name_map.get(index_code, ''),
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': price,
                    'prev_close': price / (1 + pct) if pct != 0 else price,
                    'ret': pct,
                    'volume': item.get('f5', 0),      # 成交量
                    'turnover': item.get('f6', 0),    # 成交额
                })

        df = pd.DataFrame(records)
        return df

    except Exception as e:
        print(f"  [指数] ❌ 请求失败: {e}")
        return None


def fetch_index_kline(index_code, days=30):
    """
    获取指数的历史K线数据（日线）

    参数:
        index_code: 指数代码，如 'HS300', 'CSI500', 'CSI1000', 'CSI2000'
                    或大盘指数 'SHCOMP', 'SZCOMP', 'CYBZ', 'KCB50', 'BJ50'
        days: 获取最近N天的数据，默认30天

    返回:
        DataFrame with columns: date, open, high, low, close, volume, ret
    """
    # 映射：我们的代码 -> 东方财富secid
    secid_map = {
        # 主要指数
        'HS300': '1.000300',      # 沪深300
        'CSI500': '1.000905',     # 中证500
        'CSI1000': '1.000852',    # 中证1000
        'CSI2000': '2.932000',    # 中证2000 (市场代码2)
        'SHCOMP': '1.000001',     # 上证指数
        # 大盘核心指数
        'SZCOMP': '0.399001',     # 深证成指
        'CYBZ': '0.399006',       # 创业板指
        'KCB50': '1.000688',      # 科创50
        'BJ50': '0.899050'        # 北证50
    }

    if index_code not in secid_map:
        print(f"  [K线] ⚠️  不支持的指数代码: {index_code}")
        return None

    secid = secid_map[index_code]
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

    params = {
        'secid': secid,
        'klt': '101',  # 101=日K线, 102=周K线, 103=月K线
        'fqt': '1',    # 复权类型：0=不复权, 1=前复权, 2=后复权
        'lmt': str(days),  # 获取最近N条数据
        'end': '20500000',  # 结束日期（足够大的未来日期）
        'iscca': '1',
        'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64',
        'ut': 'f057cbcbce2a86e2866ab8877db1d059',
        'forcect': '1'
    }

    try:
        print(f"  [K线] 请求 {index_code} 最近{days}天数据...")
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('rc') != 0 or 'data' not in data:
            print(f"  [K线] ⚠️  API返回异常: {data}")
            return None

        klines_str = data['data'].get('klines', [])
        if not klines_str:
            print(f"  [K线] ⚠️  没有K线数据")
            return None

        # 解析K线数据
        # 格式: "日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率"
        records = []
        for kline in klines_str:
            parts = kline.split(',')
            if len(parts) < 11:
                continue

            date_str = parts[0]  # YYYY-MM-DD
            open_price = float(parts[1])
            close_price = float(parts[2])
            high_price = float(parts[3])
            low_price = float(parts[4])
            volume = float(parts[5])
            # turnover = float(parts[6])  # 成交额
            # amplitude = float(parts[7])  # 振幅
            ret = float(parts[8]) / 100.0  # 涨跌幅(%)转小数

            records.append({
                'date': date_str,
                'index_code': index_code,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
                'ret': ret
            })

        df = pd.DataFrame(records)
        print(f"  [K线] ✅ 成功获取 {len(df)} 条K线数据")
        return df

    except Exception as e:
        print(f"  [K线] ❌ 请求失败: {e}")
        return None


def fetch_board_kline(board_code, board_type='industry', days=30):
    """
    获取板块的历史K线数据（日线）

    参数:
        board_code: 板块代码，如 'BK1031'（光伏设备）
        board_type: 板块类型，'industry'=行业板块, 'concept'=概念板块
        days: 获取最近N天的数据，默认30天

    返回:
        DataFrame with columns: date, open, high, low, close, volume, turnover, ret
    """
    # 板块K线API
    # 板块代码格式：90.BK1031（行业板块）或 90.BK0XXX（概念板块）
    secid = f"90.{board_code}"
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

    params = {
        'secid': secid,
        'klt': '101',  # 101=日K线
        'fqt': '0',    # 板块不需要复权
        'lmt': str(days),
        'end': '20500000',
        'iscca': '1',
        'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'ut': 'f057cbcbce2a86e2866ab8877db1d059',
        'forcect': '1'
    }

    try:
        print(f"  [板块K线] 请求 {board_code} 最近{days}天数据...")
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('rc') != 0 or 'data' not in data:
            print(f"  [板块K线] ⚠️  API返回异常")
            return None

        klines_str = data['data'].get('klines', [])
        if not klines_str:
            print(f"  [板块K线] ⚠️  没有K线数据")
            return None

        # 解析K线数据
        # 格式：日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
        records = []
        for kline_str in klines_str:
            parts = kline_str.split(',')
            if len(parts) < 10:
                continue

            date_str = parts[0]
            open_price = float(parts[1])
            close_price = float(parts[2])
            high_price = float(parts[3])
            low_price = float(parts[4])
            volume = float(parts[5])
            turnover = float(parts[6])
            pct_chg = float(parts[8])  # 涨跌幅(%)

            records.append({
                'date': date_str,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume,
                'turnover': turnover,
                'ret': pct_chg / 100  # 转换为小数
            })

        if not records:
            print(f"  [板块K线] ⚠️  解析K线数据失败")
            return None

        df = pd.DataFrame(records)
        print(f"  [板块K线] ✅ 成功获取 {len(df)} 条K线数据")
        return df

    except Exception as e:
        print(f"  [板块K线] ⚠️  请求失败: {e}")
        return None


def fetch_market_indices():
    """
    获取大盘核心指数数据（用于大盘看板）
    包括：上证指数/深证成指/创业板指/科创50/北证50
    """
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"

    # secids 格式: 市场代码.指数代码
    # 1.000001=上证指数, 0.399001=深证成指, 0.399006=创业板指
    # 1.000688=科创50, 0.899050=北证50
    params = {
        'secids': '1.000001,0.399001,0.399006,1.000688,0.899050',
        'fields': 'f12,f14,f2,f3,f4,f5,f6,f15,f16,f17'
        # f2=最新价, f3=涨跌幅, f4=涨跌额, f5=成交量, f6=成交额
        # f15=最高, f16=最低, f17=开盘
    }

    try:
        print(f"  [大盘指数] 请求东方财富大盘核心指数数据...")
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('rc') != 0 or 'data' not in data:
            print(f"  [大盘指数] ⚠️  API返回异常")
            return None

        indices = data['data']['diff']
        print(f"  [大盘指数] ✅ 成功获取 {len(indices)} 个大盘指数数据")

        # 映射：东方财富代码 -> 我们的代码
        code_map = {
            '000001': 'SHCOMP',      # 上证指数
            '399001': 'SZCOMP',      # 深证成指
            '399006': 'CYBZ',        # 创业板指
            '000688': 'KCB50',       # 科创50
            '899050': 'BJ50'         # 北证50
        }

        # 指数中文名称
        name_map = {
            'SHCOMP': '上证指数',
            'SZCOMP': '深证成指',
            'CYBZ': '创业板指',
            'KCB50': '科创50',
            'BJ50': '北证50'
        }

        records = []
        today = date.today().isoformat()

        for item in indices:
            code = item.get('f12', '')
            if code in code_map:
                index_code = code_map[code]
                # f3返回的是百分比的100倍，如-39表示-0.39%
                # 除以10000转换为小数形式：-39/10000 = -0.0039
                pct = item.get('f3', 0) / 10000.0
                # f2返回的值需要除以100得到实际点数
                price = item.get('f2', 0) / 100.0

                # 获取OHLC数据
                open_price = item.get('f17', 0) / 100.0 if item.get('f17') else price
                high = item.get('f15', 0) / 100.0 if item.get('f15') else price
                low = item.get('f16', 0) / 100.0 if item.get('f16') else price

                records.append({
                    'date': today,
                    'index_code': index_code,
                    'index_name': name_map.get(index_code, ''),
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': price,
                    'prev_close': price / (1 + pct) if pct != 0 else price,
                    'ret': pct,
                    'volume': item.get('f5', 0),      # 成交量
                    'turnover': item.get('f6', 0),    # 成交额
                })

        df = pd.DataFrame(records)
        return df

    except Exception as e:
        print(f"  [大盘指数] ❌ 请求失败: {e}")
        return None


def load_eastmoney_data(top_boards=20, stocks_per_board=10):
    """
    加载东方财富完整数据

    参数:
        top_boards: 每种类型抓取前N个板块
        stocks_per_board: 每个板块抓取前N只个股

    返回:
        (boards_df, stocks_df, indices_df)
    """
    print("📡 开始从东方财富获取实时数据...")
    print("=" * 50)

    # 1. 获取行业板块数据
    industry_df = fetch_board_data(board_type='industry')
    if industry_df is None or industry_df.empty:
        raise Exception("行业板块数据获取失败")
    industry_df = industry_df.head(top_boards)
    print(f"\n  ✅ 已筛选 Top {len(industry_df)} 行业板块")

    time.sleep(0.5)

    # 2. 获取概念板块数据
    concept_df = fetch_board_data(board_type='concept')
    if concept_df is None or concept_df.empty:
        raise Exception("概念板块数据获取失败")
    concept_df = concept_df.head(top_boards)
    print(f"\n  ✅ 已筛选 Top {len(concept_df)} 概念板块")

    # 合并两类板块
    boards_df = pd.concat([industry_df, concept_df], ignore_index=True)

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

    time.sleep(0.5)

    # 4. 获取大盘核心指数数据
    print()
    market_indices_df = fetch_market_indices()
    if market_indices_df is None or market_indices_df.empty:
        print("  ⚠️  大盘核心指数数据获取失败，继续使用现有数据")
        market_indices_df = pd.DataFrame()

    print("\n" + "=" * 50)
    print("✅ 数据获取完成！")
    print(f"   板块: {len(boards_df)} 个")
    print(f"   个股: {len(stocks_df)} 只")
    print(f"   指数: {len(indices_df)} 个")
    print(f"   大盘指数: {len(market_indices_df)} 个")

    return boards_df, stocks_df, indices_df, market_indices_df


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
