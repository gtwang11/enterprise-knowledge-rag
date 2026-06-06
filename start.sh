#!/bin/bash
set -e

echo "============================================"
echo " 运维数字员工门户 - 启动脚本 (Linux/macOS)"
echo "============================================"
echo

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.10+"
    exit 1
fi

# 检查 Ollama
if ! command -v ollama &> /dev/null; then
    echo "[提示] 未检测到 Ollama，请确认已安装并启动"
    echo "      安装: curl -fsSL https://ollama.com/install.sh | sh"
fi

echo "[1/4] 检查 Ollama 服务..."
if ! ollama list &> /dev/null; then
    echo "[启动] 正在启动 Ollama 服务..."
    ollama serve &
    sleep 5
fi

echo "[2/4] 检查模型..."
if ! ollama list | grep -q "deepseek-llm-7b-chat"; then
    echo "[下载] 正在下载 deepseek-llm-7b-chat:q4 模型（约4.5GB）..."
    ollama pull deepseek-llm-7b-chat:q4
fi

if ! ollama list | grep -q "nomic-embed-text"; then
    echo "[下载] 正在下载 nomic-embed-text 模型（约274MB）..."
    ollama pull nomic-embed-text
fi

echo "[3/4] 安装后端依赖..."
cd "$(dirname "$0")/backend"
pip install -r requirements.txt -q

echo "[4/4] 启动后端服务..."
echo
echo "后端启动后访问:"
echo "  - API 文档: http://localhost:8000/docs"
echo "  - 前端页面: http://localhost:8000"
echo "  - 默认账号: admin / Admin@123456"
echo
python3 main.py &

sleep 5

echo "[可选] 启动前端开发服务器:"
echo "  cd frontend && npm install && npm run dev"
echo "  开发页面: http://localhost:5173"
echo
echo "============================================"
echo " 启动完成！"
echo "============================================"
