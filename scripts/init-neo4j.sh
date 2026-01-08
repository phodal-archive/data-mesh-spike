#!/bin/bash
# Neo4j Knowledge Graph Initialization Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🧠 Initializing Neo4j Domain Knowledge Graph..."

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Neo4j did not become ready in time"
    exit 1
fi

# Load the Cypher script
echo "📊 Loading domain knowledge graph..."
CYPHER_FILE="$PROJECT_DIR/neo4j/init/01-domain-knowledge-graph.cypher"

if [ ! -f "$CYPHER_FILE" ]; then
    echo "❌ Cypher file not found: $CYPHER_FILE"
    exit 1
fi

# Execute the Cypher script via Neo4j HTTP API
curl -s -X POST \
    -H "Content-Type: application/json" \
    -u neo4j:datamesh123 \
    -d "{\"statements\": [{\"statement\": \"$(cat "$CYPHER_FILE" | sed 's/"/\\"/g' | tr '\n' ' ')\"}]}" \
    http://localhost:7474/db/neo4j/tx/commit > /tmp/neo4j-init-result.json

# Check result
if grep -q '"errors":\[\]' /tmp/neo4j-init-result.json; then
    echo "✅ Domain knowledge graph initialized successfully!"
else
    echo "⚠️  Some errors occurred during initialization:"
    cat /tmp/neo4j-init-result.json | python3 -m json.tool 2>/dev/null || cat /tmp/neo4j-init-result.json
fi

echo ""
echo "🎉 Neo4j Knowledge Graph is ready!"
echo ""
echo "📋 Access URLs:"
echo "   - Neo4j Browser: http://localhost:7474"
echo "   - Username: neo4j"
echo "   - Password: datamesh123"
echo ""
echo "🔍 Try these queries:"
echo "   // View Data Mesh core concepts"
echo "   MATCH (dm:Concept {name: 'Data Mesh'})-[:CONSISTS_OF]->(c:Concept) RETURN dm, c"
echo ""
echo "   // View domain and data product relationships"
echo "   MATCH (d:Domain)-[:OWNS]->(dp:DataProduct) RETURN d, dp"
echo ""
echo "   // View complete knowledge graph"
echo "   MATCH (n) RETURN n LIMIT 50"

