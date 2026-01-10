"""
Data Contract loader and validator for Airflow
"""
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class DataContract:
    """Data Contract representation"""
    
    def __init__(self, contract_data: Dict[str, Any]):
        self.data = contract_data
        self.id = contract_data.get('id', '')
        self.info = contract_data.get('info', {})
        self.models = contract_data.get('models', {})
        self.quality = contract_data.get('quality', {})
        self.servicelevels = contract_data.get('servicelevels', [])
        self.dependencies = contract_data.get('dependencies', [])
    
    @property
    def title(self) -> str:
        return self.info.get('title', 'Unknown')
    
    @property
    def owner(self) -> str:
        return self.info.get('owner', 'Unknown')
    
    @property
    def version(self) -> str:
        return self.info.get('version', '0.0.0')
    
    def get_quality_checks(self) -> List[Dict[str, Any]]:
        """Extract quality checks from contract"""
        checks = []
        spec = self.quality.get('specification', {})
        
        for check_set_name, check_list in spec.items():
            # Format: "checks for table_name"
            table_match = re.search(r'checks for (\w+)', check_set_name)
            table_name = table_match.group(1) if table_match else 'unknown'
            
            for check in check_list:
                if isinstance(check, dict):
                    for check_expr, check_config in check.items():
                        checks.append({
                            'table': table_name,
                            'expression': check_expr,
                            'config': check_config if isinstance(check_config, dict) else {},
                            'severity': check_config.get('severity', 'critical') if isinstance(check_config, dict) else 'critical'
                        })
        
        return checks


class ContractLoader:
    """Load data contracts from YAML files"""
    
    def __init__(self, contracts_dir: str):
        self.contracts_dir = Path(contracts_dir)
    
    def load_contract(self, contract_id: str) -> Optional[DataContract]:
        """Load a specific contract by ID"""
        contract_file = self.contracts_dir / f"{contract_id}.yaml"
        
        if not contract_file.exists():
            print(f"⚠️  Contract file not found: {contract_file}")
            return None
        
        try:
            with open(contract_file, 'r', encoding='utf-8') as f:
                contract_data = yaml.safe_load(f)
                return DataContract(contract_data)
        except Exception as e:
            print(f"❌ Error loading contract {contract_id}: {e}")
            return None
    
    def load_all_contracts(self) -> List[DataContract]:
        """Load all contracts from directory"""
        contracts = []
        
        if not self.contracts_dir.exists():
            print(f"⚠️  Contracts directory not found: {self.contracts_dir}")
            return contracts
        
        for contract_file in self.contracts_dir.glob("*.yaml"):
            if contract_file.name == "README.md":
                continue
            
            try:
                with open(contract_file, 'r', encoding='utf-8') as f:
                    contract_data = yaml.safe_load(f)
                    contracts.append(DataContract(contract_data))
            except Exception as e:
                print(f"⚠️  Skipping {contract_file.name}: {e}")
        
        return contracts


class QualityCheckExecutor:
    """Execute quality checks defined in data contracts"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def execute_check(self, check: Dict[str, Any], schema: str) -> Dict[str, Any]:
        """
        Execute a single quality check
        Returns: {
            'passed': bool,
            'expression': str,
            'severity': str,
            'message': str
        }
        """
        table = check['table']
        expression = check['expression']
        severity = check['severity']
        config = check['config']
        
        # Parse check expression (simplified SodaCL parser)
        result = {
            'passed': False,
            'expression': expression,
            'severity': severity,
            'message': config.get('name', expression)
        }
        
        try:
            # Row count checks
            if 'row_count' in expression:
                match = re.search(r'row_count\s*([><=!]+)\s*(\d+)', expression)
                if match:
                    operator, threshold = match.groups()
                    self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                    actual_count = self.cursor.fetchone()[0]
                    
                    result['passed'] = self._compare(actual_count, operator, int(threshold))
                    result['actual'] = actual_count
                    result['threshold'] = int(threshold)
            
            # Missing count checks
            elif 'missing_count' in expression:
                match = re.search(r'missing_count\((\w+)\)\s*([><=!]+)\s*(\d+)', expression)
                if match:
                    column, operator, threshold = match.groups()
                    self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table} WHERE {column} IS NULL")
                    null_count = self.cursor.fetchone()[0]
                    
                    result['passed'] = self._compare(null_count, operator, int(threshold))
                    result['actual'] = null_count
                    result['threshold'] = int(threshold)
            
            # Duplicate count checks
            elif 'duplicate_count' in expression:
                match = re.search(r'duplicate_count\((\w+)\)\s*([><=!]+)\s*(\d+)', expression)
                if match:
                    column, operator, threshold = match.groups()
                    self.cursor.execute(f"""
                        SELECT COUNT(*) - COUNT(DISTINCT {column})
                        FROM {schema}.{table}
                    """)
                    dup_count = self.cursor.fetchone()[0]
                    
                    result['passed'] = self._compare(dup_count, operator, int(threshold))
                    result['actual'] = dup_count
                    result['threshold'] = int(threshold)
            
            # Invalid count checks (enum validation)
            elif 'invalid_count' in expression:
                match = re.search(r'invalid_count\((\w+)\)', expression)
                if match and 'valid values' in config:
                    column = match.group(1)
                    valid_values = config['valid values']
                    placeholders = ','.join(['%s'] * len(valid_values))
                    
                    self.cursor.execute(f"""
                        SELECT COUNT(*) FROM {schema}.{table}
                        WHERE {column} NOT IN ({placeholders})
                    """, valid_values)
                    invalid_count = self.cursor.fetchone()[0]
                    
                    result['passed'] = (invalid_count == 0)
                    result['actual'] = invalid_count
            
            # Simple field comparisons (e.g., "total_orders >= 0")
            elif any(op in expression for op in ['>=', '<=', '>', '<', '=']):
                # Extract comparison from expression
                for op in ['>=', '<=', '>', '<', '=']:
                    if op in expression:
                        parts = expression.split(op)
                        if len(parts) == 2:
                            field, value = parts[0].strip(), parts[1].strip()
                            self.cursor.execute(f"""
                                SELECT COUNT(*) FROM {schema}.{table}
                                WHERE NOT ({expression})
                            """)
                            violation_count = self.cursor.fetchone()[0]
                            result['passed'] = (violation_count == 0)
                            result['violations'] = violation_count
                        break
            
            else:
                # Unsupported check type - mark as warning
                result['passed'] = True
                result['message'] = f"⚠️ Unsupported check (skipped): {expression}"
                result['severity'] = 'warning'
        
        except Exception as e:
            result['passed'] = False
            result['message'] = f"❌ Check failed with error: {str(e)}"
        
        return result
    
    def _compare(self, actual, operator: str, threshold) -> bool:
        """Compare actual value with threshold using operator"""
        if operator == '>':
            return actual > threshold
        elif operator == '>=':
            return actual >= threshold
        elif operator == '<':
            return actual < threshold
        elif operator == '<=':
            return actual <= threshold
        elif operator == '=' or operator == '==':
            return actual == threshold
        elif operator == '!=':
            return actual != threshold
        else:
            return False
