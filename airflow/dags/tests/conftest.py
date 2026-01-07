"""
测试配置
========
Airflow DAGs 单元测试配置
"""

import os
import sys
from pathlib import Path

# 添加 DAGs 目录到 Python 路径
DAGS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(DAGS_DIR))

# 设置测试环境变量
os.environ.setdefault('AIRFLOW__CORE__DAGS_FOLDER', str(DAGS_DIR))
os.environ.setdefault('AIRFLOW__CORE__UNIT_TEST_MODE', 'True')
os.environ.setdefault('AIRFLOW__CORE__LOAD_EXAMPLES', 'False')
os.environ.setdefault('AIRFLOW_HOME', str(DAGS_DIR.parent))

