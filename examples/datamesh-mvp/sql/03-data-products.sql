-- ============================================
-- Data Mesh MVP: 数据产品 (Data Products)
-- 每个域发布自己的数据产品供其他域消费
-- ============================================

-- 在分析域创建数据产品视图
USE domain_analytics;

-- ============================================
-- 数据产品 1: 客户360视图 (Customer 360)
-- 所有者: 客户域
-- 消费者: 营销、销售、客服
-- ============================================
CREATE OR REPLACE VIEW dp_customer_360 AS
SELECT 
    c.customer_id,
    c.email,
    CONCAT(c.first_name, ' ', c.last_name) AS full_name,
    c.created_at AS customer_since,
    COALESCE(order_stats.total_orders, 0) AS total_orders,
    COALESCE(order_stats.total_spent, 0) AS total_spent,
    COALESCE(order_stats.avg_order_value, 0) AS avg_order_value,
    order_stats.last_order_date,
    CASE 
        WHEN order_stats.total_spent >= 500 THEN 'Gold'
        WHEN order_stats.total_spent >= 200 THEN 'Silver'
        ELSE 'Bronze'
    END AS customer_tier
FROM domain_customers.customers c
LEFT JOIN (
    SELECT 
        customer_id,
        COUNT(*) AS total_orders,
        SUM(total_amount) AS total_spent,
        AVG(total_amount) AS avg_order_value,
        MAX(order_date) AS last_order_date
    FROM domain_orders.orders
    WHERE status != 'cancelled'
    GROUP BY customer_id
) order_stats ON c.customer_id = order_stats.customer_id;

-- ============================================
-- 数据产品 2: 产品销售分析 (Product Sales Analytics)
-- 所有者: 产品域
-- 消费者: 库存管理、采购、营销
-- ============================================
CREATE OR REPLACE VIEW dp_product_sales AS
SELECT 
    p.product_id,
    p.name AS product_name,
    p.category,
    p.price AS current_price,
    COALESCE(sales.total_quantity_sold, 0) AS total_quantity_sold,
    COALESCE(sales.total_revenue, 0) AS total_revenue,
    COALESCE(sales.order_count, 0) AS order_count,
    sales.last_sold_date,
    CASE 
        WHEN sales.total_quantity_sold >= 10 THEN 'Hot'
        WHEN sales.total_quantity_sold >= 5 THEN 'Normal'
        WHEN sales.total_quantity_sold >= 1 THEN 'Slow'
        ELSE 'No Sales'
    END AS sales_velocity
FROM domain_products.products p
LEFT JOIN (
    SELECT 
        oi.product_id,
        SUM(oi.quantity) AS total_quantity_sold,
        SUM(oi.quantity * oi.unit_price) AS total_revenue,
        COUNT(DISTINCT oi.order_id) AS order_count,
        MAX(o.order_date) AS last_sold_date
    FROM domain_orders.order_items oi
    JOIN domain_orders.orders o ON oi.order_id = o.order_id
    WHERE o.status != 'cancelled'
    GROUP BY oi.product_id
) sales ON p.product_id = sales.product_id;

-- ============================================
-- 数据产品 3: 订单履行状态 (Order Fulfillment Status)
-- 所有者: 订单域
-- 消费者: 物流、客服、运营
-- ============================================
CREATE OR REPLACE VIEW dp_order_fulfillment AS
SELECT 
    o.order_id,
    o.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.email AS customer_email,
    o.order_date,
    o.status,
    o.total_amount,
    DATEDIFF(NOW(), o.order_date) AS days_since_order,
    CASE 
        WHEN o.status = 'pending' AND DATEDIFF(NOW(), o.order_date) > 3 THEN 'Delayed'
        WHEN o.status = 'processing' AND DATEDIFF(NOW(), o.order_date) > 5 THEN 'Delayed'
        ELSE 'On Track'
    END AS fulfillment_status,
    item_count.total_items
FROM domain_orders.orders o
JOIN domain_customers.customers c ON o.customer_id = c.customer_id
LEFT JOIN (
    SELECT order_id, SUM(quantity) AS total_items
    FROM domain_orders.order_items
    GROUP BY order_id
) item_count ON o.order_id = item_count.order_id;

-- ============================================
-- 数据产品 4: 业务 KPI 仪表板 (Business KPI Dashboard)
-- 所有者: 分析域
-- 消费者: 管理层、BI团队
-- ============================================
CREATE OR REPLACE VIEW dp_business_kpis AS
SELECT 
    DATE(NOW()) AS report_date,
    (SELECT COUNT(*) FROM domain_customers.customers) AS total_customers,
    (SELECT COUNT(*) FROM domain_products.products) AS total_products,
    (SELECT COUNT(*) FROM domain_orders.orders) AS total_orders,
    (SELECT SUM(total_amount) FROM domain_orders.orders WHERE status != 'cancelled') AS total_revenue,
    (SELECT AVG(total_amount) FROM domain_orders.orders WHERE status != 'cancelled') AS avg_order_value,
    (SELECT COUNT(*) FROM domain_orders.orders WHERE status = 'pending') AS pending_orders,
    (SELECT COUNT(*) FROM domain_orders.orders WHERE status = 'processing') AS processing_orders,
    (SELECT COUNT(*) FROM domain_orders.orders WHERE status = 'shipped') AS shipped_orders,
    (SELECT COUNT(*) FROM domain_orders.orders WHERE status = 'delivered') AS delivered_orders;

