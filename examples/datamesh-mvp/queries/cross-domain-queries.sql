-- ============================================
-- Data Mesh MVP: Trino 跨域查询示例
-- 使用 Trino 联邦查询跨多个数据域
-- ============================================

-- ============================================
-- 查询 1: 查看所有数据域中的表
-- ============================================
SHOW SCHEMAS FROM mariadb;

-- 查看客户域的表
SHOW TABLES FROM mariadb.domain_customers;

-- 查看订单域的表
SHOW TABLES FROM mariadb.domain_orders;

-- 查看产品域的表
SHOW TABLES FROM mariadb.domain_products;

-- ============================================
-- 查询 2: 跨域联合查询 - 客户订单详情
-- 联合客户域、订单域、产品域的数据
-- ============================================
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email,
    o.order_id,
    o.order_date,
    o.status,
    p.name AS product_name,
    p.category,
    oi.quantity,
    oi.unit_price,
    oi.quantity * oi.unit_price AS line_total
FROM mariadb.domain_customers.customers c
JOIN mariadb.domain_orders.orders o ON c.customer_id = o.customer_id
JOIN mariadb.domain_orders.order_items oi ON o.order_id = oi.order_id
JOIN mariadb.domain_products.products p ON oi.product_id = p.product_id
ORDER BY o.order_date DESC
LIMIT 20;

-- ============================================
-- 查询 3: 客户消费排行榜
-- ============================================
SELECT 
    c.customer_id,
    c.first_name || ' ' || c.last_name AS customer_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.total_amount) AS total_spent,
    AVG(o.total_amount) AS avg_order_value
FROM mariadb.domain_customers.customers c
LEFT JOIN mariadb.domain_orders.orders o ON c.customer_id = o.customer_id
WHERE o.status != 'cancelled' OR o.status IS NULL
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY total_spent DESC NULLS LAST;

-- ============================================
-- 查询 4: 产品销售分析
-- ============================================
SELECT 
    p.category,
    p.name AS product_name,
    COUNT(oi.item_id) AS times_ordered,
    SUM(oi.quantity) AS total_quantity,
    SUM(oi.quantity * oi.unit_price) AS total_revenue
FROM mariadb.domain_products.products p
LEFT JOIN mariadb.domain_orders.order_items oi ON p.product_id = oi.product_id
LEFT JOIN mariadb.domain_orders.orders o ON oi.order_id = o.order_id AND o.status != 'cancelled'
GROUP BY p.category, p.name
ORDER BY total_revenue DESC NULLS LAST;

-- ============================================
-- 查询 5: 订单状态分布
-- ============================================
SELECT 
    status,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_value,
    AVG(total_amount) AS avg_value
FROM mariadb.domain_orders.orders
GROUP BY status
ORDER BY order_count DESC;

-- ============================================
-- 查询 6: 使用数据产品视图
-- ============================================
-- 客户360视图
SELECT * FROM mariadb.domain_analytics.dp_customer_360
ORDER BY total_spent DESC;

-- 产品销售分析
SELECT * FROM mariadb.domain_analytics.dp_product_sales
ORDER BY total_revenue DESC;

-- 订单履行状态
SELECT * FROM mariadb.domain_analytics.dp_order_fulfillment
WHERE fulfillment_status = 'Delayed';

-- 业务KPI
SELECT * FROM mariadb.domain_analytics.dp_business_kpis;

-- ============================================
-- 查询 7: 高级分析 - 客户购买行为
-- ============================================
WITH customer_categories AS (
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        p.category,
        SUM(oi.quantity * oi.unit_price) AS category_spend
    FROM mariadb.domain_customers.customers c
    JOIN mariadb.domain_orders.orders o ON c.customer_id = o.customer_id
    JOIN mariadb.domain_orders.order_items oi ON o.order_id = oi.order_id
    JOIN mariadb.domain_products.products p ON oi.product_id = p.product_id
    WHERE o.status != 'cancelled'
    GROUP BY c.customer_id, c.first_name, c.last_name, p.category
)
SELECT 
    customer_name,
    category,
    category_spend,
    RANK() OVER (PARTITION BY customer_id ORDER BY category_spend DESC) AS category_rank
FROM customer_categories
ORDER BY customer_name, category_rank;

