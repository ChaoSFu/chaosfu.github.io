# A股板块热度与核心个股分析系统

[![Deploy](https://github.com/chaosfu/chaosfu.github.io/actions/workflows/stock-analysis-daily.yml/badge.svg)](https://github.com/chaosfu/chaosfu.github.io/actions/workflows/stock-analysis-daily.yml)

一个基于 GitHub Pages + GitHub Actions 的静态网站，每日自动更新 A 股板块热度、核心个股及市场进攻/防守节奏分析。

## ⚠️ 免责声明

**本项目仅为个人研究与技术演示，不构成任何投资建议。市场有风险，投资需谨慎。**

项目使用的所有数据、指标和分析结果仅供学习参考，不应作为实际投资决策的依据。使用者需自行承担使用本项目信息所产生的任何风险和责任。

## 特性

- 📊 **板块热度排行**：基于涨幅、人气、持续性等多维度指标综合打分
- 🎯 **核心个股挖掘**：识别板块内的强势龙头个股
- 🌊 **市场节奏判断**：基于沪深300与中证1000相对强弱判断进攻/防守时机
- 🔄 **自动日更**：GitHub Actions 定时运行（工作日15:10），无需手动维护
- 🚀 **零成本部署**：完全基于 GitHub Pages，无需服务器

## 在线访问

访问地址：[https://chaosfu.github.io/stock-analysis/](https://chaosfu.github.io/stock-analysis/)

## 快速开始

### 1. 数据源说明

项目**默认使用东方财富网真实行情数据**，无需额外配置，开箱即用。

**数据来源**：
- 板块数据：东方财富板块排行 API
- 个股数据：板块成分股 API
- 指数数据：沪深300、中证1000、上证指数
- 更新时间：每工作日 15:10（收盘后）自动更新

如需切换其他数据源：

#### 方式 A：使用 CSV 文件
1. 准备三个 CSV 文件：`boards.csv`、`stocks.csv`、`index.csv`
2. 放置在 `stock-analysis/scripts/sample/` 目录下
3. 修改 `.github/workflows/stock-analysis-daily.yml` 中的 `MODE` 为 `CSV`

#### 方式 B：对接数据 API
1. 在 `Settings` → `Secrets` → `Actions` 中添加 `DATA_API_KEY`
2. 修改 `stock-analysis/scripts/sources.py` 中的 `load_api()` 函数实现
3. 修改 `.github/workflows/stock-analysis-daily.yml` 中的 `MODE` 为 `API`

### 2. 手动触发首次运行

1. 进入 `Actions` 标签页
2. 选择 `Build & Deploy Daily Data` 工作流
3. 点击 `Run workflow` 按钮

等待几分钟后，网站将更新数据。

## 项目结构

```
stock-analysis/
├── site/                      # 静态网站（部署到 gh-pages）
│   ├── index.html            # 主页面
│   ├── styles.css            # 样式
│   ├── app.js                # 前端逻辑
│   ├── data/
│   │   └── daily.json        # 每日生成的数据
│   └── assets/
│       └── icon.png          # 网站图标（可选）
├── scripts/                   # Python ETL 脚本
│   ├── etl_daily.py          # 主脚本
│   ├── sources.py            # 数据源适配
│   ├── factors.py            # 指标计算
│   ├── requirements.txt      # Python 依赖
│   └── sample/               # CSV 样例数据
│       ├── boards.csv
│       ├── stocks.csv
│       └── index.csv
└── README.md
```

## 指标说明

### 板块指标
- **涨幅（ret）**：当日板块收盘价涨跌幅
- **人气（pop）**：基于成交额放量与上涨家数的综合人气指标
- **持续性（persistence）**：0-3分，基于1日/3日/5日动量的持续强势评分
- **分歧度（dispersion）**：板块内个股涨幅标准差，越大表示分化越明显
- **广度（breadth）**：板块内上涨个股占比
- **综合分（score）**：基于上述指标的 Z-score 加权得分

### 市场节奏
- **OFFENSE（进攻）**：中证1000 明显强于沪深300，适合小盘/成长风格
- **DEFENSE（防守）**：沪深300 明显强于中证1000，适合大盘/价值风格
- **NEUTRAL（中性）**：两者差异不明显，保持观察

## 技术栈

- **前端**：原生 HTML + CSS + JavaScript + ECharts 5
- **后端**：无（纯静态）
- **ETL**：Python 3.11 + Pandas + NumPy
- **自动化**：GitHub Actions
- **托管**：GitHub Pages

## 本地开发

### 运行 ETL 脚本

```bash
# 安装依赖
pip install -r stock-analysis/scripts/requirements.txt

# 使用东方财富真实数据（推荐）
python stock-analysis/scripts/etl_daily.py --mode EASTMONEY --out stock-analysis/site/data/daily.json

# 自定义抓取参数
python stock-analysis/scripts/etl_daily.py \
    --mode EASTMONEY \
    --top-boards 20 \
    --stocks-per-board 10 \
    --out stock-analysis/site/data/daily.json

# 或使用 Mock 测试数据
python stock-analysis/scripts/etl_daily.py --mode MOCK --out stock-analysis/site/data/daily.json

# 或使用 CSV 模式
python stock-analysis/scripts/etl_daily.py --mode CSV --out stock-analysis/site/data/daily.json
```

### 本地预览网站

```bash
cd stock-analysis/site
python -m http.server 8000
# 访问 http://localhost:8000
```

## 定时任务说明

GitHub Actions 配置为：
- **触发时间**：UTC 07:10（北京时间 15:10），周一至周五
- **执行内容**：运行 ETL 脚本 → 生成 `daily.json` → 部署到 `gh-pages` 分支的 `stock-analysis/` 目录
- **手动触发**：可在 Actions 页面随时手动运行

## 数据合规建议

1. **避免高频抓取**：定时任务设置为每日一次，避免对数据源造成压力
2. **使用合规 API**：建议使用正规金融数据服务商提供的接口
3. **遵守使用协议**：确保数据来源符合相关服务条款
4. **延迟数据**：可考虑使用延迟 15 分钟的行情数据

## 后续扩展

- [ ] 增加历史数据存档（`site/data/archive/`）
- [ ] 添加策略回测页面
- [ ] 个股"人气×涨幅"散点图可视化
- [ ] 板块与指数相关性热力图
- [ ] 中英文国际化支持
- [ ] 移动端响应式优化

## 常见问题

**Q: Actions 运行失败怎么办？**
A: 检查 Actions 日志，常见问题包括 Python 依赖安装失败或数据源配置错误。

**Q: 如何更改定时任务时间？**
A: 修改 `.github/workflows/stock-analysis-daily.yml` 中的 `cron` 表达式（注意使用 UTC 时间）。

**Q: 可以部署到自定义域名吗？**
A: 可以，在 `Settings` → `Pages` → `Custom domain` 中配置，并添加 CNAME 记录。

## 许可证

MIT License - 详见仓库根目录的 [LICENSE](../LICENSE) 文件

## 致谢

- [ECharts](https://echarts.apache.org/) - 数据可视化库
- [GitHub Actions](https://github.com/features/actions) - 自动化工具
- [GitHub Pages](https://pages.github.com/) - 静态网站托管

---

**再次提醒：本项目仅供学习交流使用，不构成投资建议。投资有风险，入市需谨慎！**