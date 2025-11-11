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

    # —— 模拟指数（包含所有主要指数）
    idx = pd.DataFrame([
        [d, "CSI100",   0.006,  80000000,  260000000000],   # 中证100
        [d, "HS300",    0.006,  180000000, 480000000000],   # 沪深300
        [d, "CSI500",   0.004,  190000000, 340000000000],   # 中证500
        [d, "CSI1000",  0.002,  260000000, 410000000000],   # 中证1000
        [d, "CSI2000", -0.001,  150000000, 220000000000],   # 中证2000
        [d, "SHCOMP",   0.004,  580000000, 860000000000],   # 上证指数
    ], columns=["date", "index_code", "ret", "volume", "turnover"])
    return bk, stk, idx

def load_csv(board_csv, stock_csv, index_csv):
    bk = pd.read_csv(board_csv)
    stk = pd.read_csv(stock_csv)
    idx = pd.read_csv(index_csv)
    return bk, stk, idx

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
    """
    from eastmoney import load_eastmoney_data
    return load_eastmoney_data(top_boards, stocks_per_board)
