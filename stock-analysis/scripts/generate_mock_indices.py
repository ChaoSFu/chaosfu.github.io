#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成模拟指数数据用于测试
"""
import json
from datetime import date

# 模拟指数数据（移除上证50）
mock_indices = {
    "CSI100": {
        "name": "中证100",
        "code": "000903",
        "price": 3256.78,
        "ret": 0.0123,
        "change": 39.62,
        "volume": 145623000,
        "turnover": 8562300000
    },
    "HS300": {
        "name": "沪深300",
        "code": "000300",
        "price": 3789.45,
        "ret": 0.0156,
        "change": 58.12,
        "volume": 234567000,
        "turnover": 15678900000
    },
    "CSI500": {
        "name": "中证500",
        "code": "000905",
        "price": 5678.90,
        "ret": 0.0234,
        "change": 130.45,
        "volume": 345678000,
        "turnover": 23456700000
    },
    "CSI1000": {
        "name": "中证1000",
        "code": "000852",
        "price": 4567.89,
        "ret": 0.0287,
        "change": 127.89,
        "volume": 456789000,
        "turnover": 34567800000
    },
    "CSI2000": {
        "name": "中证2000",
        "code": "932000",
        "price": 3456.78,
        "ret": 0.0321,
        "change": 107.56,
        "volume": 567890000,
        "turnover": 45678900000
    },
    "SHCOMP": {
        "name": "上证指数",
        "code": "000001",
        "price": 3234.56,
        "ret": 0.0145,
        "change": 46.23,
        "volume": 198765000,
        "turnover": 12345600000
    }
}

# 添加兼容旧代码的字段
mock_indices["hs300"] = mock_indices["HS300"]
mock_indices["csi1000"] = mock_indices["CSI1000"]
mock_indices["shcomp"] = mock_indices["SHCOMP"]

if __name__ == "__main__":
    # 读取现有的daily.json
    with open('../data/daily.json', 'r', encoding='utf-8') as f:
        daily_data = json.load(f)

    # 更新indices数据
    daily_data['indices'] = mock_indices

    # 保存回文件
    with open('../data/daily.json', 'w', encoding='utf-8') as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)

    print("✅ 模拟指数数据已更新到 daily.json")
    print(f"📊 包含 {len([k for k in mock_indices.keys() if k.isupper()])} 个指数")
