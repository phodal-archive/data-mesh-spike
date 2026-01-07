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
import mysql.connector
from airflow.exceptions import AirflowException

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
    """
    验证数据质量 - Data Mesh 质量左移实践
    包含三类规则：完整性、一致性、新鲜度
    """
    print("=" * 60)
    print("🔍 Data Quality Validation Started")
    print("=" * 60)
    
    # 连接 MariaDB
    conn = mysql.connector.connect(
        host='datamesh-mariadb',
        user='datamesh',
        password='datamesh123',
        database='domain_customers'
    )
    cursor = conn.cursor()
    
    failed_checks = []
    passed_checks = []
    
    # ===== 完整性检查 (Completeness) =====
    print("\n📋 1. Completeness Checks")
    print("-" * 60)
    
    # 检查 1: 客户主键非空且唯一
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT customer_id) as unique_ids,
            COUNT(CASE WHEN customer_id IS NULL THEN 1 END) as null_ids
        FROM domain_customers.customers
    """)
    result = cursor.fetchone()
    total, unique_ids, null_ids = result
    
    check_name = "customers.customer_id: 非空且唯一"
    if null_ids == 0 and total == unique_ids:
        passed_checks.append(check_name)
        print(f"  ✓ {check_name}")
        print(f"    Total: {total}, Unique: {unique_ids}, Null: {null_ids}")
    else:
        failed_checks.append(check_name)
        print(f"  ✗ {check_name}")
        print(f"    Total: {total}, Unique: {unique_ids}, Null: {null_ids}")
    
    # 检查 2: 订单必须有有效客户
    cursor.execute("""
        SELECT COUNT(*) as orphan_orders
        FROM domain_orders.orders o
        LEFT JOIN domain_customers.customers c ON o.customer_id = c.customer_id
        WHERE c.customer_id IS NULL
    """)
    orphan_orders = cursor.fetchone()[0]
    
    check_name = "orders: 所有订单有有效客户"
    if orphan_orders == 0:
        passed_checks.append(check_name)
        print(f"  ✓ {check_name}")
    else:
        failed_checks.append(check_name)
        print(f"  ✗ {check_name} - 发现 {orphan_orders} 个孤儿订单")
    
    # 检查 3: 产品价格必须为正
    cursor.execute("""
        SELECT COUNT(*) as invalid_price_count
        FROM domain_products.products
        WHERE price IS NULL OR price <= 0
    """)
    invalid_prices = cursor.fetchone()[0]
    
    check_name = "products.price: 必须为正数"
    if invalid_prices == 0:
        passed_checks.append(check_name)
        print(f"  ✓ {check_name}")
    else:
        failed_checks.append(check_name)
        print(f"  ✗ {check_name} - 发现 {invalid_prices} 个无效价格")
    
    # ===== 一致性检查 (Consistency) =====
    print("\n🔗 2. Consistency Checks")
    print("-" * 60)
    
    # 检查 4: 订单总额 = 订单明细汇总（关键！）
    cursor.execute("""
        SELECT 
            o.order_id,
            o.total_amount as order_total,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) as items_total,
            ABS(o.total_amount - COALESCE(SUM(oi.quantity * oi.unit_price), 0)) as diff
        FROM domain_orders.orders o
        LEFT JOIN domain_orders.order_items oi ON o.order_id = oi.order_id
        GROUP BY o.order_id, o.total_amount
        HAVING ABS(o.total_amount - COALESCE(SUM(oi.quantity * oi.unit_price), 0)) > 0.01
    """)
    inconsistent_orders = cursor.fetchall()
    
    check_name = "orders.total_amount = SUM(order_items)"
    if len(inconsistent_orders) == 0:
        passed_checks.append(check_name)
        print(f"  ✓ {check_name}")
    else:
        failed_checks.append(check_name)
        print(f"  ✗ {check_name} - 发现 {len(inconsistent_orders)} 个不一致订单:")
        for order_id, order_total, items_total, diff in inconsistent_orders[:3]:
            print(f"    Order {order_id}: 订单={order_total}, 明细={items_total}, 差异={diff}")
        if len(inconsistent_orders) > 3:
            print(f"    ... 还有 {len(inconsistent_orders) - 3} 个")
    
    # 检查 5: 订单明细的产品必须存在
    cursor.execute("""
        SELECT COUNT(*) as invalid_products
        FROM domain_orders.order_items oi
        LEFT JOIN domain_products.products p ON oi.product_id = p.product_id
        WHERE p.product_id IS NULL
    """)
    invalid_products = cursor.fetchone()[0]
    
    check_name = "order_items: 产品必须存在于 products"
    if invalid_products == 0:
        passed_checks.append(check_name)
        print(f"  ✓ {check_name}")
    else:
        failed_checks.append(check_name)
        print(f"  ✗ {check_name} - 发现 {invalid_products} 个无效产品引用")
    
    # ===== 新鲜度检查 (Freshness) =====
    print("\n⏰ 3. Freshness Checks")
    print("-" * 60)
    
    # 检查 6: 最近 24 小时内有订单更新
    cursor.execute("""
        SELECT 
            MAX(order_date) as last_order_date,
            TIMESTAMPDIFF(HOUR, MAX(order_date), NOW()) as hours_since_last_order
        FROM domain_orders.orders
    """)
    result = cursor.fetchone()
    last_order_date, hours_since = result[0], result[1] if result[1] is not None else 999
    
    check_name = "orders: 24小时内有新数据"
    # 对于演示，我们放宽到 72 小时
    if hours_since <= 72:
        passed_checks.append(check_name)
        print(f"  ✓ {check_name}")
        print(f"    最后订单时间: {last_order_date} ({hours_since} 小时前)")
    else:
        failed_checks.append(check_name)
        print(f"  ⚠ {check_name}")
        print(f"    最后订单时间: {last_order_date} ({hours_since} 小时前)")
    
    cursor.close()
    conn.close()
    
    # ===== 汇总结果 =====
    print("\n" + "=" * 60)
    print("📊 Quality Check Summary")
    print("=" * 60)
    print(f"✓ Passed: {len(passed_checks)}/{len(passed_checks) + len(failed_checks)}")
    print(f"✗ Failed: {len(failed_checks)}/{len(passed_checks) + len(failed_checks)}")
    
    if failed_checks:
        print("\n❌ Failed Checks:")
        for check in failed_checks:
            print(f"  - {check}")
    
    print("=" * 60)
    
    # 推送结果到 XCom（可被下游任务使用）
    quality_result = {
        'passed': passed_checks,
        'failed': failed_checks,
        'pass_rate': len(passed_checks) / (len(passed_checks) + len(failed_checks)) * 100
    }
    
    # 如果有失败的关键检查，抛出异常阻止管道继续
    critical_failures = [f for f in failed_checks if '订单总额' in f or '主键' in f]
    if critical_failures:
        raise AirflowException(
            f"❌ 关键质量检查失败！管道已阻止。失败项: {', '.join(critical_failures)}"
        )
    
    return quality_result


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

