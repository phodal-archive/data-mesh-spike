# Data Mesh Learning Environment

一个完整的 Data Mesh MVP 学习环境，包含数据目录、联邦查询、数据编排和可观测性。

## 快速开始

```bash
# 启动所有服务
./scripts/start.sh all

# 或分别启动
./scripts/start.sh stack1  # 数据平台核心
./scripts/start.sh stack2  # 可观测性和开发者门户
```

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Mesh MVP 架构                           │
├─────────────────────────────────────────────────────────────────┤
│  开发者门户层                                                     │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │  Backstage  │  │   Grafana   │                               │
│  │   :7007     │  │   :3000     │                               │
│  └─────────────┘  └─────────────┘                               │
├─────────────────────────────────────────────────────────────────┤
│  数据平台层                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │OpenMetadata │  │    Trino    │  │   Airflow   │              │
│  │   :8585     │  │   :8080     │  │   :8081     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  数据域层                                                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │
│  │ 客户域    │ │ 订单域    │ │ 产品域    │ │ 分析域    │        │
│  │customers  │ │ orders    │ │ products  │ │ analytics │        │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘        │
│                      MariaDB :3306                               │
├─────────────────────────────────────────────────────────────────┤
│  可观测性层                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Prometheus  │  │   Jaeger    │  │OTel Collector│             │
│  │   :9090     │  │  :16686     │  │   :4317     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## 服务端口

| 服务 | 端口 | 用途 | 凭证 |
|------|------|------|------|
| OpenMetadata | 8585 | 数据目录 | admin/admin |
| Trino | 8080 | 联邦查询 | - |
| Airflow | 8081 | 数据编排 | admin/admin |
| Backstage | 7007 | 开发者门户 | - |
| Grafana | 3000 | 可视化 | admin/admin |
| Prometheus | 9090 | 指标存储 | - |
| Jaeger | 16686 | 分布式追踪 | - |
| MariaDB | 3306 | 数据存储 | datamesh/datamesh123 |

## 数据域

- **domain_customers**: 客户主数据
- **domain_orders**: 订单交易数据
- **domain_products**: 产品目录数据
- **domain_analytics**: 聚合分析数据

## 跨域查询示例 (Trino)

```sql
-- 销售分析 - 跨域联邦查询
SELECT
  c.first_name || ' ' || c.last_name as customer_name,
  p.name as product_name,
  o.order_date,
  oi.quantity * oi.unit_price as line_total
FROM mariadb.domain_orders.orders o
JOIN mariadb.domain_orders.order_items oi ON o.order_id = oi.order_id
JOIN mariadb.domain_customers.customers c ON o.customer_id = c.customer_id
JOIN mariadb.domain_products.products p ON oi.product_id = p.product_id;
```