# Airflow DAGs 本地开发指南

本目录包含 Data Mesh MVP 的 Airflow DAG 定义和本地开发工具。

## 目录结构

```
airflow/dags/
├── datamesh_mvp_pipeline.py    # 主 DAG: 跨域数据产品管道
├── sample_data_mesh_dag.py     # 示例 DAG
├── tests/                       # 单元测试
│   ├── conftest.py             # pytest 配置
│   └── test_datamesh_mvp_pipeline.py
├── requirements.txt             # Python 依赖
├── requirements-dev.txt         # 开发依赖
├── setup.cfg                    # 测试和 lint 配置
└── README.md                    # 本文档
```

## 快速开始

### 1. 创建虚拟环境

```bash
cd /Users/phodal/repractise/learn-data-mesh/airflow/dags

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate   # Windows
```

### 2. 安装依赖

```bash
# 安装生产依赖
pip install -r requirements.txt

# 或安装开发依赖（包含测试工具）
pip install -r requirements-dev.txt
```

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_datamesh_mvp_pipeline.py

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # macOS
```

### 4. 代码质量检查

```bash
# Flake8 检查
flake8 datamesh_mvp_pipeline.py

# Black 格式化
black datamesh_mvp_pipeline.py

# Pylint 检查
pylint datamesh_mvp_pipeline.py

# MyPy 类型检查
mypy datamesh_mvp_pipeline.py
```

## 本地测试 DAG

### 方法 1: 使用 pytest（推荐）

```bash
# 测试 DAG 加载和结构
pytest tests/test_datamesh_mvp_pipeline.py::TestDataMeshMVPPipeline -v

# 测试数据质量验证逻辑
pytest tests/test_datamesh_mvp_pipeline.py::TestDataQualityValidation -v
```

### 方法 2: 使用 Airflow CLI

```bash
# 需要先设置 AIRFLOW_HOME
export AIRFLOW_HOME=/Users/phodal/repractise/learn-data-mesh/airflow

# 测试 DAG 是否有语法错误
python datamesh_mvp_pipeline.py

# 列出 DAG 中的所有任务
airflow tasks list datamesh_mvp_pipeline

# 测试单个任务
airflow tasks test datamesh_mvp_pipeline validate_data_quality 2026-01-07
```

### 方法 3: Python 交互式测试

```python
# 启动 Python/IPython
ipython

# 导入 DAG
from datamesh_mvp_pipeline import dag, validate_data_quality

# 查看 DAG 信息
print(f"DAG ID: {dag.dag_id}")
print(f"Tasks: {[task.task_id for task in dag.tasks]}")

# 测试质量验证函数（需要数据库连接）
# result = validate_data_quality()
# print(result)
```

## 开发工作流

### 1. 修改 DAG

编辑 `datamesh_mvp_pipeline.py`，例如添加新的质量规则：

```python
def validate_data_quality(**context):
    # ... 现有代码 ...
    
    # 添加新的检查
    cursor.execute("""
        SELECT COUNT(*) 
        FROM domain_customers.customers 
        WHERE email NOT LIKE '%@%'
    """)
    invalid_emails = cursor.fetchone()[0]
    
    check_name = "customers.email: 必须是有效邮箱格式"
    if invalid_emails == 0:
        passed_checks.append(check_name)
    else:
        failed_checks.append(check_name)
```

### 2. 运行 Linter

```bash
# 自动格式化代码
black datamesh_mvp_pipeline.py

# 检查代码风格
flake8 datamesh_mvp_pipeline.py
```

### 3. 编写测试

在 `tests/test_datamesh_mvp_pipeline.py` 中添加测试：

```python
def test_email_validation(self, mocker):
    """测试邮箱格式验证"""
    # 添加测试逻辑
    pass
```

### 4. 运行测试

```bash
pytest tests/ -v
```

### 5. 部署到容器

```bash
# DAG 文件会自动同步到容器（通过 volume 挂载）
# 检查 Airflow 是否识别到更改
docker exec datamesh-airflow-scheduler airflow dags list | grep datamesh_mvp_pipeline
```

## 环境变量配置

创建 `.env` 文件（不要提交到 git）：

```bash
# .env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=datamesh
MYSQL_PASSWORD=datamesh123

# 对于本地测试，如果使用 Colima
MYSQL_HOST=192.168.5.1
```

在代码中使用：

```python
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST', 'datamesh-mariadb'),
    user=os.getenv('MYSQL_USER', 'datamesh'),
    password=os.getenv('MYSQL_PASSWORD', 'datamesh123'),
)
```

## 调试技巧

### 1. 使用日志

```python
import logging

logger = logging.getLogger(__name__)

def validate_data_quality(**context):
    logger.info("Starting quality validation...")
    logger.debug(f"Context: {context}")
```

### 2. 使用 pdb 调试

```python
def validate_data_quality(**context):
    import pdb; pdb.set_trace()  # 添加断点
    # ... 代码 ...
```

### 3. 查看 Airflow 日志

```bash
# 容器内日志
docker logs datamesh-airflow-scheduler | grep validate_data_quality

# 本地日志文件
cat ../logs/dag_id=datamesh_mvp_pipeline/*/task_id=validate_data_quality/attempt=1.log
```

## 常见问题

### Q: 如何连接本地数据库？

A: 如果使用 Colima，需要使用 Colima VM 的 IP：

```python
# 获取 Colima IP
# colima ssh -- hostname -I

conn = mysql.connector.connect(
    host='192.168.5.1',  # Colima IP
    port=3306,
    user='datamesh',
    password='datamesh123'
)
```

### Q: pytest 找不到模块？

A: 确保已激活虚拟环境并安装了依赖：

```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Q: DAG 修改后 Airflow 未更新？

A: Airflow 有缓存，等待几秒或手动刷新：

```bash
docker exec datamesh-airflow-scheduler airflow dags reserialize
```

## 最佳实践

1. **使用虚拟环境**: 避免依赖冲突
2. **编写测试**: 确保质量规则正确
3. **遵循代码风格**: 使用 black + flake8
4. **添加文档**: 为复杂逻辑添加注释
5. **版本控制**: 提交前运行 `pytest` 和 `flake8`

## 相关文档

- [Airflow 官方文档](https://airflow.apache.org/docs/)
- [pytest 文档](https://docs.pytest.org/)
- [Data Mesh 质量验证演示](../../docs/task-c-data-quality-validation.md)

## 快速命令参考

```bash
# 环境设置
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt

# 测试
pytest                              # 运行所有测试
pytest -v                           # 详细模式
pytest --cov=. --cov-report=html   # 生成覆盖率报告

# 代码质量
black .                             # 格式化所有文件
flake8 *.py                         # 检查代码风格
pylint datamesh_mvp_pipeline.py    # 详细检查

# Airflow
python datamesh_mvp_pipeline.py    # 检查语法
airflow dags list                   # 列出所有 DAG
airflow tasks test <dag_id> <task_id> <date>  # 测试任务
```

