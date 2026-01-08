#!/bin/bash

# Data Mesh MVP 端口转发脚本
# 用于 Colima 环境下的端口映射

set -e

echo "📡 Setting up port forwarding for Data Mesh MVP..."

# 保存 SSH 配置
colima ssh-config > /tmp/colima_ssh_config

# 检查是否已有端口转发进程
if pgrep -f "ssh.*colima.*-L" > /dev/null; then
    echo "⚠️  Port forwarding already running. Killing existing processes..."
    pkill -f "ssh.*colima.*-L" || true
    sleep 2
fi

# 启动端口转发
echo "🔌 Starting port forwarding..."
ssh -F /tmp/colima_ssh_config -N \
  -L 3000:localhost:3000 \
  -L 8080:localhost:8080 \
  -L 8081:localhost:8081 \
  -L 8089:localhost:8089 \
  -L 8585:localhost:8585 \
  -L 8586:localhost:8586 \
  -L 9090:localhost:9090 \
  -L 9200:localhost:9200 \
  -L 16686:localhost:16686 \
  -L 7007:localhost:7007 \
  -L 7474:localhost:7474 \
  -L 7687:localhost:7687 \
  colima &

SSH_PID=$!
echo "✅ Port forwarding started (PID: $SSH_PID)"

sleep 2

# 测试连接
echo ""
echo "🧪 Testing connections..."
echo -n "  Grafana (3000): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "  Trino (8080): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/v1/info 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "  Airflow (8081): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/health 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "  Superset (8089): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:8089/health 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "  Neo4j (7474): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "  OpenMetadata (8585): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:8585/api/v1/system/version 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "  Prometheus (9090): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/-/healthy 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "  Jaeger (16686): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:16686/ 2>/dev/null && echo " ✅" || echo " ❌"
echo -n "  Backstage (7007): "; curl -s -o /dev/null -w "%{http_code}" http://localhost:7007/healthcheck 2>/dev/null && echo " ✅" || echo " ❌"

echo ""
echo "📋 Access URLs:"
echo "  - Backstage (Service Catalog): http://localhost:7007"
echo "  - Superset (BI Reports):       http://localhost:8089 (admin/admin)"
echo "  - Neo4j (Knowledge Graph):     http://localhost:7474 (neo4j/datamesh123)"
echo "  - Grafana (Ops Monitoring):    http://localhost:3000 (admin/admin)"
echo "  - Airflow (Orchestration):     http://localhost:8081 (admin/admin)"
echo "  - OpenMetadata (Data Catalog): http://localhost:8585 (admin/admin)"
echo "  - Trino (Query Engine):        http://localhost:8080"
echo "  - Jaeger (Tracing):            http://localhost:16686"
echo "  - Prometheus (Metrics):        http://localhost:9090"
echo ""
echo "💡 To stop port forwarding: pkill -f 'ssh.*colima.*-L'"

