# Data Products SQL

## 单一来源 (Single Source of Truth)

数据产品视图（`dp_*`）的定义位于：

```
airflow/dags/sql/03-data-products.sql
```

本目录不再包含重复的 SQL 文件。所有数据产品初始化和刷新都引用上述统一位置。

## 使用方式

```bash
# 初始化/刷新数据产品
./scripts/init-data-products.sh

# 或在 Airflow DAG 中自动刷新
# datamesh_mvp_pipeline -> refresh_data_products task
```

## 数据产品清单

| 数据产品 | 视图名称 | 所有者 | 消费者 |
|---------|---------|-------|--------|
| 客户360视图 | `dp_customer_360` | 客户域 | 营销、销售、客服 |
| 产品销售分析 | `dp_product_sales` | 产品域 | 库存管理、采购、营销 |
| 订单履行状态 | `dp_order_fulfillment` | 订单域 | 物流、客服、运营 |
| 业务KPI仪表板 | `dp_business_kpis` | 分析域 | 管理层、BI团队 |
