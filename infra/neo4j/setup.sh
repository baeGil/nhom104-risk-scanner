#!/usr/bin/env bash
# ==============================================================
# T6.1 — Setup Neo4j Self-Hosted
# ==============================================================
# Ubuntu/Debian setup script
#
# Usage:
#   chmod +x infra/neo4j/setup.sh
#   sudo ./infra/neo4j/setup.sh
# ==============================================================

set -euo pipefail

NEO4J_VERSION="5.18.0"
HEAP_INITIAL="2g"
HEAP_MAX="4g"
PAGE_CACHE="2g"
NEO4J_HOME="/var/lib/neo4j"
CONF_FILE="/etc/neo4j/neo4j.conf"

echo "=== T6.1: Setting up Neo4j ${NEO4J_VERSION} ==="

# 1. Cài đặt Java (prerequisite)
if ! command -v java &>/dev/null; then
    echo "Installing Java 17..."
    apt-get update -q
    apt-get install -y openjdk-17-jdk
fi

# 2. Add Neo4j repository
if [ ! -f /etc/apt/sources.list.d/neo4j.list ]; then
    echo "Adding Neo4j repository..."
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add -
    echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list
    apt-get update -q
fi

# 3. Install Neo4j
echo "Installing Neo4j..."
apt-get install -y neo4j=${NEO4J_VERSION}

# 4. Cấu hình memory
echo "Configuring memory: heap=${HEAP_MAX}, cache=${PAGE_CACHE}..."
cat >> "${CONF_FILE}" << EOF

# === Nhom104 Risk Scanner Configuration ===
server.memory.heap.initial_size=${HEAP_INITIAL}
server.memory.heap.max_size=${HEAP_MAX}
server.memory.pagecache.size=${PAGE_CACHE}

# Allow remote connections
server.default_listen_address=0.0.0.0

# Bolt connector (default port 7687)
server.bolt.enabled=true
server.bolt.listen_address=:7687

# HTTP connector (default port 7474)
server.http.enabled=true
server.http.listen_address=:7474
EOF

# 5. Enable APOC plugin (required for vector index)
echo "Enabling APOC plugin..."
APOC_JAR=$(find /usr/share/neo4j/plugins/ -name "apoc*.jar" 2>/dev/null | head -1)
if [ -z "$APOC_JAR" ]; then
    echo "WARNING: APOC plugin not found. Install manually from:"
    echo "  https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases"
else
    echo "APOC found: ${APOC_JAR}"
fi

# 6. Start Neo4j
echo "Starting Neo4j service..."
systemctl enable neo4j
systemctl start neo4j

# 7. Wait for startup
echo "Waiting for Neo4j to be ready..."
for i in $(seq 1 30); do
    if curl -s http://localhost:7474 > /dev/null 2>&1; then
        echo "Neo4j is ready!"
        break
    fi
    echo "  Attempt ${i}/30..."
    sleep 3
done

# 8. Health check
echo ""
echo "=== Health Check ==="
systemctl status neo4j --no-pager | head -10
echo ""
echo "Neo4j Browser: http://localhost:7474"
echo "Bolt URL:      bolt://localhost:7687"
echo "Default credentials: neo4j / neo4j (change on first login)"
echo ""
echo "Next step: Apply schema"
echo "  cypher-shell -u neo4j -p <password> -f output/neo4j_schema.cypher"
echo ""
echo "=== T6.1 Done ==="
