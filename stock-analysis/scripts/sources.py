# -*- coding: utf-8 -*-
import pandas as pd
from datetime import date, timedelta

def load_mock():
    d = date.today().isoformat()
    # —— 模拟板块
    bk = pd.DataFrame([
        ["BK001","半导体", 103,100, 12e9, 120, 8],
        ["BK002","电力",   100.8,100, 9e9,  80,  1],
        ["BK003","游戏",   104,100, 7e9,  95,  3],
    ], columns=["bk_code","bk_name","close","prev_close","turnover","up_count","limit_up"])
    bk["date"] = d

    # —— 模拟个股
    stk = pd.DataFrame([
        [d,"BK001","688001","芯片A", 110,100, 1.5e9, 6.1, 7.5],
        [d,"BK001","688002","芯片B", 108,100, 1.2e9, 5.4, 6.0],
        [d,"BK001","603001","设备C", 107,100, 0.9e9, 4.9, 5.2],
        [d,"BK002","600001","电力A", 101,100, 0.8e9, 2.1, 3.0],
        [d,"BK003","300001","游戏A", 106,100, 1.0e9, 5.0, 7.0],
    ], columns=["date","bk_code","ts_code","name","close","prev_close","turnover","turnover_ratio","amplitude"])

    # —— 模拟指数（包含所有主要指数，添加OHLC数据）
    idx = pd.DataFrame([
        [d, "CSI100",   5800.0,  5850.0,  5780.0,  5834.8,  0.006,  80000000,  260000000000],   # 中证100
        [d, "HS300",    3200.0,  3230.0,  3180.0,  3219.2,  0.006,  180000000, 480000000000],   # 沪深300
        [d, "CSI500",   4500.0,  4530.0,  4480.0,  4518.0,  0.004,  190000000, 340000000000],   # 中证500
        [d, "CSI1000",  5600.0,  5640.0,  5580.0,  5611.2,  0.002,  260000000, 410000000000],   # 中证1000
        [d, "CSI2000",  4800.0,  4820.0,  4760.0,  4795.2, -0.001,  150000000, 220000000000],   # 中证2000
        [d, "SHCOMP",   3100.0,  3140.0,  3080.0,  3112.4,  0.004,  580000000, 860000000000],   # 上证指数
    ], columns=["date", "index_code", "open", "high", "low", "close", "ret", "volume", "turnover"])

    # —— 模拟大盘核心指数
    market_idx = pd.DataFrame([
        [d, "SHCOMP",  "上证指数", 3200.5, 3200.0, 0.005, 580000000, 860000000000],   # 上证指数
        [d, "SZCOMP",  "深证成指", 11000.2, 11000.0, 0.008, 520000000, 780000000000], # 深证成指
        [d, "CYBZ",    "创业板指", 2300.8, 2300.0, 0.012, 340000000, 520000000000],   # 创业板指
        [d, "KCB50",   "科创50", 980.5, 980.0, 0.015, 120000000, 180000000000],       # 科创50
        [d, "BJ50",    "北证50", 850.3, 850.0, 0.010, 45000000, 68000000000],         # 北证50
    ], columns=["date", "index_code", "index_name", "close", "prev_close", "ret", "volume", "turnover"])

    return bk, stk, idx, market_idx

def load_csv(board_csv, stock_csv, index_csv):
    bk = pd.read_csv(board_csv)
    stk = pd.read_csv(stock_csv)
    idx = pd.read_csv(index_csv)
    # CSV模式暂不支持大盘指数，返回空DataFrame
    market_idx = pd.DataFrame()
    return bk, stk, idx, market_idx

def load_api(api_key:str=""):
    """
    从东方财富获取真实行情数据
    """
    try:
        from eastmoney import load_eastmoney_data
        return load_eastmoney_data(top_boards=20, stocks_per_board=10)
    except Exception as e:
        print(f"⚠️  东方财富数据获取失败: {e}")
        print("⚠️  回退到 Mock 数据")
        return load_mock()

def load_eastmoney(top_boards=20, stocks_per_board=10):
    """
    直接从东方财富获取数据（推荐）
    返回: (boards_df, stocks_df, indices_df, market_indices_df)
    """
    from eastmoney import load_eastmoney_data
    return load_eastmoney_data(top_boards, stocks_per_board)
