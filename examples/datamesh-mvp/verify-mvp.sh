#!/bin/bash
# ============================================
# Data Mesh MVP 完整验证脚本
# 验证所有组件是否正常工作、数据链路是否闭环
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           Data Mesh MVP 完整验证                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

check_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    PASSED=$((PASSED + 1))
}

check_fail() {
    echo -e "  ${RED}✗${NC} $1"
    FAILED=$((FAILED + 1))
}

check_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

section() {
    echo ""
    echo -e "${CYAN}━━━ $1 ━━━${NC}"
}

# ============================================
# 1. 检查容器状态
# ============================================
section "1. 容器状态检查"

# Stack 1 服务
stack1_services=("datamesh-mariadb" "datamesh-trino" "datamesh-airflow-webserver" "datamesh-airflow-scheduler" "datamesh-openmetadata" "datamesh-elasticsearch")
# Stack 2 服务
stack2_services=("datamesh-prometheus" "datamesh-grafana" "datamesh-jaeger" "datamesh-otel-collector" "datamesh-blackbox-exporter" "datamesh-pushgateway" "datamesh-superset" "datamesh-neo4j" "datamesh-backstage")

echo "  Stack 1 (数据平台核心):"
for service in "${stack1_services[@]}"; do
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${service}$"; then
        check_pass "$service"
    else
        check_fail "$service 未运行"
    fi
done

echo ""
echo "  Stack 2 (可观测性 & 门户):"
for service in "${stack2_services[@]}"; do
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${service}$"; then
        check_pass "$service"
    else
        # pushgateway/blackbox/backstage 可能是可选的
        if [[ "$service" == "datamesh-backstage" || "$service" == "datamesh-pushgateway" || "$service" == "datamesh-blackbox-exporter" ]]; then
            check_warn "$service 未运行 (可选)"
        else
            check_fail "$service 未运行"
        fi
    fi
done

# ============================================
# 2. HTTP 健康检查
# ============================================
section "2. HTTP 健康检查"

check_http() {
    local name=$1
    local url=$2
    local code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null || echo "000")
    if [[ "$code" =~ ^(200|204|301|302)$ ]]; then
        check_pass "$name ($url)"
    else
        check_fail "$name ($url) - HTTP $code"
    fi
}

check_http "Trino" "http://localhost:8080/v1/info"
check_http "Airflow" "http://localhost:8081/health"
check_http "OpenMetadata" "http://localhost:8585/api/v1/system/version"
check_http "Prometheus" "http://localhost:9090/-/healthy"
check_http "Grafana" "http://localhost:3000/api/health"
check_http "Jaeger" "http://localhost:16686"
check_http "Superset" "http://localhost:8089/health"
check_http "Neo4j" "http://localhost:7474"

# ============================================
# 3. 数据域连通性 (Trino → MariaDB)
# ============================================
section "3. 数据域连通性 (Trino 跨域查询)"

trino_scalar() {
    # 用 TSV 输出格式拿到稳定的标量结果（避免 warning/表格格式干扰）
    docker exec datamesh-trino trino --output-format TSV --execute "$1" 2>/dev/null \
      | tr -d '\r' \
      | grep -E '^[0-9]+(\\.[0-9]+)?$' \
      | tail -1
}

trino_row() {
    # 返回最后一行数据（用于 KPI 等非纯数字输出）
    docker exec datamesh-trino trino --output-format TSV --execute "$1" 2>/dev/null \
      | tr -d '\r' \
      | tail -1
}

domains=("domain_customers.customers" "domain_orders.orders" "domain_products.products")
for table in "${domains[@]}"; do
    result=$(trino_scalar "SELECT COUNT(*) FROM mariadb.$table")
    if [[ "$result" =~ ^[0-9]+$ ]] && [ "$result" -gt 0 ]; then
        check_pass "mariadb.$table: $result 条"
    else
        check_fail "mariadb.$table 查询失败"
    fi
done

# ============================================
# 4. 数据产品视图
# ============================================
section "4. 数据产品视图 (dp_*)"

data_products=("dp_customer_360" "dp_product_sales" "dp_order_fulfillment" "dp_business_kpis")
dp_all_ok=true

for dp in "${data_products[@]}"; do
    result=$(trino_scalar "SELECT COUNT(*) FROM mariadb.domain_analytics.$dp" 2>/dev/null)
    if [[ "$result" =~ ^[0-9]+$ ]] && [ "$result" -ge 0 ]; then
        check_pass "$dp: $result 条"
    else
        check_fail "$dp 不存在或查询失败"
        dp_all_ok=false
    fi
done

if [ "$dp_all_ok" = false ]; then
    echo ""
    echo -e "  ${YELLOW}💡 提示: 运行 ./scripts/init-data-products.sh 初始化数据产品视图${NC}"
fi

# ============================================
# 5. Airflow DAG 状态
# ============================================
section "5. Airflow DAG 状态"

dag_check() {
    local dag_id=$1
    # 检查 DAG 是否存在且未暂停
    local info=$(docker exec datamesh-airflow-scheduler airflow dags list 2>/dev/null | grep "^$dag_id" || echo "")
    if [ -n "$info" ]; then
        local paused=$(echo "$info" | awk '{print $NF}')
        if [ "$paused" == "False" ]; then
            check_pass "$dag_id (已启用)"
        else
            check_warn "$dag_id (已暂停)"
        fi
    else
        check_fail "$dag_id 不存在"
    fi
}

dag_check "datamesh_mvp_pipeline"
dag_check "sample_data_mesh_pipeline"

# 检查最近运行
echo ""
echo "  最近 DAG 运行:"
recent_run=$(
  docker exec datamesh-airflow-scheduler airflow dags list-runs -d datamesh_mvp_pipeline -o plain 2>/dev/null \
    | sed '1d' \
    | head -1 \
  || true
)
if [ -n "$recent_run" ] && [[ ! "$recent_run" =~ "No data found" ]]; then
    echo -e "    ${GREEN}→${NC} $recent_run"
else
    echo -e "    ${YELLOW}→${NC} 暂无运行记录 (可手动触发)"
fi

# ============================================
# 6. 可观测性链路 (Prometheus 指标)
# ============================================
section "6. 可观测性链路"

prom_query() {
    curl -s "http://localhost:9090/api/v1/query?query=$1" 2>/dev/null
}

prom_value() {
    # 从 Prometheus instant query JSON 里取第一个 result 的 value[1]
    # 输出为空表示没有数据
    local query="$1"
    local json
    json=$(prom_query "$query" || true)
    python3 - <<'PY' "$json"
import sys, json
raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    d = json.loads(raw) if raw else {}
    r = d.get("data", {}).get("result", [])
    print(r[0]["value"][1] if r else "")
except Exception:
    print("")
PY
}

# 检查 probe_success (Blackbox exporter)
echo "  Blackbox 探测 (probe_success):"
probe_result=$(prom_query 'probe_success')
if echo "$probe_result" | grep -q '"result":\[' && ! echo "$probe_result" | grep -q '"result":\[\]'; then
    check_pass "Blackbox exporter 正在探测服务"
else
    check_warn "Blackbox exporter 无数据 (可能未启动)"
fi

# 检查质量指标 (Pushgateway)
echo ""
echo "  质量指标 (datamesh_quality_*):"
quality_result=$(prom_query 'datamesh_quality_pass_rate')
pass_rate=$(prom_value 'datamesh_quality_pass_rate')
if [ -n "$pass_rate" ]; then
    check_pass "datamesh_quality_pass_rate = $pass_rate%"
else
    check_warn "质量指标未推送 (运行 DAG 后会出现)"
fi

# 检查 up 指标
echo ""
echo "  服务健康指标 (up):"
up_count_val=$(prom_value 'count(up)')
if [[ "$up_count_val" =~ ^[0-9]+(\\.[0-9]+)?$ ]] && [ "${up_count_val%%.*}" -gt 0 ]; then
    check_pass "Prometheus 正在监控 ${up_count_val} 个 job"
else
    check_fail "Prometheus 无 up 指标"
fi

# ============================================
# 7. 业务 KPI 概览
# ============================================
section "7. 业务 KPI 概览"

kpi_result=$(trino_row "SELECT total_customers, total_orders, total_revenue, pending_orders FROM mariadb.domain_analytics.dp_business_kpis" 2>/dev/null)
if [ -n "$kpi_result" ]; then
    # 解析 KPI (格式: "value1","value2",...)
    IFS=$'\t' read -ra kpis <<< "$(echo "$kpi_result" | tr -d '\"')"
    echo -e "  ${GREEN}📊 业务指标:${NC}"
    echo "    • 客户总数:   ${kpis[0]:-N/A}"
    echo "    • 订单总数:   ${kpis[1]:-N/A}"
    echo "    • 总收入:     \$${kpis[2]:-N/A}"
    echo "    • 待处理订单: ${kpis[3]:-N/A}"
else
    check_warn "无法获取 KPI (数据产品可能未初始化)"
fi

# ============================================
# 8. 元数据目录 (OpenMetadata)
# ============================================
section "8. 元数据目录 (OpenMetadata)"

token=""
if command -v python3 >/dev/null 2>&1; then
    # 从 openmetadata/mariadb-ingestion.yaml 读取 jwtToken（用于调用受保护 API）
    token=$(python3 - <<'PY' "$PROJECT_DIR" 2>/dev/null || true
import sys
project_dir = sys.argv[1]
path = project_dir + "/openmetadata/mariadb-ingestion.yaml"
try:
    import yaml
    d = yaml.safe_load(open(path, "r", encoding="utf-8"))
    print(d["workflowConfig"]["openMetadataServerConfig"]["securityConfig"]["jwtToken"])
except Exception:
    print("")
PY
)
fi

auth_header=()
if [ -n "$token" ]; then
    auth_header=(-H "Authorization: Bearer $token")
fi

omd_tables=$(curl -s "${auth_header[@]}" "http://localhost:8585/api/v1/tables?limit=5" 2>/dev/null | grep -o '"name":"[^"]*"' | head -5 || echo "")
if [ -n "$omd_tables" ]; then
    check_pass "OpenMetadata 有已注册的表"
    echo "    示例: $(echo "$omd_tables" | head -3 | sed 's/"name":"//g' | sed 's/"//g' | tr '\n' ', ' | sed 's/,$//')"
else
    if [ -z "$token" ]; then
        check_warn "OpenMetadata tables API 需要 token（无法自动读取 token；请确认 openmetadata/mariadb-ingestion.yaml）"
    else
        check_warn "OpenMetadata 暂无表 (运行 ./scripts/run-ingestion.sh)"
    fi
fi

# ============================================
# 汇总报告
# ============================================
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                      验证汇总                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}✓ 通过: $PASSED${NC}"
echo -e "  ${RED}✗ 失败: $FAILED${NC}"
echo -e "  ${YELLOW}⚠ 警告: $WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "  ${GREEN}🎉 Data Mesh MVP 验证通过！${NC}"
    exit_code=0
else
    echo -e "  ${RED}❌ 有 $FAILED 项检查未通过，请查看上方详情${NC}"
    exit_code=1
fi

echo ""
echo "━━━ 快速访问 ━━━"
echo "  Trino UI:       http://localhost:8080"
echo "  Airflow UI:     http://localhost:8081  (admin/admin)"
echo "  OpenMetadata:   http://localhost:8585  (admin/admin)"
echo "  Superset:       http://localhost:8089  (admin/admin)"
echo "  Grafana:        http://localhost:3000  (admin/admin)"
echo "  Neo4j:          http://localhost:7474  (neo4j/datamesh123)"
echo "  Prometheus:     http://localhost:9090"
echo "  Jaeger:         http://localhost:16686"
echo ""
echo "━━━ 下一步 ━━━"
if [ $FAILED -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo "  1. 如果数据产品缺失:  ./scripts/init-data-products.sh"
    echo "  2. 如果元数据缺失:    ./scripts/run-ingestion.sh"
    echo "  3. 触发质量检查 DAG:  Airflow UI → datamesh_mvp_pipeline → Trigger"
fi
echo "  4. 查看质量日志:      ./scripts/view-quality-logs.sh"
echo ""

exit $exit_code
