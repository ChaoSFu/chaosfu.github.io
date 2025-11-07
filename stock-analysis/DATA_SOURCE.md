# 数据源说明

## 📡 东方财富真实数据（默认）

本项目使用**东方财富网公开 API** 获取真实的 A 股行情数据。

### 数据接口

#### 1. 板块排行数据
- **接口**: `http://push2.eastmoney.com/api/qt/clist/get`
- **数据内容**:
  - 板块代码、名称
  - 最新价、涨跌幅
  - 成交额、成交量
  - 上涨家数、涨停家数
- **更新频率**: 实时（每次运行时获取最新数据）

#### 2. 板块成分股数据
- **接口**: `http://push2.eastmoney.com/api/qt/clist/get`（带板块代码参数）
- **数据内容**:
  - 个股代码、名称
  - 最新价、涨跌幅
  - 成交额、换手率、振幅
- **抓取策略**: 每个板块抓取涨幅前 N 只个股（默认10只）

#### 3. 指数数据
- **接口**: `http://push2.eastmoney.com/api/qt/ulist.np/get`
- **数据内容**:
  - 沪深300（000300）
  - 中证1000（000852）
  - 上证综指（000001）
- **指标**: 涨跌幅

### 数据处理流程

```
1. 获取板块排行（按涨幅降序）
   ↓
2. 筛选 Top N 板块（默认20个）
   ↓
3. 对每个板块获取成分股数据
   ↓
4. 获取主要指数数据
   ↓
5. 计算指标（人气、持续性、分歧度等）
   ↓
6. 生成 daily.json
```

### 合规性说明

✅ **符合规范**:
- 使用公开 API 接口
- 控制请求频率（板块间延迟 0.3 秒）
- 设置合理的 User-Agent
- 不进行高频抓取（每日仅运行一次）
- 遵守 HTTP 规范

⚠️ **注意事项**:
- 数据仅供个人学习研究使用
- 请勿用于商业用途
- 请勿进行高频请求
- 尊重数据源网站服务条款

### 数据质量

**优点**:
- ✅ 数据真实可靠
- ✅ 更新及时（实时行情）
- ✅ 覆盖全面（86个行业板块）
- ✅ 无需注册和认证

**限制**:
- ⏰ 交易时间外可能无法获取最新数据
- 🌐 需要网络连接
- ⚡ 首次运行需要约 10-15 秒

---

## 🧪 Mock 测试数据

用于开发调试的模拟数据。

### 数据内容

- **板块**: 3个（半导体、电力、游戏）
- **个股**: 5只
- **指数**: 3个（沪深300、中证1000、上证综指）

### 使用场景

- ✅ 本地开发测试
- ✅ CI/CD 环境测试
- ✅ 功能演示
- ❌ 不适用于生产环境

### 切换方式

```bash
python scripts/etl_daily.py --mode MOCK --out site/data/daily.json
```

---

## 📂 CSV 文件数据

支持从本地 CSV 文件读取数据。

### 文件格式

#### boards.csv (板块数据)
```csv
date,bk_code,bk_name,close,prev_close,turnover,up_count,limit_up
2025-11-07,BK001,半导体,103,100,12000000000,120,8
```

#### stocks.csv (个股数据)
```csv
date,bk_code,ts_code,name,close,prev_close,turnover,turnover_ratio,amplitude
2025-11-07,BK001,688001,芯片A,110,100,1500000000,6.1,7.5
```

#### index.csv (指数数据)
```csv
date,index_code,ret
2025-11-07,HS300,0.006
2025-11-07,CSI1000,0.002
2025-11-07,SHCOMP,0.004
```

### 使用场景

- ✅ 对接自有数据源
- ✅ 历史数据回测
- ✅ 离线环境使用

### 切换方式

```bash
python scripts/etl_daily.py --mode CSV \
    --board_csv scripts/sample/boards.csv \
    --stock_csv scripts/sample/stocks.csv \
    --index_csv scripts/sample/index.csv \
    --out site/data/daily.json
```

---

## 🔌 自定义 API 数据源

支持对接第三方数据服务商。

### 实现步骤

1. 修改 `scripts/sources.py` 中的 `load_api()` 函数
2. 实现数据获取和转换逻辑
3. 返回统一格式的 DataFrame

### 数据格式要求

必须返回三个 DataFrame：

```python
# 板块数据
boards_df: pd.DataFrame
  - date: 日期
  - bk_code: 板块代码
  - bk_name: 板块名称
  - close: 最新价
  - prev_close: 昨收价
  - turnover: 成交额
  - up_count: 上涨家数
  - limit_up: 涨停家数

# 个股数据
stocks_df: pd.DataFrame
  - date: 日期
  - bk_code: 板块代码
  - ts_code: 股票代码
  - name: 股票名称
  - close: 最新价
  - prev_close: 昨收价
  - turnover: 成交额
  - turnover_ratio: 换手率
  - amplitude: 振幅

# 指数数据
indices_df: pd.DataFrame
  - date: 日期
  - index_code: 指数代码（HS300/CSI1000/SHCOMP）
  - ret: 涨跌幅（小数形式，如 0.006 表示 0.6%）
```

### 切换方式

```bash
export DATA_API_KEY="your-api-key"
python scripts/etl_daily.py --mode API --out site/data/daily.json
```

---

## 🎯 推荐配置

### 生产环境（GitHub Actions）
```yaml
MODE: "EASTMONEY"
top-boards: 20
stocks-per-board: 10
```

### 本地开发
```bash
# 快速测试
python scripts/etl_daily.py --mode MOCK

# 真实数据预览
python scripts/etl_daily.py --mode EASTMONEY --top-boards 10
```

### 历史数据回测
```bash
# 准备历史 CSV 数据
python scripts/etl_daily.py --mode CSV \
    --board_csv data/2024-01-01/boards.csv \
    --stock_csv data/2024-01-01/stocks.csv \
    --index_csv data/2024-01-01/index.csv
```

---

## 📊 数据字段说明

### 板块指标
- **ret** (return): 涨跌幅，小数形式（0.03 = 3%）
- **pop** (popularity): 人气分，基于成交额放量和上涨家数的 Z-score
- **persistence**: 持续性，0-3 分（0=弱，3=强）
- **dispersion**: 分歧度，成分股涨跌幅标准差
- **breadth**: 广度，上涨股票占比（0.72 = 72%）
- **score**: 综合分，基于多指标加权的 Z-score
- **stance**: 操作建议（STRONG_BUY/BUY/WATCH/AVOID）

### 个股指标
- **ret_1d**: 当日涨跌幅
- **turnover_ratio**: 换手率（%）
- **amplitude**: 振幅（%）
- **core**: 核心度，基于人气和涨幅的综合评分

### 市场指标
- **risk_on**: 风险偏好（true=风险偏好上升）
- **broad_strength**: 宽基强弱（HS300 - CSI1000 涨跌幅）
- **advice**: 市场节奏（OFFENSE=进攻/DEFENSE=防守/NEUTRAL=中性）

---

## 🔧 故障排查

### 问题：东方财富数据获取失败

**原因**:
- 网络连接问题
- API 接口变更
- 请求被限流

**解决**:
1. 检查网络连接
2. 查看控制台错误信息
3. 临时切换到 Mock 模式：`--mode MOCK`

### 问题：数据为空或异常

**原因**:
- 非交易时间
- 数据源返回异常

**解决**:
1. 检查是否为交易时间段
2. 查看 ETL 日志输出
3. 使用 `python scripts/eastmoney.py` 单独测试数据获取

---

## 📞 技术支持

如有数据源相关问题，请提交 Issue 并附上：
1. 运行模式（EASTMONEY/MOCK/CSV/API）
2. 错误日志
3. 运行时间和环境信息

---

**最后更新**: 2025-11-07
**当前版本**: v1.0.0 (真实数据版本)
