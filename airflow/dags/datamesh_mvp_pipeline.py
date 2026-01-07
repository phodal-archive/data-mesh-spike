"""
Data Mesh MVP Pipeline
======================
这个 DAG 演示了 Data Mesh 架构中的数据管道：
1. 从各个域提取数据
2. 创建跨域数据产品
3. 生成业务报告
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

# DAG 默认参数
default_args = {
    'owner': 'datamesh-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 创建 DAG
dag = DAG(
    'datamesh_mvp_pipeline',
    default_args=default_args,
    description='Data Mesh MVP - 跨域数据产品管道',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['datamesh', 'mvp', 'data-product'],
)


def log_pipeline_start(**context):
    """记录管道开始"""
    print("=" * 50)
    print("Data Mesh MVP Pipeline Started")
    print(f"Execution Date: {context['ds']}")
    print("=" * 50)
    return "Pipeline started successfully"


def validate_data_quality(**context):
    """验证数据质量"""
    print("Validating data quality across domains...")
    # 这里可以添加实际的数据质量检查逻辑
    checks = {
        'customers_not_empty': True,
        'orders_have_valid_customers': True,
        'products_have_prices': True,
    }
    
    for check, passed in checks.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {check}: {status}")
    
    return checks


def generate_kpi_report(**context):
    """生成 KPI 报告"""
    print("Generating Business KPI Report...")
    print("-" * 40)
    
    # 模拟 KPI 数据（实际中会从数据库查询）
    kpis = {
        'total_customers': 10,
        'total_orders': 13,
        'total_revenue': 3500.00,
        'avg_order_value': 269.23,
        'pending_orders': 3,
    }
    
    for kpi, value in kpis.items():
        print(f"  {kpi}: {value}")
    
    print("-" * 40)
    print("KPI Report generated successfully!")
    return kpis


def notify_data_products_ready(**context):
    """通知数据产品已就绪"""
    print("=" * 50)
    print("Data Products Ready for Consumption:")
    print("  - dp_customer_360: Customer 360 View")
    print("  - dp_product_sales: Product Sales Analytics")
    print("  - dp_order_fulfillment: Order Fulfillment Status")
    print("  - dp_business_kpis: Business KPI Dashboard")
    print("=" * 50)
    return "Notification sent"


# 定义任务
start_task = PythonOperator(
    task_id='start_pipeline',
    python_callable=log_pipeline_start,
    dag=dag,
)

validate_quality = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=dag,
)

# 使用 Bash 执行 Trino 查询刷新数据产品
refresh_data_products = BashOperator(
    task_id='refresh_data_products',
    bash_command='''
    echo "Refreshing data products via Trino..."
    echo "Querying: mariadb.domain_analytics.dp_customer_360"
    echo "Querying: mariadb.domain_analytics.dp_product_sales"
    echo "Data products refreshed successfully!"
    ''',
    dag=dag,
)

generate_report = PythonOperator(
    task_id='generate_kpi_report',
    python_callable=generate_kpi_report,
    dag=dag,
)

notify_ready = PythonOperator(
    task_id='notify_data_products_ready',
    python_callable=notify_data_products_ready,
    dag=dag,
)

# 定义任务依赖关系
start_task >> validate_quality >> refresh_data_products >> generate_report >> notify_ready

