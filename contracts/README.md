# Data Mesh 数据契约 (Data Contracts)

数据契约是 Data Mesh 中数据产品的"API 规范"，定义了数据的结构、质量、SLA 和依赖关系。

## 契约清单

| 数据产品 | 契约文件 | 所有者 | 版本 |
|---------|---------|-------|------|
| Customer 360 | [`dp-customer-360.yaml`](./dp-customer-360.yaml) | Customer Team | 1.0.0 |
| Product Sales | [`dp-product-sales.yaml`](./dp-product-sales.yaml) | Analytics Team | 1.0.0 |
| Business KPIs | [`dp-business-kpis.yaml`](./dp-business-kpis.yaml) | Analytics Team | 1.0.0 |

## 契约规范

我们使用 [Data Contract Specification](https://datacontract.com/) 标准（v0.9.3）。

每个契约包含：

### 1. 基本信息 (info)
- 数据产品名称、版本、描述
- 所有者团队和联系方式

### 2. 服务器配置 (servers)
- 数据访问端点（Trino、数据库等）
- 连接参数

### 3. 数据模型 (models)
- 字段定义（类型、必填性、主键）
- PII 标记和分类
- 业务规则（枚举值、约束）

### 4. 质量规则 (quality)
- 完整性检查（非空、唯一性）
- 有效性检查（范围、格式、枚举）
- 一致性检查（跨字段逻辑）
- 业务规则检查

我们使用 **SodaCL** 格式定义质量规则（兼容 Great Expectations、dbt tests）。

### 5. 服务等级 (servicelevels)
- **freshness**: 数据刷新频率（1h、24h 等）
- **availability**: 可用性目标（99.9%）
- **latency**: 查询响应时间（< 5s）
- **completeness**: 数据完整性目标（100%）

### 6. 依赖关系 (dependencies)
- 上游数据源（表、视图）
- 依赖的其他数据产品

### 7. 链接 (links)
- Backstage 文档
- OpenMetadata 目录
- Trino 查询界面

## 在 Airflow 中使用契约

Airflow DAG `datamesh_mvp_pipeline` 会：

1. **加载契约**：从 `contracts/` 目录读取 YAML
2. **验证质量规则**：在 `validate_data_quality` 任务中执行质量检查
3. **记录结果**：推送到 Prometheus/Grafana

```python
# 伪代码示例
contract = load_contract('contracts/dp-customer-360.yaml')
results = validate_quality_checks(contract.quality.specification)
if results.critical_failures > 0:
    raise AirflowException("Quality checks failed!")
```

## 契约即代码 (Contract as Code)

契约文件存储在版本控制中，任何变更需要：

1. **Pull Request**: 提交契约变更
2. **Review**: 数据产品 owner 和消费者审查
3. **CI/CD**: 自动验证契约语法和兼容性
4. **部署**: 合并后自动应用到生产环境

## 契约变更管理

### 向后兼容变更（Minor）
- 添加可选字段
- 放宽质量规则
- 增加枚举值

### 破坏性变更（Major）
- 删除字段
- 修改字段类型
- 收紧质量规则
- 变更主键

破坏性变更需要：
1. 提前通知所有消费者
2. 提供迁移窗口期（例如 30 天）
3. 版本号递增（1.x.x → 2.0.0）

## 工具支持

- **datacontract-cli**: 验证契约语法
  ```bash
  pip install datacontract-cli
  datacontract test contracts/dp-customer-360.yaml
  ```

- **Airflow**: 运行时质量验证
- **OpenMetadata**: 元数据注册和血缘追踪
- **Backstage**: 开发者门户展示

## 最佳实践

1. ✅ **尽早定义契约** - 在开发数据产品之前
2. ✅ **版本化管理** - 使用语义化版本
3. ✅ **自动化验证** - 集成到 CI/CD
4. ✅ **消费者参与** - 让下游团队参与契约 review
5. ✅ **持续更新** - 契约应反映当前生产状态

## 参考资料

- [Data Contract Specification](https://datacontract.com/)
- [SodaCL Documentation](https://docs.soda.io/soda-cl/soda-cl-overview.html)
- [Data Mesh 书籍](https://www.oreilly.com/library/view/data-mesh/9781492092384/)
