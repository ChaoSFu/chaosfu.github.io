# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

def zscore(s: pd.Series):
    return (s - s.mean()) / (s.std(ddof=0) + 1e-9)

def board_metrics(board_df: pd.DataFrame, stocks_df: pd.DataFrame):
    """
    board_df: date,bk_code,bk_name,close,prev_close,turnover,up_count,limit_up
    stocks_df: date,bk_code,ts_code,name,close,prev_close,turnover,turnover_ratio,amplitude
    """
    df = board_df.copy()
    df["ret"] = df["close"] / df["prev_close"] - 1
    df["pop_turnover"] = df.groupby("bk_code")["turnover"].transform(
        lambda s: s / (s.rolling(5, min_periods=1).mean() + 1e-9)
    )
    df["pop"] = zscore(df["pop_turnover"]) + 0.5 * zscore(df["up_count"])
    # 持续性：mom3,mom5（此处简单用近几日滚动累计，要求上游保证有历史）
    for n in (3, 5):
        df[f"mom{n}"] = df.groupby("bk_code")["ret"].transform(
            lambda s: s.rolling(n, min_periods=1).sum()
        )
    df["persistence"] = (df["ret"] > 0).astype(int) \
                      + (df["mom3"] > 0).astype(int) \
                      + (df["mom5"] > 0).astype(int)

    # 分歧与广度
    tmp = stocks_df.copy()
    tmp["ret_1d"] = tmp["close"] / tmp["prev_close"] - 1
    disp = tmp.groupby(["date","bk_code"])["ret_1d"].std(ddof=0).rename("dispersion")
    breadth = (tmp["ret_1d"] > 0).groupby([tmp["date"], tmp["bk_code"]]).mean().rename("breadth")
    df = df.merge(disp, on=["date","bk_code"], how="left").merge(breadth, on=["date","bk_code"], how="left")

    # 综合分
    df["score"] = zscore(df["ret"]) + zscore(df["pop"]) + 0.5 * zscore(1.0 / (df["dispersion"] + 1e-9))
    return df

def core_stocks(stocks_df: pd.DataFrame):
    s = stocks_df.copy()
    s["ret_1d"] = s["close"] / s["prev_close"] - 1
    s["score_ret"] = zscore(s["ret_1d"])
    s["score_pop"] = zscore(s["turnover_ratio"]) + 0.5 * zscore(s.get("amplitude", pd.Series(0, index=s.index)))
    s["core"] = 0.6 * s["score_pop"] + 0.4 * s["score_ret"]
    return s

def market_regime(idx_df: pd.DataFrame):
    """
    idx_df: date,index_code,ret  (index_code ∈ {HS300,CSI1000,SHCOMP})
    """
    piv = idx_df.pivot(index="date", columns="index_code", values="ret").reset_index().iloc[-1]
    hs300, csi1000, shcomp = piv["HS300"], piv["CSI1000"], piv["SHCOMP"]
    broad_strength = float(hs300 - csi1000)
    risk_on = int([hs300, csi1000, shcomp].count(np.nan) == 0 and (np.array([hs300, csi1000, shcomp]) > 0).sum() >= 2)
    if broad_strength > 0.002:
        advice = "DEFENSE"
    elif broad_strength < -0.002:
        advice = "OFFENSE"
    else:
        advice = "NEUTRAL"
    return {
        "hs300": {"ret": float(hs300)},
        "csi1000": {"ret": float(csi1000)},
        "shcomp": {"ret": float(shcomp)},
        "risk_on": bool(risk_on),
        "broad_strength": broad_strength,
        "advice": advice
    }
