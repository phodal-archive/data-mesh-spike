"""
Unit tests for data_contract_validator.py
Tests contract loading, parsing, and quality check execution
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_contract_validator import DataContract, ContractLoader, QualityCheckExecutor


class TestDataContract:
    """Tests for DataContract class"""
    
    def test_contract_basic_properties(self):
        """Test basic contract property extraction"""
        contract_data = {
            'id': 'dp-test',
            'info': {
                'title': 'Test Contract',
                'version': '1.0.0',
                'owner': 'Test Team'
            },
            'models': {
                'test_table': {
                    'fields': {'id': {'type': 'integer'}}
                }
            }
        }
        
        contract = DataContract(contract_data)
        
        assert contract.id == 'dp-test'
        assert contract.title == 'Test Contract'
        assert contract.version == '1.0.0'
        assert contract.owner == 'Test Team'
    
    def test_contract_default_values(self):
        """Test default values when properties are missing"""
        contract = DataContract({})
        
        assert contract.id == ''
        assert contract.title == 'Unknown'
        assert contract.version == '0.0.0'
        assert contract.owner == 'Unknown'
    
    def test_get_quality_checks_basic(self):
        """Test extracting quality checks from contract"""
        contract_data = {
            'quality': {
                'specification': {
                    'checks for test_table': [
                        {'row_count > 0': {'name': 'Has rows'}},
                        {'missing_count(id) = 0': {'name': 'ID not null', 'severity': 'critical'}}
                    ]
                }
            }
        }
        
        contract = DataContract(contract_data)
        checks = contract.get_quality_checks()
        
        assert len(checks) == 2
        assert checks[0]['table'] == 'test_table'
        assert checks[0]['expression'] == 'row_count > 0'
        assert checks[0]['config']['name'] == 'Has rows'
        assert checks[1]['severity'] == 'critical'
    
    def test_get_quality_checks_empty(self):
        """Test empty quality checks"""
        contract = DataContract({'quality': {}})
        checks = contract.get_quality_checks()
        
        assert checks == []


class TestContractLoader:
    """Tests for ContractLoader class"""
    
    def test_load_contract_not_found(self, tmp_path):
        """Test loading non-existent contract"""
        loader = ContractLoader(str(tmp_path))
        result = loader.load_contract('nonexistent')
        
        assert result is None
    
    def test_load_contract_success(self, tmp_path):
        """Test successful contract loading"""
        contract_file = tmp_path / "dp-test.yaml"
        contract_file.write_text("""
id: dp-test
info:
  title: Test Contract
  version: 1.0.0
  owner: Test Team
""")
        
        loader = ContractLoader(str(tmp_path))
        contract = loader.load_contract('dp-test')
        
        assert contract is not None
        assert contract.id == 'dp-test'
        assert contract.title == 'Test Contract'
    
    def test_load_all_contracts(self, tmp_path):
        """Test loading all contracts from directory"""
        # Create two contract files
        (tmp_path / "dp-one.yaml").write_text("id: dp-one\ninfo: {title: One}")
        (tmp_path / "dp-two.yaml").write_text("id: dp-two\ninfo: {title: Two}")
        (tmp_path / "README.md").write_text("# Readme")  # Should be ignored
        
        loader = ContractLoader(str(tmp_path))
        contracts = loader.load_all_contracts()
        
        assert len(contracts) == 2
        ids = {c.id for c in contracts}
        assert 'dp-one' in ids
        assert 'dp-two' in ids
    
    def test_load_all_contracts_empty_dir(self, tmp_path):
        """Test loading from empty directory"""
        loader = ContractLoader(str(tmp_path))
        contracts = loader.load_all_contracts()
        
        assert contracts == []
    
    def test_load_all_contracts_nonexistent_dir(self):
        """Test loading from non-existent directory"""
        loader = ContractLoader('/nonexistent/path')
        contracts = loader.load_all_contracts()
        
        assert contracts == []


class TestQualityCheckExecutor:
    """Tests for QualityCheckExecutor class"""
    
    @pytest.fixture
    def mock_cursor(self):
        """Create a mock database cursor"""
        cursor = Mock()
        cursor.fetchone = Mock()
        cursor.execute = Mock()
        return cursor
    
    def test_row_count_check_pass(self, mock_cursor):
        """Test row_count check that passes"""
        mock_cursor.fetchone.return_value = (10,)
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'test_table',
            'expression': 'row_count > 0',
            'severity': 'critical',
            'config': {'name': 'Has rows'}
        }
        
        result = executor.execute_check(check, 'test_schema')
        
        assert result['passed'] is True
        assert result['actual'] == 10
        mock_cursor.execute.assert_called()
    
    def test_row_count_check_fail(self, mock_cursor):
        """Test row_count check that fails"""
        mock_cursor.fetchone.return_value = (0,)
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'test_table',
            'expression': 'row_count > 0',
            'severity': 'critical',
            'config': {'name': 'Has rows'}
        }
        
        result = executor.execute_check(check, 'test_schema')
        
        assert result['passed'] is False
        assert result['actual'] == 0
    
    def test_missing_count_check(self, mock_cursor):
        """Test missing_count check"""
        mock_cursor.fetchone.return_value = (0,)
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'customers',
            'expression': 'missing_count(email) = 0',
            'severity': 'critical',
            'config': {'name': 'Email not null'}
        }
        
        result = executor.execute_check(check, 'domain_customers')
        
        assert result['passed'] is True
        assert result['actual'] == 0
    
    def test_duplicate_count_check(self, mock_cursor):
        """Test duplicate_count check"""
        mock_cursor.fetchone.return_value = (0,)
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'customers',
            'expression': 'duplicate_count(customer_id) = 0',
            'severity': 'critical',
            'config': {'name': 'ID unique'}
        }
        
        result = executor.execute_check(check, 'domain_customers')
        
        assert result['passed'] is True
    
    def test_invalid_count_with_valid_values(self, mock_cursor):
        """Test invalid_count check with valid values enum"""
        mock_cursor.fetchone.return_value = (0,)
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'customers',
            'expression': 'invalid_count(tier) = 0',
            'severity': 'critical',
            'config': {
                'name': 'Valid tier',
                'valid values': ['Bronze', 'Silver', 'Gold']
            }
        }
        
        result = executor.execute_check(check, 'domain_analytics')
        
        assert result['passed'] is True
    
    def test_invalid_count_without_config(self, mock_cursor):
        """Test invalid_count check without valid values config"""
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'test_table',
            'expression': 'invalid_count(status) = 0',
            'severity': 'warning',
            'config': {}  # No valid values
        }
        
        result = executor.execute_check(check, 'test_schema')
        
        # Should skip with warning
        assert result['passed'] is True
        assert result['severity'] == 'warning'
    
    def test_invalid_percent_with_regex(self, mock_cursor):
        """Test invalid_percent check with regex validation"""
        mock_cursor.fetchone.return_value = (100, 2)  # 100 total, 2 invalid
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'customers',
            'expression': 'invalid_percent(email) < 5%',
            'severity': 'warning',
            'config': {
                'name': 'Email format',
                'valid regex': '^[^@]+@[^@]+\\.[^@]+$'
            }
        }
        
        result = executor.execute_check(check, 'domain_analytics')
        
        assert result['passed'] is True  # 2% < 5%
        assert result['invalid_count'] == 2
        assert result['total_count'] == 100
    
    def test_avg_row_check(self, mock_cursor):
        """Test avg_row check"""
        mock_cursor.fetchone.return_value = (150.0,)
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'customers',
            'expression': 'avg_row(total_spent) > 100',
            'severity': 'warning',
            'config': {'name': 'Avg customer value'}
        }
        
        result = executor.execute_check(check, 'domain_analytics')
        
        assert result['passed'] is True
        assert result['actual'] == 150.0
    
    def test_avg_check_alternative_syntax(self, mock_cursor):
        """Test avg() check (alternative to avg_row)"""
        mock_cursor.fetchone.return_value = (50.0,)
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'orders',
            'expression': 'avg(total_amount) > 100',
            'severity': 'warning',
            'config': {'name': 'Avg order value'}
        }
        
        result = executor.execute_check(check, 'domain_orders')
        
        assert result['passed'] is False  # 50 < 100
        assert result['actual'] == 50.0
    
    def test_tolerance_check_pass(self, mock_cursor):
        """Test tolerance-based equality check that passes"""
        mock_cursor.fetchone.return_value = (0,)  # No violations
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'products',
            'expression': 'total_revenue = total_quantity_sold * current_price',
            'severity': 'warning',
            'config': {
                'name': 'Revenue calculation',
                'tolerance': '1%'
            }
        }
        
        result = executor.execute_check(check, 'domain_analytics')
        
        assert result['passed'] is True
        assert result['violations'] == 0
    
    def test_tolerance_check_fail(self, mock_cursor):
        """Test tolerance-based equality check that fails"""
        mock_cursor.fetchone.return_value = (5,)  # 5 violations
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'products',
            'expression': 'total_revenue = total_quantity_sold * current_price',
            'severity': 'warning',
            'config': {
                'name': 'Revenue calculation',
                'tolerance': '1%'
            }
        }
        
        result = executor.execute_check(check, 'domain_analytics')
        
        assert result['passed'] is False
        assert result['violations'] == 5
    
    def test_simple_comparison_pass(self, mock_cursor):
        """Test simple field comparison that passes"""
        mock_cursor.fetchone.return_value = (0,)  # No violations
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'products',
            'expression': 'price > 0',
            'severity': 'critical',
            'config': {'name': 'Positive price'}
        }
        
        result = executor.execute_check(check, 'domain_products')
        
        assert result['passed'] is True
        assert result['violations'] == 0
    
    def test_simple_comparison_fail(self, mock_cursor):
        """Test simple field comparison that fails"""
        mock_cursor.fetchone.return_value = (3,)  # 3 violations
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'customers',
            'expression': 'total_orders >= 0',
            'severity': 'critical',
            'config': {'name': 'Non-negative orders'}
        }
        
        result = executor.execute_check(check, 'domain_analytics')
        
        assert result['passed'] is False
        assert result['violations'] == 3
    
    def test_unsupported_check(self, mock_cursor):
        """Test unsupported check expression"""
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'test_table',
            'expression': 'some_unsupported_function()',
            'severity': 'info',
            'config': {'name': 'Unknown check'}
        }
        
        result = executor.execute_check(check, 'test_schema')
        
        # Should skip with warning
        assert result['passed'] is True
        assert result['severity'] == 'warning'
    
    def test_check_with_error(self, mock_cursor):
        """Test check that raises an exception"""
        mock_cursor.execute.side_effect = Exception("Database error")
        executor = QualityCheckExecutor(mock_cursor)
        
        check = {
            'table': 'test_table',
            'expression': 'row_count > 0',
            'severity': 'critical',
            'config': {'name': 'Has rows'}
        }
        
        result = executor.execute_check(check, 'test_schema')
        
        assert result['passed'] is False
        assert 'error' in result
        assert 'Database error' in result['error']


class TestCompareFunction:
    """Tests for the _compare helper function"""
    
    @pytest.fixture
    def executor(self):
        return QualityCheckExecutor(Mock())
    
    def test_compare_greater_than(self, executor):
        assert executor._compare(10, '>', 5) is True
        assert executor._compare(5, '>', 10) is False
        assert executor._compare(5, '>', 5) is False
    
    def test_compare_greater_equal(self, executor):
        assert executor._compare(10, '>=', 5) is True
        assert executor._compare(5, '>=', 5) is True
        assert executor._compare(4, '>=', 5) is False
    
    def test_compare_less_than(self, executor):
        assert executor._compare(5, '<', 10) is True
        assert executor._compare(10, '<', 5) is False
        assert executor._compare(5, '<', 5) is False
    
    def test_compare_less_equal(self, executor):
        assert executor._compare(5, '<=', 10) is True
        assert executor._compare(5, '<=', 5) is True
        assert executor._compare(6, '<=', 5) is False
    
    def test_compare_equal(self, executor):
        assert executor._compare(5, '=', 5) is True
        assert executor._compare(5, '==', 5) is True
        assert executor._compare(5, '=', 10) is False
    
    def test_compare_not_equal(self, executor):
        assert executor._compare(5, '!=', 10) is True
        assert executor._compare(5, '!=', 5) is False
    
    def test_compare_none_value(self, executor):
        assert executor._compare(None, '>', 5) is False
        assert executor._compare(None, '=', 0) is False
    
    def test_compare_invalid_operator(self, executor):
        assert executor._compare(5, 'invalid', 5) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
