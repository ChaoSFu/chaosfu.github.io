# -*- coding: utf-8 -*-
import json, argparse
from datetime import date
import pandas as pd
from sources import load_mock, load_csv, load_api
from factors import board_metrics, core_stocks, market_regime

def to_json(out_path, boards, indices):
    result = {
        "date": date.today().isoformat(),
        "market": {
            "risk_on": indices["risk_on"],
            "broad_strength": indices["broad_strength"],
            "advice": "OFFENSE" if indices["advice"]=="OFFENSE" else ("DEFENSE" if indices["advice"]=="DEFENSE" else "NEUTRAL")
        },
        "boards": boards,
        "indices": {
            "hs300": {"ret": indices["hs300"]["ret"]},
            "csi1000": {"ret": indices["csi1000"]["ret"]},
            "shcomp": {"ret": indices["shcomp"]["ret"]}
        },
        "disclaimer": "本页面仅为个人研究与技术演示，不构成投资建议。"
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result

def archive_daily_data(data, archive_dir):
    """存档当日数据到 archive 目录"""
    import os
    os.makedirs(archive_dir, exist_ok=True)

    date_str = data['date']
    archive_path = os.path.join(archive_dir, f"{date_str}.json")

    with open(archive_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"   📁 存档: {archive_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["EASTMONEY","MOCK","CSV","API"], default="EASTMONEY",
                    help="数据源模式: EASTMONEY=东方财富实时数据(默认), MOCK=模拟数据, CSV=CSV文件, API=自定义API")
    ap.add_argument("--board_csv", default="scripts/sample/boards.csv")
    ap.add_argument("--stock_csv", default="scripts/sample/stocks.csv")
    ap.add_argument("--index_csv", default="scripts/sample/index.csv")
    ap.add_argument("--out", default="site/data/daily.json")
    ap.add_argument("--top-boards", type=int, default=20, help="抓取前N个板块(EASTMONEY模式)")
    ap.add_argument("--stocks-per-board", type=int, default=10, help="每板块抓取前N只个股(EASTMONEY模式)")
    ap.add_argument("--archive-dir", default="site/data/archive", help="历史数据存档目录")
    ap.add_argument("--enable-history", action="store_true", help="启用历史趋势数据生成")
    ap.add_argument("--history-days", type=int, default=7, help="历史数据天数")
    args = ap.parse_args()

    print(f"🚀 ETL 模式: {args.mode}")
    print("=" * 60)

    if args.mode == "EASTMONEY":
        from sources import load_eastmoney
        bk, stk, idx = load_eastmoney(top_boards=args.top_boards, stocks_per_board=args.stocks_per_board)
    elif args.mode == "CSV":
        bk, stk, idx = load_csv(args.board_csv, args.stock_csv, args.index_csv)
    elif args.mode == "API":
        from os import getenv
        api_key = getenv("DATA_API_KEY","")
        bk, stk, idx = load_api(api_key)
    else:  # MOCK
        print("⚠️  使用 Mock 数据（仅用于测试）")
        bk, stk, idx = load_mock()

    # 计算
    boards_df = board_metrics(bk, stk)
    stocks_df = core_stocks(stk)
    indices = market_regime(idx)

    # 聚合输出（Top 10 板块）
    boards_df = boards_df.sort_values("score", ascending=False)
    out_boards = []
    for _, row in boards_df.head(10).iterrows():
        bcode = row["bk_code"]
        top_core = (stocks_df[stocks_df["bk_code"]==bcode]
                    .sort_values("core", ascending=False)
                    .head(3)[["ts_code","name","ret_1d","core"]])
        out_boards.append({
            "code": bcode,
            "name": row["bk_name"],
            "ret": round(float(row["ret"]), 6),
            "pop": round(float(row["pop"]), 6),
            "persistence": int(row["persistence"]),
            "dispersion": round(float(row["dispersion"]), 6) if pd.notna(row["dispersion"]) else None,
            "breadth": round(float(row["breadth"]), 6) if pd.notna(row["breadth"]) else None,
            "score": round(float(row["score"]), 6),
            "stance": "STRONG_BUY" if row["score"]>1.5 else ("BUY" if row["score"]>0.5 else ("WATCH" if row["score"]>-0.5 else "AVOID")),
            "core_stocks": [
                {"code": r["ts_code"], "name": r["name"], "ret": round(float(r["ret_1d"]),6), "core": round(float(r["core"]),6)}
                for _, r in top_core.iterrows()
            ]
        })

    daily_data = to_json(args.out, out_boards, indices)

    print("\n" + "=" * 60)
    print(f"✅ 数据已保存: {args.out}")
    print(f"   日期: {date.today().isoformat()}")
    print(f"   板块数: {len(out_boards)}")
    print(f"   个股数: {len(stocks_df)}")
    print(f"   市场节奏: {indices['advice']}")

    # 存档当日数据
    archive_daily_data(daily_data, args.archive_dir)

    # 生成历史趋势数据
    if args.enable_history:
        print("\n" + "=" * 60)
        print("📊 生成历史趋势数据...")
        from generate_history import generate_history, save_history
        history = generate_history(args.archive_dir, args.history_days)
        if history:
            history_path = args.out.replace('daily.json', 'history.json')
            save_history(history, history_path)

    print("=" * 60)

if __name__ == "__main__":
    main()
