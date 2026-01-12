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
    """Execute quality checks defined in data contracts (SodaCL compatible)"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def execute_check(self, check: Dict[str, Any], schema: str) -> Dict[str, Any]:
        """
        Execute a single quality check
        Returns: {
            'passed': bool,
            'expression': str,
            'severity': str,
            'message': str,
            'actual': Any (optional),
            'threshold': Any (optional)
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
            # Row count checks: row_count > 0
            if 'row_count' in expression and 'avg_row' not in expression:
                match = re.search(r'row_count\s*([><=!]+)\s*(\d+)', expression)
                if match:
                    operator, threshold = match.groups()
                    self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table}")
                    actual_count = self.cursor.fetchone()[0]
                    
                    result['passed'] = self._compare(actual_count, operator, int(threshold))
                    result['actual'] = actual_count
                    result['threshold'] = int(threshold)
            
            # Missing count checks: missing_count(column) = 0
            elif 'missing_count' in expression:
                match = re.search(r'missing_count\((\w+)\)\s*([><=!]+)\s*(\d+)', expression)
                if match:
                    column, operator, threshold = match.groups()
                    self.cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table} WHERE {column} IS NULL")
                    null_count = self.cursor.fetchone()[0]
                    
                    result['passed'] = self._compare(null_count, operator, int(threshold))
                    result['actual'] = null_count
                    result['threshold'] = int(threshold)
            
            # Duplicate count checks: duplicate_count(column) = 0
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
            
            # Invalid percent checks: invalid_percent(column) < 1%
            elif 'invalid_percent' in expression:
                match = re.search(r'invalid_percent\((\w+)\)\s*([><=!]+)\s*(\d+(?:\.\d+)?)\s*%?', expression)
                if match:
                    column = match.group(1)
                    operator = match.group(2)
                    threshold_pct = float(match.group(3))
                    
                    # Check for regex validation
                    if 'valid regex' in config:
                        regex_pattern = config['valid regex']
                        # Use SQL REGEXP for MariaDB
                        self.cursor.execute(f"""
                            SELECT 
                                COUNT(*) as total,
                                SUM(CASE WHEN {column} NOT REGEXP %s THEN 1 ELSE 0 END) as invalid
                            FROM {schema}.{table}
                            WHERE {column} IS NOT NULL
                        """, (regex_pattern,))
                        row = self.cursor.fetchone()
                        total, invalid = row[0], row[1] or 0
                        
                        if total > 0:
                            actual_pct = (invalid / total) * 100
                        else:
                            actual_pct = 0
                        
                        result['passed'] = self._compare(actual_pct, operator, threshold_pct)
                        result['actual'] = f"{actual_pct:.2f}%"
                        result['threshold'] = f"{threshold_pct}%"
                        result['invalid_count'] = invalid
                        result['total_count'] = total
                    else:
                        # No regex, skip with warning
                        result['passed'] = True
                        result['message'] = f"⚠️ invalid_percent requires 'valid regex' config: {expression}"
                        result['severity'] = 'warning'
            
            # Invalid count checks (enum validation): invalid_count(column) = 0
            elif 'invalid_count' in expression:
                match = re.search(r'invalid_count\((\w+)\)\s*([><=!]+)?\s*(\d+)?', expression)
                if match:
                    column = match.group(1)
                    operator = match.group(2) or '='
                    threshold = int(match.group(3)) if match.group(3) else 0
                    
                    if 'valid values' in config:
                        valid_values = config['valid values']
                        placeholders = ','.join(['%s'] * len(valid_values))
                        
                        self.cursor.execute(f"""
                            SELECT COUNT(*) FROM {schema}.{table}
                            WHERE {column} IS NOT NULL AND {column} NOT IN ({placeholders})
                        """, valid_values)
                        invalid_count = self.cursor.fetchone()[0]
                        
                        result['passed'] = self._compare(invalid_count, operator, threshold)
                        result['actual'] = invalid_count
                        result['threshold'] = threshold
                    else:
                        result['passed'] = True
                        result['message'] = f"⚠️ invalid_count requires 'valid values' config: {expression}"
                        result['severity'] = 'warning'
            
            # Average row checks: avg_row(column) > value OR avg(column) > value
            elif 'avg_row' in expression or (expression.strip().startswith('avg(') and ')' in expression):
                # Pattern: avg_row(column) > value OR avg(column) > value
                match = re.search(r'avg(?:_row)?\((\w+)\)\s*([><=!]+)\s*(\d+(?:\.\d+)?)', expression)
                if match:
                    column, operator, threshold = match.groups()
                    threshold = float(threshold)
                    
                    self.cursor.execute(f"SELECT AVG({column}) FROM {schema}.{table}")
                    avg_value = self.cursor.fetchone()[0] or 0
                    
                    result['passed'] = self._compare(float(avg_value), operator, threshold)
                    result['actual'] = round(float(avg_value), 2)
                    result['threshold'] = threshold
            
            # Tolerance-based equality checks (with config tolerance)
            elif 'tolerance' in config:
                # Expression like: total_revenue = total_quantity_sold * current_price
                tolerance_str = config.get('tolerance', '0%')
                tolerance_pct = float(tolerance_str.replace('%', '')) / 100 if '%' in tolerance_str else float(tolerance_str)
                
                # This is complex - we check if values are within tolerance
                # For MVP, we do a simplified check: count rows where difference > tolerance
                # Parse left = right pattern
                if '=' in expression and '>' not in expression and '<' not in expression:
                    parts = expression.split('=')
                    if len(parts) == 2:
                        left_expr = parts[0].strip()
                        right_expr = parts[1].strip()
                        
                        # Count rows where ABS(left - right) / GREATEST(ABS(left), ABS(right), 1) > tolerance
                        self.cursor.execute(f"""
                            SELECT COUNT(*) FROM {schema}.{table}
                            WHERE ABS(({left_expr}) - ({right_expr})) / 
                                  GREATEST(ABS({left_expr}), ABS({right_expr}), 1) > %s
                        """, (tolerance_pct,))
                        violation_count = self.cursor.fetchone()[0]
                        
                        result['passed'] = (violation_count == 0)
                        result['actual'] = f"{violation_count} rows outside tolerance"
                        result['threshold'] = f"tolerance {tolerance_str}"
                        result['violations'] = violation_count
                else:
                    result['passed'] = True
                    result['message'] = f"⚠️ Cannot parse tolerance check: {expression}"
                    result['severity'] = 'warning'
            
            # Simple field comparisons (e.g., "total_orders >= 0", "price > 0")
            elif any(op in expression for op in ['>=', '<=', '!=', '>', '<', '=']):
                # Find the operator (order matters: check multi-char ops first)
                for op in ['>=', '<=', '!=', '>', '<', '=']:
                    if op in expression:
                        parts = expression.split(op)
                        if len(parts) == 2:
                            field = parts[0].strip()
                            value = parts[1].strip()
                            
                            # Validate field name (simple alphanumeric + underscore)
                            if re.match(r'^[\w]+$', field):
                                try:
                                    # Try numeric comparison
                                    numeric_value = float(value)
                                    self.cursor.execute(f"""
                                        SELECT COUNT(*) FROM {schema}.{table}
                                        WHERE NOT ({field} {op} {numeric_value})
                                        AND {field} IS NOT NULL
                                    """)
                                    violation_count = self.cursor.fetchone()[0]
                                    result['passed'] = (violation_count == 0)
                                    result['violations'] = violation_count
                                except ValueError:
                                    # Non-numeric comparison
                                    result['passed'] = True
                                    result['message'] = f"⚠️ Skipping non-numeric comparison: {expression}"
                                    result['severity'] = 'warning'
                            else:
                                # Complex expression, try direct execution
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
            result['error'] = str(e)
        
        return result
    
    def _compare(self, actual, operator: str, threshold) -> bool:
        """Compare actual value with threshold using operator"""
        if actual is None:
            return False
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
