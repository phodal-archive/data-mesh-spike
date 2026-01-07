-- ============================================
-- Data Mesh MVP: 扩展示例数据
-- 模拟真实的电商场景数据
-- ============================================

-- 添加更多客户数据
USE domain_customers;

INSERT IGNORE INTO customers (email, first_name, last_name) VALUES
    ('alice.zhang@example.com', 'Alice', 'Zhang'),
    ('charlie.brown@example.com', 'Charlie', 'Brown'),
    ('diana.prince@example.com', 'Diana', 'Prince'),
    ('edward.stark@example.com', 'Edward', 'Stark'),
    ('fiona.green@example.com', 'Fiona', 'Green'),
    ('george.miller@example.com', 'George', 'Miller'),
    ('helen.troy@example.com', 'Helen', 'Troy');

-- 添加更多产品数据
USE domain_products;

INSERT IGNORE INTO products (name, description, price, category) VALUES
    ('Wireless Mouse', 'Ergonomic wireless mouse', 49.99, 'Electronics'),
    ('Mechanical Keyboard', 'RGB mechanical keyboard', 129.99, 'Electronics'),
    ('USB-C Hub', '7-in-1 USB-C hub', 59.99, 'Electronics'),
    ('Jeans', 'Classic blue jeans', 79.99, 'Clothing'),
    ('Sneakers', 'Running sneakers', 119.99, 'Clothing'),
    ('Hoodie', 'Comfortable cotton hoodie', 59.99, 'Clothing'),
    ('Python Cookbook', 'Advanced Python recipes', 54.99, 'Books'),
    ('Clean Code', 'Software craftsmanship guide', 44.99, 'Books'),
    ('Domain-Driven Design', 'DDD principles and patterns', 64.99, 'Books');

-- 添加更多订单数据
USE domain_orders;

INSERT INTO orders (customer_id, status, total_amount, order_date) VALUES
    (4, 'delivered', 179.98, DATE_SUB(NOW(), INTERVAL 30 DAY)),
    (5, 'delivered', 249.97, DATE_SUB(NOW(), INTERVAL 25 DAY)),
    (6, 'shipped', 129.99, DATE_SUB(NOW(), INTERVAL 10 DAY)),
    (7, 'processing', 199.98, DATE_SUB(NOW(), INTERVAL 5 DAY)),
    (4, 'pending', 64.99, DATE_SUB(NOW(), INTERVAL 2 DAY)),
    (1, 'delivered', 109.98, DATE_SUB(NOW(), INTERVAL 45 DAY)),
    (2, 'delivered', 174.97, DATE_SUB(NOW(), INTERVAL 40 DAY)),
    (3, 'shipped', 59.99, DATE_SUB(NOW(), INTERVAL 7 DAY)),
    (8, 'processing', 299.97, DATE_SUB(NOW(), INTERVAL 3 DAY)),
    (9, 'pending', 89.98, DATE_SUB(NOW(), INTERVAL 1 DAY));

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (4, 4, 1, 49.99),   -- Wireless Mouse
    (4, 5, 1, 129.99),  -- Mechanical Keyboard
    (5, 6, 1, 59.99),   -- USB-C Hub
    (5, 7, 1, 79.99),   -- Jeans
    (5, 8, 1, 119.99),  -- Sneakers (价格调整)
    (6, 5, 1, 129.99),  -- Mechanical Keyboard
    (7, 8, 1, 119.99),  -- Sneakers
    (7, 9, 1, 59.99),   -- Hoodie
    (8, 12, 1, 64.99),  -- Domain-Driven Design
    (9, 4, 1, 49.99),   -- Wireless Mouse
    (9, 9, 1, 59.99),   -- Hoodie
    (10, 10, 1, 54.99), -- Python Cookbook
    (10, 11, 1, 44.99), -- Clean Code
    (10, 1, 1, 999.99), -- Laptop
    (11, 2, 1, 29.99),  -- T-Shirt
    (11, 9, 1, 59.99),  -- Hoodie
    (12, 6, 1, 59.99),  -- USB-C Hub
    (13, 1, 1, 999.99), -- Laptop
    (13, 4, 1, 49.99),  -- Wireless Mouse
    (13, 5, 1, 129.99); -- Mechanical Keyboard

