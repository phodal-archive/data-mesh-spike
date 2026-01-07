#!/bin/bash
# Airflow DAGs 开发快速命令参考

echo "📚 Airflow DAGs 本地开发 - 快速参考"
echo ""
echo "📍 当前目录: $(pwd)"
echo ""

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "✅ 虚拟环境已存在"
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"
    else
        echo "⚠️  虚拟环境未激活"
        echo "   运行: source venv/bin/activate"
    fi
else
    echo "❌ 虚拟环境不存在"
    echo "   运行: ./setup-dev.sh"
fi

echo ""
echo "🔧 常用命令:"
echo ""
echo "  环境设置:"
echo "    ./setup-dev.sh          # 初始化环境"
echo "    source venv/bin/activate # 激活虚拟环境"
echo ""
echo "  测试:"
echo "    pytest tests/test_dags_simple.py -v              # 运行简化测试"
echo "    pytest tests/test_dags_simple.py --cov=.         # 测试+覆盖率"
echo "    pytest tests/test_dags_simple.py -k test_dag_structure  # 运行特定测试"
echo ""
echo "  代码质量:"
echo "    black *.py              # 格式化代码"
echo "    flake8 *.py             # 检查风格"
echo "    pylint datamesh_mvp_pipeline.py  # 详细检查"
echo ""
echo "  DAG 验证:"
echo "    python datamesh_mvp_pipeline.py  # 检查语法"
echo ""
echo "  容器内验证:"
echo "    docker exec datamesh-airflow-scheduler airflow dags list | grep datamesh"
echo "    docker logs datamesh-airflow-scheduler | grep validate_data_quality"
echo ""
echo "📖 详细文档: cat README.md"

