#!/bin/bash

# Data Mesh MVP - OpenMetadata Ingestion Script
# 运行此脚本来采集 MariaDB 的元数据到 OpenMetadata

set -e

echo "🔍 Running OpenMetadata metadata ingestion..."

# 确保网络存在
if ! docker network inspect datamesh-network >/dev/null 2>&1; then
    echo "❌ Error: datamesh-network not found. Please start the Data Mesh stack first."
    exit 1
fi

# 运行 ingestion
docker run --rm \
  --network datamesh-network \
  -v "$(pwd)/openmetadata/mariadb-ingestion.yaml:/config/ingestion.yaml" \
  docker.getcollate.io/openmetadata/ingestion:1.3.1 \
  python -m metadata ingest -c /config/ingestion.yaml

echo ""
echo "✅ Ingestion completed! Visit http://localhost:8585 to explore the data catalog."

