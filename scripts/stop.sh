#!/bin/bash
# Data Mesh Learning Environment - Stop Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🛑 Stopping Data Mesh Learning Environment..."

case "${1:-all}" in
    stack1)
        echo "Stopping Stack 1..."
        docker compose -f docker-compose.stack1.yml down
        ;;
    stack2)
        echo "Stopping Stack 2..."
        docker compose -f docker-compose.stack2.yml down
        ;;
    all)
        echo "Stopping all services..."
        docker compose -f docker-compose.stack2.yml down 2>/dev/null || true
        docker compose -f docker-compose.stack1.yml down
        ;;
    clean)
        echo "Stopping all services and removing volumes..."
        docker compose -f docker-compose.stack2.yml down -v 2>/dev/null || true
        docker compose -f docker-compose.stack1.yml down -v
        docker network rm datamesh-network 2>/dev/null || true
        ;;
    *)
        echo "Usage: $0 [stack1|stack2|all|clean]"
        exit 1
        ;;
esac

echo "✅ Services stopped!"

