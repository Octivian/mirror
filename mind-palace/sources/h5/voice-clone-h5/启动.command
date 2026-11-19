#!/bin/bash
# 双击启动 MiniMax 音色克隆工具
cd "$(dirname "$0")"
echo "🚀 正在启动 MiniMax 音色克隆工具..."
echo "📁 工作目录：$(pwd)"
echo ""

# 检查依赖
if ! python3 -c "import flask, flask_cors, requests" 2>/dev/null; then
    echo "📦 首次运行，正在安装依赖..."
    pip3 install flask flask-cors requests --quiet
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，请手动运行：pip3 install flask flask-cors requests"
        read -p "按回车键退出..."
        exit 1
    fi
    echo "✅ 依赖装好了"
    echo ""
fi

# 启动服务
python3 server.py
echo ""
echo "👋 服务已关闭"
read -p "按回车键退出..."
