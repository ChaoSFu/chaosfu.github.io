#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证history.json数据完整性
"""
import json
import sys
from pathlib import Path

def verify_history_data(history_file):
    """验证历史数据文件"""
    print("=" * 70)
    print("📊 验证历史数据文件")
    print("=" * 70)

    # 1. 检查文件是否存在
    if not Path(history_file).exists():
        print(f"❌ 文件不存在: {history_file}")
        return False

    print(f"✅ 文件存在: {history_file}")

    # 2. 加载JSON
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ JSON格式正确")
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
        return False

    # 3. 验证market_indices_history（大盘指数）
    print("\n" + "=" * 70)
    print("🔍 验证 market_indices_history（大盘看板数据）")
    print("=" * 70)

    if 'market_indices_history' not in data:
        print("❌ 缺少 market_indices_history 字段")
        return False

    mih = data['market_indices_history']

    # 检查dates
    if 'dates' not in mih or not mih['dates']:
        print("❌ market_indices_history.dates 为空")
        return False

    print(f"✅ 日期数量: {len(mih['dates'])} 天")
    print(f"   日期范围: {mih['dates'][0]} ~ {mih['dates'][-1]}")

    # 检查market_indices
    if 'market_indices' not in mih:
        print("❌ 缺少 market_indices 字段")
        return False

    market_indices = mih['market_indices']
    expected_indices = ['SHCOMP', 'SZCOMP', 'CYBZ', 'KCB50', 'BJ50']

    for index_code in expected_indices:
        if index_code not in market_indices:
            print(f"❌ 缺少指数: {index_code}")
            return False

        index_data = market_indices[index_code]
        valid_count = sum(1 for item in index_data if item is not None)

        # 检查第一条数据的结构
        if valid_count > 0:
            first_valid = next(item for item in index_data if item is not None)
            required_fields = ['open', 'close', 'low', 'high', 'ret', 'volume']
            missing_fields = [f for f in required_fields if f not in first_valid]

            if missing_fields:
                print(f"❌ {index_code} 缺少字段: {missing_fields}")
                return False

            print(f"✅ {index_code}: {valid_count}/{len(index_data)} 条有效数据")
        else:
            print(f"⚠️  {index_code}: 无有效数据")

    # 4. 验证main_indices_history（主要指数）
    print("\n" + "=" * 70)
    print("🔍 验证 main_indices_history（主要指数看板数据）")
    print("=" * 70)

    if 'main_indices_history' not in data:
        print("❌ 缺少 main_indices_history 字段")
        return False

    main_ih = data['main_indices_history']

    # 检查dates
    if 'dates' not in main_ih or not main_ih['dates']:
        print("❌ main_indices_history.dates 为空")
        return False

    print(f"✅ 日期数量: {len(main_ih['dates'])} 天")
    print(f"   日期范围: {main_ih['dates'][0]} ~ {main_ih['dates'][-1]}")

    # 检查main_indices
    if 'main_indices' not in main_ih:
        print("❌ 缺少 main_indices 字段")
        return False

    main_indices = main_ih['main_indices']
    expected_main_indices = ['HS300', 'CSI500', 'CSI1000', 'CSI2000']

    for index_code in expected_main_indices:
        if index_code not in main_indices:
            print(f"❌ 缺少指数: {index_code}")
            return False

        index_data = main_indices[index_code]
        valid_count = sum(1 for item in index_data if item is not None)

        # 检查第一条数据的结构
        if valid_count > 0:
            first_valid = next(item for item in index_data if item is not None)
            required_fields = ['open', 'close', 'low', 'high', 'ret', 'volume']
            missing_fields = [f for f in required_fields if f not in first_valid]

            if missing_fields:
                print(f"❌ {index_code} 缺少字段: {missing_fields}")
                return False

            print(f"✅ {index_code}: {valid_count}/{len(index_data)} 条有效数据")

            # 显示第一条数据示例
            if index_code == 'HS300':
                print(f"\n   数据示例 ({main_ih['dates'][0]}):")
                print(f"   开盘: {first_valid['open']:.2f}")
                print(f"   收盘: {first_valid['close']:.2f}")
                print(f"   最高: {first_valid['high']:.2f}")
                print(f"   最低: {first_valid['low']:.2f}")
                print(f"   涨跌幅: {first_valid['ret']*100:.2f}%")
                print(f"   成交量: {first_valid['volume']:.0f}")
        else:
            print(f"⚠️  {index_code}: 无有效数据")

    # 5. 总结
    print("\n" + "=" * 70)
    print("✅ 数据验证通过！")
    print("=" * 70)
    print(f"📊 大盘指数: {len(expected_indices)} 个")
    print(f"📊 主要指数: {len(expected_main_indices)} 个")
    print(f"📅 数据天数: {len(mih['dates'])} 天")

    return True

if __name__ == '__main__':
    history_file = 'data/history.json'

    if len(sys.argv) > 1:
        history_file = sys.argv[1]

    success = verify_history_data(history_file)
    sys.exit(0 if success else 1)
