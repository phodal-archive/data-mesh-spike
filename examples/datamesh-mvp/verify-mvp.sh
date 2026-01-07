#!/bin/bash
# ============================================
# Data Mesh MVP 验证脚本
# 验证所有组件是否正常工作
# ============================================

set -e

echo "============================================"
echo "Data Mesh MVP 验证"
echo "============================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓ $1${NC}"
}

check_fail() {
    echo -e "${RED}✗ $1${NC}"
}

# 1. 检查服务状态
echo "1. 检查服务状态..."
echo "-------------------------------------------"

services=("datamesh-trino" "datamesh-mariadb" "datamesh-airflow-webserver" "datamesh-elasticsearch")
for service in "${services[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        check_pass "$service 运行中"
    else
        check_fail "$service 未运行"
    fi
done
echo ""

# 2. 测试 Trino 连接
echo "2. 测试 Trino 跨域查询..."
echo "-------------------------------------------"

result=$(docker exec datamesh-trino trino --execute "SELECT COUNT(*) FROM mariadb.domain_customers.customers" 2>/dev/null | tail -1)
if [ ! -z "$result" ] && [ "$result" -gt 0 ]; then
    check_pass "客户域: $result 条记录"
else
    check_fail "客户域查询失败"
fi

result=$(docker exec datamesh-trino trino --execute "SELECT COUNT(*) FROM mariadb.domain_orders.orders" 2>/dev/null | tail -1)
if [ ! -z "$result" ] && [ "$result" -gt 0 ]; then
    check_pass "订单域: $result 条记录"
else
    check_fail "订单域查询失败"
fi

result=$(docker exec datamesh-trino trino --execute "SELECT COUNT(*) FROM mariadb.domain_products.products" 2>/dev/null | tail -1)
if [ ! -z "$result" ] && [ "$result" -gt 0 ]; then
    check_pass "产品域: $result 条记录"
else
    check_fail "产品域查询失败"
fi
echo ""

# 3. 测试数据产品
echo "3. 测试数据产品..."
echo "-------------------------------------------"

data_products=("dp_customer_360" "dp_product_sales" "dp_order_fulfillment" "dp_business_kpis")
for dp in "${data_products[@]}"; do
    result=$(docker exec datamesh-trino trino --execute "SELECT COUNT(*) FROM mariadb.domain_analytics.$dp" 2>/dev/null | tail -1)
    if [ ! -z "$result" ] && [ "$result" -gt 0 ]; then
        check_pass "$dp: $result 条记录"
    else
        check_fail "$dp 查询失败"
    fi
done
echo ""

# 4. 测试 Airflow DAG
echo "4. 测试 Airflow DAG..."
echo "-------------------------------------------"

dag_status=$(docker exec datamesh-airflow-scheduler airflow dags list 2>/dev/null | grep datamesh_mvp_pipeline | awk '{print $NF}')
if [ "$dag_status" == "False" ]; then
    check_pass "datamesh_mvp_pipeline DAG 已启用"
else
    check_fail "datamesh_mvp_pipeline DAG 未启用"
fi
echo ""

# 5. 显示业务 KPI
echo "5. 业务 KPI 概览..."
echo "-------------------------------------------"
docker exec datamesh-trino trino --execute "
SELECT 
    'Total Customers' as metric, CAST(total_customers AS VARCHAR) as value FROM mariadb.domain_analytics.dp_business_kpis
UNION ALL
SELECT 'Total Orders', CAST(total_orders AS VARCHAR) FROM mariadb.domain_analytics.dp_business_kpis
UNION ALL
SELECT 'Total Revenue', CAST(total_revenue AS VARCHAR) FROM mariadb.domain_analytics.dp_business_kpis
UNION ALL
SELECT 'Pending Orders', CAST(pending_orders AS VARCHAR) FROM mariadb.domain_analytics.dp_business_kpis
" 2>/dev/null | tail -4 | while read line; do
    echo "  $line"
done
echo ""

echo "============================================"
echo "验证完成!"
echo "============================================"
echo ""
echo "访问以下 URL 查看更多:"
echo "  - Trino UI:       http://localhost:8080"
echo "  - Airflow UI:     http://localhost:8081 (admin/admin)"
echo "  - OpenMetadata:   http://localhost:8585 (admin/admin)"
echo ""

