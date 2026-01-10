#!/usr/bin/env python3
"""
OpenMetadata Lineage Populator
从数据契约和 SQL 视图定义中提取血缘关系，并推送到 OpenMetadata
"""
import yaml
import re
import requests
import json
from pathlib import Path
from typing import Dict, List, Set, Optional


class LineageExtractor:
    """从 SQL 和契约中提取血缘关系"""
    
    def __init__(self):
        self.table_pattern = re.compile(
            r'FROM\s+(\w+\.\w+\.\w+|\w+\.\w+)',
            re.IGNORECASE
        )
        self.join_pattern = re.compile(
            r'JOIN\s+(\w+\.\w+\.\w+|\w+\.\w+)',
            re.IGNORECASE
        )
    
    def extract_from_sql(self, sql: str) -> Set[str]:
        """从 SQL 中提取上游表"""
        upstream_tables = set()
        
        # 提取 FROM 子句中的表
        for match in self.table_pattern.finditer(sql):
            table = match.group(1)
            upstream_tables.add(self._normalize_table_name(table))
        
        # 提取 JOIN 子句中的表
        for match in self.join_pattern.finditer(sql):
            table = match.group(1)
            upstream_tables.add(self._normalize_table_name(table))
        
        return upstream_tables
    
    def extract_from_contract(self, contract_path: Path) -> Dict:
        """从数据契约中提取依赖关系"""
        with open(contract_path, 'r', encoding='utf-8') as f:
            contract = yaml.safe_load(f)
        
        product_id = contract.get('id', '')
        dependencies = contract.get('dependencies', [])
        
        upstream_tables = set()
        for dep in dependencies:
            if 'name' in dep:
                upstream_tables.add(dep['name'])
        
        # 从 models 中获取视图/表名
        models = contract.get('models', {})
        downstream_table = list(models.keys())[0] if models else None
        
        return {
            'product_id': product_id,
            'downstream': downstream_table,
            'upstream': list(upstream_tables)
        }
    
    def _normalize_table_name(self, table: str) -> str:
        """规范化表名（去除 catalog 前缀）"""
        parts = table.split('.')
        if len(parts) == 3:
            # mariadb.domain_customers.customers -> domain_customers.customers
            return f"{parts[1]}.{parts[2]}"
        return table


class OpenMetadataLineageClient:
    """OpenMetadata API 客户端，用于创建血缘关系"""
    
    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url.rstrip('/')
        self.token = jwt_token
        self.headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
    
    def get_table_fqn(self, service: str, database: str, schema: str, table: str) -> str:
        """构建完全限定名 (FQN)"""
        return f"{service}.{database}.{schema}.{table}"
    
    def get_table_id(self, fqn: str) -> Optional[str]:
        """通过 FQN 获取表的 ID"""
        encoded_fqn = requests.utils.quote(fqn, safe='')
        url = f"{self.base_url}/api/v1/tables/name/{encoded_fqn}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                table_data = response.json()
                return table_data.get('id')
            else:
                print(f"  ⚠️  Table not found: {fqn} (HTTP {response.status_code})")
                return None
        except Exception as e:
            print(f"  ❌ Error fetching table {fqn}: {e}")
            return None
    
    def create_lineage(self, upstream_fqn: str, downstream_fqn: str) -> bool:
        """创建血缘关系"""
        upstream_id = self.get_table_id(upstream_fqn)
        downstream_id = self.get_table_id(downstream_fqn)
        
        if not upstream_id or not downstream_id:
            print(f"    ✗ Cannot create lineage (missing IDs)")
            return False
        
        url = f"{self.base_url}/api/v1/lineage"
        
        lineage_data = {
            "edge": {
                "fromEntity": {
                    "id": upstream_id,
                    "type": "table"
                },
                "toEntity": {
                    "id": downstream_id,
                    "type": "table"
                }
            }
        }
        
        try:
            response = requests.put(url, headers=self.headers, json=lineage_data, timeout=10)
            if response.status_code in [200, 201]:
                print(f"    ✓ {upstream_fqn} → {downstream_fqn}")
                return True
            else:
                print(f"    ✗ Failed (HTTP {response.status_code}): {response.text[:100]}")
                return False
        except Exception as e:
            print(f"    ✗ Error creating lineage: {e}")
            return False


def main():
    print("=" * 70)
    print("🔗 OpenMetadata Lineage Populator")
    print("=" * 70)
    
    # Configuration
    project_dir = Path(__file__).parent.parent
    contracts_dir = project_dir / "contracts"
    sql_dir = project_dir / "airflow" / "dags" / "sql"
    
    openmetadata_url = "http://localhost:8585"
    # This token is from mariadb-ingestion.yaml (ingestion-bot)
    jwt_token = "eyJraWQiOiJHYjM4OWEtOWY3Ni1nZGpzLWE5MmotMDI0MmJrOTQzNTYiLCJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJvcGVuLW1ldGFkYXRhLm9yZyIsInN1YiI6ImluZ2VzdGlvbi1ib3QiLCJlbWFpbCI6ImluZ2VzdGlvbi1ib3RAb3Blbm1ldGFkYXRhLm9yZyIsImlzQm90Ijp0cnVlLCJ0b2tlblR5cGUiOiJCT1QiLCJpYXQiOjE3Njc3MTQ2NDUsImV4cCI6bnVsbH0.VPP66EO5fBvFZdUiEULKTkKLBt0irzJP_mraAXGaLBUfLV13XGg-b7YbrUoq8eTeIuRgvN6ZrAzKMetMmedRC76g5SrOoXZ4qy_g8THrOJl5G2ZQBtuLtKNi9Iz8n_5_jMhilm3WJnKraILG3nxUhkGOYlf-ZYGPti7og0zGicUN52gyUQAm04sJdTRqYwEePuHx0VVJJnNSE8M7ft-Pf0V2EbXDKiwAevu72JaE2AjeWuvuZWTwNKrY07S1PDIbvGj03LGED1-jTscUyNmQ7zunZfSyqDsdyPWUj5k4GsLYOi3R15s0wyhaRcD_M7-NXv50L4RoyzTHHAbjbbKC3Q"
    
    client = OpenMetadataLineageClient(openmetadata_url, jwt_token)
    extractor = LineageExtractor()
    
    # Service/database constants for MariaDB
    service_name = "datamesh-mariadb"
    database_name = "default"
    
    print(f"\n📋 Loading contracts from: {contracts_dir}")
    
    # Process each contract
    total_lineages = 0
    created_lineages = 0
    
    for contract_file in contracts_dir.glob("dp-*.yaml"):
        print(f"\n{'─' * 70}")
        print(f"📄 Processing: {contract_file.name}")
        
        lineage_info = extractor.extract_from_contract(contract_file)
        
        downstream_table = lineage_info['downstream']
        if not downstream_table:
            print("  ⚠️  No downstream table found in contract")
            continue
        
        # Construct downstream FQN (data products are in domain_analytics)
        downstream_fqn = client.get_table_fqn(
            service_name, database_name, "domain_analytics", downstream_table
        )
        
        print(f"  📊 Data Product: {downstream_table}")
        print(f"  ⬇️  Downstream FQN: {downstream_fqn}")
        
        if not lineage_info['upstream']:
            print("  ⚠️  No upstream dependencies defined")
            continue
        
        print(f"  ⬆️  Upstream tables:")
        for upstream_table in lineage_info['upstream']:
            # Parse schema.table from upstream
            parts = upstream_table.split('.')
            if len(parts) != 2:
                print(f"    ⚠️  Skipping invalid table name: {upstream_table}")
                continue
            
            upstream_schema, upstream_table_name = parts
            upstream_fqn = client.get_table_fqn(
                service_name, database_name, upstream_schema, upstream_table_name
            )
            
            print(f"    • {upstream_fqn}")
            
            total_lineages += 1
            if client.create_lineage(upstream_fqn, downstream_fqn):
                created_lineages += 1
    
    # Summary
    print(f"\n{'=' * 70}")
    print("📊 Lineage Creation Summary")
    print(f"{'=' * 70}")
    print(f"  Total lineage edges:    {total_lineages}")
    print(f"  ✓ Successfully created: {created_lineages}")
    print(f"  ✗ Failed:               {total_lineages - created_lineages}")
    print(f"{'=' * 70}")
    
    if created_lineages > 0:
        print(f"\n✅ Lineage populated! View in OpenMetadata:")
        print(f"   {openmetadata_url}/explore/tables")
    else:
        print(f"\n⚠️  No lineage created. Possible reasons:")
        print(f"   - Tables not yet ingested in OpenMetadata")
        print(f"   - Run: ./scripts/run-ingestion.sh")


if __name__ == "__main__":
    main()
