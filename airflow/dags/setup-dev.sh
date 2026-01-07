#!/bin/bash

# Airflow DAGs 本地开发环境快速设置脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Setting up Airflow DAGs local development environment..."
echo ""

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# 激活虚拟环境
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# 升级 pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

# 安装依赖
echo "📥 Installing dependencies..."
if [ "$1" == "--dev" ]; then
    pip install -r requirements-dev.txt -q
    echo "✓ Development dependencies installed"
else
    pip install -r requirements.txt -q
    echo "✓ Production dependencies installed"
    echo "💡 Run './setup-dev.sh --dev' to install development tools"
fi

# 创建 tests 目录的 __init__.py
mkdir -p tests
touch tests/__init__.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Activate the virtual environment:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Run tests:"
echo "      pytest -v"
echo ""
echo "   3. Check code quality:"
echo "      flake8 *.py"
echo "      black *.py"
echo ""
echo "   4. Start coding! 🎉"
echo ""
echo "📚 Read README.md for more information"

