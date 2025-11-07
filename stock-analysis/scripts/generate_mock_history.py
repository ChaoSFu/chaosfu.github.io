# -*- coding: utf-8 -*-
"""
生成模拟的历史数据用于测试
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

def generate_mock_day(date_str, base_seed=0):
    """生成某一天的模拟数据"""
    random.seed(hash(date_str) + base_seed)

    boards = [
        "化学原料", "化学制品", "光伏设备", "能源金属", "电池",
        "半导体", "计算机设备", "电力设备", "汽车零部件", "通信设备",
        "医疗器械", "中药", "生物制品", "游戏", "传媒"
    ]

    market_advice = random.choice(["OFFENSE", "DEFENSE", "NEUTRAL"])
    broad_strength = random.uniform(-0.3, 0.3)

    # 随机排序板块并生成涨跌幅
    random.shuffle(boards)
    board_data = []

    for i, name in enumerate(boards[:10]):
        # 排名越前涨幅越大
        base_ret = random.uniform(0.005, 0.04) - (i * 0.003)
        board_data.append({
            "code": f"BK{1000+i}",
            "name": name,
            "ret": round(base_ret, 6),
            "pop": round(random.uniform(-1, 2), 6),
            "persistence": random.randint(1, 3),
            "dispersion": round(random.uniform(0.01, 0.05), 6),
            "breadth": round(random.uniform(0.6, 1.0), 6),
            "score": round(random.uniform(-1, 3), 6),
            "stance": random.choice(["STRONG_BUY", "BUY", "WATCH"]),
            "core_stocks": [
                {
                    "code": f"{random.randint(600000, 688999)}",
                    "name": f"股票{j+1}",
                    "ret": round(random.uniform(0, 0.1), 6),
                    "core": round(random.uniform(0, 2), 6)
                }
                for j in range(3)
            ]
        })

    return {
        "date": date_str,
        "market": {
            "risk_on": random.choice([True, False]),
            "broad_strength": round(broad_strength, 2),
            "advice": market_advice
        },
        "boards": board_data,
        "indices": {
            "hs300": {"ret": round(random.uniform(-0.02, 0.02), 6)},
            "csi1000": {"ret": round(random.uniform(-0.02, 0.02), 6)},
            "shcomp": {"ret": round(random.uniform(-0.02, 0.02), 6)}
        },
        "disclaimer": "本页面仅为个人研究与技术演示，不构成投资建议。"
    }

def main():
    import argparse
    ap = argparse.ArgumentParser(description='生成模拟历史数据')
    ap.add_argument('--days', type=int, default=7, help='生成天数')
    ap.add_argument('--archive-dir', default='site/data/archive', help='存档目录')
    args = ap.parse_args()

    archive_dir = Path(args.archive_dir)
    archive_dir.mkdir(parents=True, exist_ok=True)

    print(f"📝 生成最近 {args.days} 天的模拟历史数据...")
    print("=" * 60)

    today = date.today()
    for i in range(args.days):
        d = today - timedelta(days=args.days - 1 - i)
        date_str = d.isoformat()

        data = generate_mock_day(date_str, base_seed=i)
        archive_path = archive_dir / f"{date_str}.json"

        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  ✅ {date_str}: {len(data['boards'])} 个板块")

    print("=" * 60)
    print(f"✅ 模拟数据已生成到: {archive_dir}")

if __name__ == '__main__':
    main()
