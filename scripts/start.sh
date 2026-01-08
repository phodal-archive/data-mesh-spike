#!/bin/bash
# Data Mesh Learning Environment - Startup Script
# Compatible with Colima on macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🚀 Starting Data Mesh Learning Environment..."
echo ""

# Check if Colima is running
if command -v colima &> /dev/null; then
    if ! colima status &> /dev/null; then
        echo "⚠️  Colima is not running. Starting Colima..."
        colima start --cpu 4 --memory 8 --disk 60
    else
        echo "✅ Colima is running"
    fi
fi

# Check Docker
if ! docker info &> /dev/null; then
    echo "❌ Docker is not available. Please ensure Docker/Colima is running."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p airflow/dags airflow/logs airflow/plugins
mkdir -p mariadb/init
mkdir -p trino/etc trino/catalog
mkdir -p otel prometheus
mkdir -p grafana/provisioning/datasources grafana/provisioning/dashboards/json

# Set Airflow UID
export AIRFLOW_UID=$(id -u)

# Start services based on argument
case "${1:-all}" in
    stack1)
        echo "📦 Starting Stack 1 (Data Catalog & Orchestration)..."
        docker compose -f docker-compose.stack1.yml up -d
        echo "🧩 Ensuring Data Products (dp_*) views exist..."
        ./scripts/init-data-products.sh || true
        ;;
    stack2)
        echo "📦 Starting Stack 2 (Developer Portal & Observability)..."
        # Ensure network exists
        docker network create datamesh-network 2>/dev/null || true
        docker compose -f docker-compose.stack2.yml up -d
        ;;
    all)
        echo "📦 Starting all services..."
        docker compose -f docker-compose.stack1.yml up -d
        sleep 10  # Wait for network to be created
        docker compose -f docker-compose.stack2.yml up -d
        echo "🧩 Ensuring Data Products (dp_*) views exist..."
        ./scripts/init-data-products.sh || true
        ;;
    *)
        echo "Usage: $0 [stack1|stack2|all]"
        exit 1
        ;;
esac

echo ""
echo "✅ Services are starting up!"
echo ""
echo "📊 Service URLs (wait a few minutes for services to be ready):"
echo "   - OpenMetadata:    http://localhost:8585  (admin/admin)"
echo "   - Airflow:         http://localhost:8081  (admin/admin)"
echo "   - Trino:           http://localhost:8080"
echo "   - MariaDB:         localhost:3306         (datamesh/datamesh123)"
echo "   - Backstage:       http://localhost:7007"
echo "   - Grafana:         http://localhost:3000  (admin/admin)"
echo "   - Prometheus:      http://localhost:9090"
echo "   - Jaeger:          http://localhost:16686"
echo "   - Elasticsearch:   http://localhost:9200"
echo ""
echo "💡 Tips:"
echo "   - Check logs:      docker compose logs -f [service_name]"
echo "   - Stop services:   ./scripts/stop.sh"
echo "   - Check status:    ./scripts/status.sh"

