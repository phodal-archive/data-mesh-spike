"""
测试 Data Mesh MVP Pipeline
"""
import pytest
from datetime import datetime
from airflow.models import DagBag


class TestDataMeshMVPPipeline:
    """测试 DataMesh MVP Pipeline DAG"""

    @pytest.fixture(scope="class")
    def dagbag(self):
        """加载 DAG"""
        import os
        dags_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return DagBag(dag_folder=dags_folder, include_examples=False)

    def test_dag_loaded(self, dagbag):
        """测试 DAG 是否成功加载"""
        dag = dagbag.get_dag(dag_id='datamesh_mvp_pipeline')
        assert dag is not None, "DAG 'datamesh_mvp_pipeline' 未找到"
        assert len(dagbag.import_errors) == 0, f"DAG 导入错误: {dagbag.import_errors}"

    def test_dag_structure(self, dagbag):
        """测试 DAG 结构"""
        dag = dagbag.get_dag(dag_id='datamesh_mvp_pipeline')
        
        # 检查任务数量
        assert len(dag.tasks) == 5, "应该有 5 个任务"
        
        # 检查任务列表
        task_ids = [task.task_id for task in dag.tasks]
        expected_tasks = [
            'start_pipeline',
            'validate_data_quality',
            'refresh_data_products',
            'generate_kpi_report',
            'notify_data_products_ready'
        ]
        assert set(task_ids) == set(expected_tasks), f"任务列表不匹配: {task_ids}"

    def test_dag_dependencies(self, dagbag):
        """测试任务依赖关系"""
        dag = dagbag.get_dag(dag_id='datamesh_mvp_pipeline')
        
        # 获取任务
        start_task = dag.get_task('start_pipeline')
        validate_task = dag.get_task('validate_data_quality')
        refresh_task = dag.get_task('refresh_data_products')
        generate_task = dag.get_task('generate_kpi_report')
        notify_task = dag.get_task('notify_data_products_ready')
        
        # 检查依赖关系
        assert validate_task in start_task.downstream_list
        assert refresh_task in validate_task.downstream_list
        assert generate_task in refresh_task.downstream_list
        assert notify_task in generate_task.downstream_list

    def test_dag_schedule(self, dagbag):
        """测试 DAG 调度配置"""
        dag = dagbag.get_dag(dag_id='datamesh_mvp_pipeline')
        
        assert dag.schedule_interval == '@daily', "调度间隔应该是 @daily"
        assert dag.catchup is False, "catchup 应该是 False"

    def test_dag_default_args(self, dagbag):
        """测试 DAG 默认参数"""
        dag = dagbag.get_dag(dag_id='datamesh_mvp_pipeline')
        
        assert dag.default_args['owner'] == 'datamesh-team'
        assert dag.default_args['retries'] == 1

    def test_dag_tags(self, dagbag):
        """测试 DAG 标签"""
        dag = dagbag.get_dag(dag_id='datamesh_mvp_pipeline')
        
        expected_tags = {'datamesh', 'mvp', 'data-product'}
        assert set(dag.tags) == expected_tags


class TestDataQualityValidation:
    """测试数据质量验证函数"""

    def test_quality_validation_mock(self, mocker):
        """测试质量验证逻辑（使用 mock）"""
        # 导入函数
        from datamesh_mvp_pipeline import validate_data_quality
        
        # Mock MySQL 连接
        mock_conn = mocker.MagicMock()
        mock_cursor = mocker.MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock 查询结果
        mock_cursor.fetchone.side_effect = [
            (10, 10, 0),  # customers 主键检查
            (0,),         # orphan orders
            (0,),         # invalid prices
            [],           # inconsistent orders
            (0,),         # invalid products
            (datetime.now(), 5),  # freshness check
        ]
        mock_cursor.fetchall.return_value = []
        
        # Mock mysql.connector.connect
        mocker.patch('mysql.connector.connect', return_value=mock_conn)
        
        # 执行验证
        result = validate_data_quality()
        
        # 验证结果
        assert 'passed' in result
        assert 'failed' in result
        assert 'pass_rate' in result
        assert isinstance(result['passed'], list)
        assert isinstance(result['failed'], list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

