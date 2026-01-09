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
echo "🧩 Verifying OpenMetadata table details API..."

# Some OpenMetadata setups can end up with a dangling Domain->Table relationship in Postgres,
# which breaks the UI when it requests `fields=domain` (it shows "No data available.").
# If detected, we soft-delete the orphan relationship rows.
TABLE_FQN="datamesh-mariadb.default.domain_customers.customers"

TOKEN=$(python3 - <<'PY'
import yaml
with open("openmetadata/mariadb-ingestion.yaml", "r") as f:
    cfg = yaml.safe_load(f)
print(cfg["workflowConfig"]["openMetadataServerConfig"]["securityConfig"]["jwtToken"])
PY
)

RESP_FILE="/tmp/openmetadata_table_domain_check.json"
HTTP_CODE=$(curl -s -o "$RESP_FILE" -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8585/api/v1/tables/name/${TABLE_FQN}?fields=domain&include=all" || true)

if [[ "$HTTP_CODE" == "404" ]]; then
  DOMAIN_ID=$(python3 - <<'PY'
import json
import re
from pathlib import Path

body = Path("/tmp/openmetadata_table_domain_check.json").read_text(encoding="utf-8").strip()
try:
    obj = json.loads(body)
except Exception:
    print("")
    raise SystemExit(0)

msg = obj.get("message", "")
m = re.search(r"domain instance for ([0-9a-f\\-]{36}) not found", msg)
print(m.group(1) if m else "")
PY
)

  if [[ -n "$DOMAIN_ID" ]]; then
    echo "⚠️  Found orphan OpenMetadata domain relationship ($DOMAIN_ID). Fixing..."
    docker exec -i datamesh-openmetadata-postgres psql -U openmetadata -d openmetadata -c \
      "UPDATE entity_relationship SET deleted=true WHERE fromid='${DOMAIN_ID}' AND fromentity='domain' AND relation=10;"
    echo "✅ Orphan relationship soft-deleted. Please refresh OpenMetadata UI if it was open."
  fi
fi

echo ""
echo "✅ Ingestion completed! Visit http://localhost:8585 to explore the data catalog."

