#!/bin/bash
# Initialize / refresh Data Products (dp_*) views in MariaDB
#
# Why: mariadb/init scripts only run on first boot (empty volume). This script
# can be re-run any time to ensure dp_* views exist.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

SQL_FILE="${1:-examples/datamesh-mvp/sql/03-data-products.sql}"

if [ ! -f "$SQL_FILE" ]; then
  echo "❌ SQL file not found: $SQL_FILE"
  exit 1
fi

echo "🧩 Initializing Data Products views from: $SQL_FILE"

MARIADB_CONTAINER="${MARIADB_CONTAINER:-datamesh-mariadb}"
MARIADB_USER="${MARIADB_USER:-datamesh}"
MARIADB_PASSWORD="${MARIADB_PASSWORD:-datamesh123}"

echo "⏳ Waiting for MariaDB to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
  if docker exec "$MARIADB_CONTAINER" mariadb -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" -e "SELECT 1" >/dev/null 2>&1; then
    echo "✅ MariaDB is ready!"
    break
  fi
  attempt=$((attempt + 1))
  echo "   Attempt $attempt/$max_attempts..."
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo "❌ MariaDB did not become ready in time"
  exit 1
fi

echo "🚀 Applying Data Products SQL..."
docker exec -i "$MARIADB_CONTAINER" mariadb -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" < "$SQL_FILE"

echo "✅ Data Products initialized/refreshed."


