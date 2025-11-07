#!/bin/bash
# A股板块分析系统 - 本地测试脚本

set -e

echo "=========================================="
echo "  A股板块热度分析系统 - 本地测试"
echo "=========================================="
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 步骤 1: 检查 Python 环境
echo "📦 [1/4] 检查 Python 环境..."
if [ ! -d "venv" ]; then
    echo "   创建虚拟环境..."
    python3 -m venv venv
fi

echo "   激活虚拟环境..."
source venv/bin/activate

# 步骤 2: 安装依赖
echo ""
echo "📦 [2/4] 安装 Python 依赖..."
pip install -q -r scripts/requirements.txt

# 步骤 3: 生成真实数据
echo ""
echo "🔄 [3/4] 从东方财富获取真实数据..."
echo "   （如需使用测试数据，添加参数: --mode MOCK）"
python scripts/etl_daily.py --mode EASTMONEY --top-boards 15 --stocks-per-board 8 --out site/data/daily.json
echo "   ✅ 数据已生成: site/data/daily.json"

# 显示数据摘要
echo ""
echo "📊 数据摘要:"
echo "   日期: $(cat site/data/daily.json | grep '"date"' | head -1)"
echo "   板块数: $(cat site/data/daily.json | grep '"code"' | wc -l | xargs)"
echo "   市场节奏: $(cat site/data/daily.json | grep '"advice"' | head -1)"

# 步骤 4: 启动 Web 服务器
echo ""
echo "🌐 [4/4] 启动本地服务器..."
echo ""
echo "=========================================="
echo "  ✅ 测试环境已就绪！"
echo "=========================================="
echo ""
echo "📱 访问地址: http://localhost:8000"
echo ""
echo "💡 提示:"
echo "   - 按 Ctrl+C 停止服务器"
echo "   - 修改代码后刷新浏览器即可看到变化"
echo "   - 重新生成数据: source venv/bin/activate && python scripts/etl_daily.py --mode MOCK --out site/data/daily.json"
echo ""
echo "🚀 正在启动服务器..."
echo ""

cd site
python3 -m http.server 8000
