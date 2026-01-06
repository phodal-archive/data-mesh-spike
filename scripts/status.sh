#!/bin/bash
# Data Mesh Learning Environment - Status Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "📊 Data Mesh Learning Environment Status"
echo "========================================="
echo ""

# Check Colima status
if command -v colima &> /dev/null; then
    echo "🐳 Colima Status:"
    colima status 2>/dev/null || echo "   Not running"
    echo ""
fi

echo "📦 Container Status:"
echo ""
docker compose -f docker-compose.stack1.yml ps 2>/dev/null || true
docker compose -f docker-compose.stack2.yml ps 2>/dev/null || true

echo ""
echo "🔍 Health Checks:"
echo ""

check_service() {
    local name=$1
    local url=$2
    if curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -q "200\|302\|301"; then
        echo "   ✅ $name is healthy"
    else
        echo "   ❌ $name is not responding"
    fi
}

check_service "OpenMetadata" "http://localhost:8585/healthcheck"
check_service "Airflow" "http://localhost:8081/health"
check_service "Trino" "http://localhost:8080/v1/info"
check_service "Backstage" "http://localhost:7007/healthcheck"
check_service "Grafana" "http://localhost:3000/api/health"
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Jaeger" "http://localhost:16686"
check_service "Elasticsearch" "http://localhost:9200/_cluster/health"

echo ""

