# Data Mesh Learning Environment

一个完整的 Data Mesh MVP 学习环境，包含数据目录、联邦查询、数据编排和可观测性。

## 快速开始

```bash
# 启动所有服务
./scripts/start.sh all

# 或分别启动
./scripts/start.sh stack1  # 数据平台核心
./scripts/start.sh stack2  # 可观测性和开发者门户

# 对于 Colima 用户 (macOS ARM)：需要启动端口转发
./scripts/port-forward.sh
```

## macOS ARM (Apple Silicon) 注意事项

如果你使用的是 Colima 而不是 Docker Desktop，需要手动设置端口转发才能从 localhost 访问服务：

```bash
# 启动端口转发
./scripts/port-forward.sh

# 停止端口转发
pkill -f 'ssh.*colima.*-L'
```

## 架构概览

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Data Mesh MVP 架构                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│  消费层 (BI & 开发者门户 & 知识图谱)                                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────────┐            │
│  │ Backstage │  │  Grafana  │  │ Superset  │  │     Neo4j       │            │
│  │   :7007   │  │   :3000   │  │   :8089   │  │     :7474       │            │
│  │ 服务目录  │  │ 运维监控  │  │ 业务BI    │  │ 领域知识图谱    │            │
│  └───────────┘  └───────────┘  └───────────┘  └─────────────────┘            │
├──────────────────────────────────────────────────────────────────────────────┤
│  数据平台层 (自服务基础设施)                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                           │
│  │OpenMetadata │  │    Trino    │  │   Airflow   │                           │
│  │   :8585     │  │   :8080     │  │   :8081     │                           │
│  │ 数据目录    │◄─┤ 联邦查询    │──►│ 数据编排    │                           │
│  └──────┬──────┘  └──────▲──────┘  └──────┬──────┘                           │
│         │                │                │                                  │
│         └────────────────┼────────────────┘                                  │
│                    元数据 Lineage                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│  数据产品层 (域即产品)                                                        │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐                    │
│  │ 客户域    │ │ 订单域    │ │ 产品域    │ │ 分析域    │                    │
│  │customers  │ │ orders    │ │ products  │ │ analytics │                    │
│  │           │ │           │ │           │ │ (dp_*)    │                    │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘                    │
│                      MariaDB :3306                                           │
├──────────────────────────────────────────────────────────────────────────────┤
│  可观测性层                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                           │
│  │ Prometheus  │  │   Jaeger    │  │OTel Collector│                          │
│  │   :9090     │  │  :16686     │  │   :4317     │                           │
│  └─────────────┘  └─────────────┘  └─────────────┘                           │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 服务端口

| 服务           | 端口       | 用途        | 凭证                    |
|--------------|----------|-----------|-----------------------|
| OpenMetadata | 8585     | 数据目录      | admin/admin           |
| Trino        | 8080     | 联邦查询      | -                     |
| Airflow      | 8081     | 数据编排      | admin/admin           |
| **Superset** | **8089** | **BI 报表** | **admin/admin**       |
| **Neo4j**    | **7474** | **知识图谱**  | **neo4j/datamesh123** |
| Backstage    | 7007     | 开发者门户     | -                     |
| Grafana      | 3000     | 运维监控      | admin/admin           |
| Prometheus   | 9090     | 指标存储      | -                     |
| Jaeger       | 16686    | 分布式追踪     | -                     |
| MariaDB      | 3306     | 数据存储      | datamesh/datamesh123  |

## 数据域

- **domain_customers**: 客户主数据
- **domain_orders**: 订单交易数据
- **domain_products**: 产品目录数据
- **domain_analytics**: 聚合分析数据
- **knowledge-graph**: Data Mesh 架构元数据与概念关系 (Neo4j)

## OpenMetadata 元数据采集

启动服务后，运行以下命令采集 MariaDB 的元数据到 OpenMetadata：

```bash
./scripts/run-ingestion.sh
```

这将自动：

- 扫描所有数据域 (domain_customers, domain_orders, domain_products, domain_analytics)
- 将表结构、列信息导入 OpenMetadata
- 可在 http://localhost:8585 查看数据目录

## 数据质量验证

Data Mesh MVP 包含完整的数据质量检查管道，在每次数据刷新前验证质量：

```bash
# 查看最新的质量检查结果
./scripts/view-quality-logs.sh
```

质量规则包括：

- **完整性检查**: 主键非空、参照完整性、业务规则
- **一致性检查**: 跨表金额匹配、外键有效性
- **新鲜度检查**: 数据更新时效性

详细演示文档：[docs/task-c-data-quality-validation.md](docs/task-c-data-quality-validation.md)

## BI 报表 (Superset)

启动服务后，可以通过 Superset 创建业务报表：

1. 访问 http://localhost:8089 (admin/admin)
2. 添加 Trino 数据源：
    - Settings → Database Connections → + Database → Trino
    - SQLAlchemy URI: `trino://trino@datamesh-trino:8080/mariadb`
3. 创建数据集和图表，例如：
    - 客户 360 视图: `SELECT * FROM domain_analytics.dp_customer_360`
    - 产品销售: `SELECT * FROM domain_analytics.dp_product_sales`
    - 业务 KPI: `SELECT * FROM domain_analytics.dp_business_kpis`

## 领域知识图谱 (Neo4j)

Neo4j 用于可视化展示 Data Mesh 中的概念关系、领域之间的依赖：

1. 访问 http://localhost:7474 (neo4j/datamesh123)
2. 初始化知识图谱后，可以执行以下查询：

```cypher
// 查看 Data Mesh 核心概念
MATCH (dm:Concept {name: 'Data Mesh'})-[:CONSISTS_OF]->(c:Concept)
RETURN dm, c

// 查看领域与数据产品的关系
MATCH (d:Domain)-[:OWNS]->(dp:DataProduct)
RETURN d, dp

// 查看完整的领域依赖图
MATCH (d1:Domain)-[r:DEPENDS_ON|AGGREGATES]->(d2:Domain)
RETURN d1, r, d2

// 查看平台组件与领域的交互
MATCH (p:Platform)-[r]->(d:Domain)
RETURN p, r, d

// 查看团队与领域的所有权关系
MATCH (t:Team)-[:OWNS]->(d:Domain)
RETURN t, d
```

## 跨域查询示例 (Trino)

```sql
-- 销售分析 - 跨域联邦查询
SELECT c.first_name || ' ' || c.last_name as customer_name,
       p.name                             as product_name,
       o.order_date,
       oi.quantity * oi.unit_price        as line_total
FROM mariadb.domain_orders.orders o
         JOIN mariadb.domain_orders.order_items oi ON o.order_id = oi.order_id
         JOIN mariadb.domain_customers.customers c ON o.customer_id = c.customer_id
         JOIN mariadb.domain_products.products p ON oi.product_id = p.product_id;
```

## 数据产品 (Data Products)

数据产品定义在不同域中，可通过 Trino/Superset 查询：

| 数据产品                       | 描述                  | 所有者       | 访问方式                       |
|----------------------------|---------------------|-----------|----------------------------|
| dp_customer_360            | 客户全景视图              | 客户域       | SQL / Superset             |
| dp_product_sales           | 产品销售分析              | 分析域       | SQL / Superset             |
| dp_order_fulfillment       | 订单履行状态              | 订单域       | SQL / Superset             |
| dp_business_kpis           | 业务 KPI 仪表板          | 分析域       | SQL / Superset             |
| **Domain Knowledge Graph** | **Data Mesh 架构元数据** | **知识图谱域** | **Neo4j Browser / Cypher** |