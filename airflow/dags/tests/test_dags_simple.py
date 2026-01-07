"""
简化的测试 - 不依赖 Airflow 数据库
"""
import pytest
from datetime import datetime
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDAGSyntax:
    """测试 DAG 文件语法正确性"""

    def test_dag_import(self):
        """测试能否成功导入 DAG"""
        try:
            import datamesh_mvp_pipeline
            assert hasattr(datamesh_mvp_pipeline, 'dag')
        except Exception as e:
            pytest.fail(f"DAG import failed: {e}")

    def test_dag_structure(self):
        """测试 DAG 基本结构"""
        from datamesh_mvp_pipeline import dag
        
        # 检查 DAG ID
        assert dag.dag_id == 'datamesh_mvp_pipeline'
        
        # 检查任务数量
        assert len(dag.tasks) == 5, f"Expected 5 tasks, got {len(dag.tasks)}"
        
        # 检查任务列表
        task_ids = sorted([task.task_id for task in dag.tasks])
        expected_tasks = sorted([
            'start_pipeline',
            'validate_data_quality',
            'refresh_data_products',
            'generate_kpi_report',
            'notify_data_products_ready'
        ])
        assert task_ids == expected_tasks, f"Task IDs mismatch: {task_ids}"

    def test_dag_schedule(self):
        """测试 DAG 调度配置"""
        from datamesh_mvp_pipeline import dag
        
        assert dag.schedule_interval == '@daily'
        assert dag.catchup is False

    def test_dag_default_args(self):
        """测试 DAG 默认参数"""
        from datamesh_mvp_pipeline import dag
        
        assert dag.default_args['owner'] == 'datamesh-team'
        assert dag.default_args['retries'] == 1

    def test_dag_tags(self):
        """测试 DAG 标签"""
        from datamesh_mvp_pipeline import dag
        
        expected_tags = {'datamesh', 'mvp', 'data-product'}
        assert set(dag.tags) == expected_tags


class TestDataQualityFunction:
    """测试数据质量验证函数"""

    def test_function_signature(self):
        """测试函数签名"""
        from datamesh_mvp_pipeline import validate_data_quality
        
        import inspect
        sig = inspect.signature(validate_data_quality)
        assert 'context' in sig.parameters

    def test_quality_validation_mock(self, mocker):
        """测试质量验证逻辑（使用 mock）"""
        from datamesh_mvp_pipeline import validate_data_quality
        
        # Mock MySQL 连接
        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock 查询结果 - 模拟全部通过的情况
        mock_cursor.fetchone.side_effect = [
            (10, 10, 0),                   # customers 主键检查: total, unique, null
            (0,),                          # orphan orders
            (0,),                          # invalid prices
            (0,),                          # invalid products
            (datetime.now(), 5),           # freshness check
        ]
        mock_cursor.fetchall.return_value = []  # 没有不一致的订单
        
        # Mock mysql.connector.connect
        mocker.patch('mysql.connector.connect', return_value=mock_conn)
        
        # 执行验证
        result = validate_data_quality()
        
        # 验证结果结构
        assert 'passed' in result
        assert 'failed' in result
        assert 'pass_rate' in result
        assert isinstance(result['passed'], list)
        assert isinstance(result['failed'], list)
        assert isinstance(result['pass_rate'], (int, float))
        
        # 验证连接被调用
        mock_conn.cursor.assert_called()
        mock_cursor.close.assert_called()
        mock_conn.close.assert_called()


class TestTaskOperators:
    """测试任务操作器类型"""

    def test_python_operators(self):
        """测试 PythonOperator 任务"""
        from datamesh_mvp_pipeline import dag
        from airflow.operators.python import PythonOperator
        
        python_tasks = [
            'start_pipeline',
            'validate_data_quality',
            'generate_kpi_report',
            'notify_data_products_ready'
        ]
        
        for task_id in python_tasks:
            task = dag.get_task(task_id)
            assert isinstance(task, PythonOperator), \
                f"Task {task_id} should be PythonOperator"

    def test_bash_operator(self):
        """测试 BashOperator 任务"""
        from datamesh_mvp_pipeline import dag
        from airflow.operators.bash import BashOperator
        
        task = dag.get_task('refresh_data_products')
        assert isinstance(task, BashOperator), \
            "Task refresh_data_products should be BashOperator"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

