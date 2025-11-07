# 本地测试指南

## 🚀 快速开始（推荐）

使用一键测试脚本：

```bash
cd stock-analysis
./test-local.sh
```

脚本会自动完成：
- ✅ 创建/激活 Python 虚拟环境
- ✅ 安装所需依赖
- ✅ 生成测试数据
- ✅ 启动本地服务器

完成后在浏览器访问：**http://localhost:8000**

---

## 📋 手动测试步骤

如果你想手动执行每一步：

### 步骤 1: 准备 Python 环境

```bash
cd stock-analysis

# 创建虚拟环境（首次运行）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r scripts/requirements.txt
```

### 步骤 2: 生成数据

```bash
# 使用东方财富真实数据（推荐，默认）
python scripts/etl_daily.py --mode EASTMONEY --out site/data/daily.json

# 或使用 Mock 测试数据
python scripts/etl_daily.py --mode MOCK --out site/data/daily.json

# 或使用 CSV 数据
python scripts/etl_daily.py --mode CSV --out site/data/daily.json
```

### 步骤 3: 验证数据生成

```bash
# 查看生成的数据
cat site/data/daily.json

# 或者格式化输出
python -m json.tool site/data/daily.json
```

### 步骤 4: 启动 Web 服务器

```bash
cd site
python3 -m http.server 8000
```

### 步骤 5: 在浏览器中访问

打开浏览器访问：**http://localhost:8000**

---

## 🔍 测试不同的数据源

### 测试东方财富真实数据（推荐）

```bash
source venv/bin/activate
python scripts/etl_daily.py --mode EASTMONEY \
    --top-boards 15 \
    --stocks-per-board 8 \
    --out site/data/daily.json
```

真实数据包括：
- 前15个涨幅最高的板块（可自定义）
- 每个板块前8只个股（可自定义）
- 3个指数：沪深300、中证1000、上证综指

**数据来源**：东方财富网公开 API
**更新频率**：实时（建议每日收盘后运行）

### 测试 Mock 数据（模拟数据）

```bash
source venv/bin/activate
python scripts/etl_daily.py --mode MOCK --out site/data/daily.json
```

模拟数据包括：
- 3个板块：半导体、电力、游戏
- 5只个股
- 3个指数：沪深300、中证1000、上证综指

**注意**：Mock 数据仅用于开发测试，不应用于生产环境。

### 测试 CSV 数据

1. 准备你的 CSV 文件，放在 `scripts/sample/` 目录：
   - `boards.csv`：板块数据
   - `stocks.csv`：个股数据
   - `index.csv`：指数数据

2. 运行脚本：
```bash
source venv/bin/activate
python scripts/etl_daily.py --mode CSV \
    --board_csv scripts/sample/boards.csv \
    --stock_csv scripts/sample/stocks.csv \
    --index_csv scripts/sample/index.csv \
    --out site/data/daily.json
```

### 测试 API 数据

1. 修改 `scripts/sources.py` 中的 `load_api()` 函数
2. 设置环境变量（如需要）：
```bash
export DATA_API_KEY="your-api-key-here"
```
3. 运行脚本：
```bash
source venv/bin/activate
python scripts/etl_daily.py --mode API --out site/data/daily.json
```

---

## 🐛 常见问题

### Q1: `ModuleNotFoundError: No module named 'pandas'`

**解决方法**：确保已激活虚拟环境并安装依赖
```bash
source venv/bin/activate
pip install -r scripts/requirements.txt
```

### Q2: 端口 8000 已被占用

**解决方法**：使用其他端口
```bash
python3 -m http.server 8001
```
然后访问 http://localhost:8001

### Q3: 页面显示但没有数据

**解决方法**：检查浏览器控制台错误，确保 `site/data/daily.json` 存在：
```bash
ls -la site/data/daily.json
cat site/data/daily.json
```

### Q4: 图表不显示

**原因**：可能是 CDN 被墙，ECharts 未加载成功

**解决方法**：
1. 检查浏览器控制台是否有 ECharts 加载错误
2. 修改 `site/index.html` 使用国内 CDN：
```html
<!-- 替换为 -->
<script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/echarts.min.js"></script>
```

---

## 📊 验证清单

测试时请验证以下功能：

- [ ] 页面正常加载，无 404 错误
- [ ] 显示当前日期和市场节奏（进攻/防守）
- [ ] 显示板块排行榜（至少 3 个板块）
- [ ] 每个板块显示核心个股
- [ ] 底部显示宽基强弱柱状图（ECharts）
- [ ] 图表可以交互（鼠标悬停显示数值）
- [ ] 显示免责声明

---

## 🔧 开发调试

### 修改前端代码

1. 编辑 `site/index.html`、`site/styles.css` 或 `site/app.js`
2. 保存后直接刷新浏览器（Ctrl/Cmd + R）
3. 如果浏览器有缓存，使用强制刷新（Ctrl/Cmd + Shift + R）

### 修改 Python 代码

1. 编辑 `scripts/` 下的 Python 文件
2. 重新运行 ETL 脚本生成数据：
```bash
source venv/bin/activate
python scripts/etl_daily.py --mode MOCK --out site/data/daily.json
```
3. 刷新浏览器查看效果

### 查看详细日志

```bash
# Python 脚本添加详细输出
python scripts/etl_daily.py --mode MOCK --out site/data/daily.json -v

# 查看 HTTP 服务器日志（已在终端显示）
# 每次请求都会显示访问记录
```

---

## 🎯 性能测试

### 测试数据生成速度

```bash
time python scripts/etl_daily.py --mode MOCK --out site/data/daily.json
```

正常情况下应该在 1-2 秒内完成。

### 测试页面加载速度

使用浏览器开发者工具（F12）的 Network 标签：
- `daily.json` 应该小于 100KB
- 页面总加载时间应该小于 2 秒

---

## 📝 测试数据说明

Mock 数据的特点：
- **日期**：当天日期（自动获取）
- **板块涨幅**：0.8% ~ 4%
- **人气分数**：基于模拟的成交额和上涨家数
- **持续性**：固定为 3（满分）
- **市场节奏**：固定为 DEFENSE（防守）

如需更真实的测试，建议使用 CSV 模式并准备历史数据。

---

## 🚀 下一步

测试通过后：
1. 提交代码到 GitHub
2. 触发 GitHub Actions 部署
3. 访问线上地址验证

祝测试顺利！🎉
