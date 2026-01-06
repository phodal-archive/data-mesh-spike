-- Initialize sample databases for Data Mesh learning
-- This script runs automatically when MariaDB container starts

-- Create sample domain databases
CREATE DATABASE IF NOT EXISTS domain_customers;
CREATE DATABASE IF NOT EXISTS domain_orders;
CREATE DATABASE IF NOT EXISTS domain_products;
CREATE DATABASE IF NOT EXISTS domain_analytics;

-- Grant permissions to datamesh user
GRANT ALL PRIVILEGES ON domain_customers.* TO 'datamesh'@'%';
GRANT ALL PRIVILEGES ON domain_orders.* TO 'datamesh'@'%';
GRANT ALL PRIVILEGES ON domain_products.* TO 'datamesh'@'%';
GRANT ALL PRIVILEGES ON domain_analytics.* TO 'datamesh'@'%';

FLUSH PRIVILEGES;

-- Create sample tables in domain_customers
USE domain_customers;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create sample tables in domain_products
USE domain_products;

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_category_id INT,
    FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
);

-- Create sample tables in domain_orders
USE domain_orders;

CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    total_amount DECIMAL(10, 2)
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- Insert sample data
USE domain_customers;
INSERT INTO customers (email, first_name, last_name) VALUES
    ('john.doe@example.com', 'John', 'Doe'),
    ('jane.smith@example.com', 'Jane', 'Smith'),
    ('bob.wilson@example.com', 'Bob', 'Wilson');

USE domain_products;
INSERT INTO categories (name, parent_category_id) VALUES
    ('Electronics', NULL),
    ('Clothing', NULL),
    ('Books', NULL);

INSERT INTO products (name, description, price, category) VALUES
    ('Laptop', 'High-performance laptop', 999.99, 'Electronics'),
    ('T-Shirt', 'Cotton t-shirt', 29.99, 'Clothing'),
    ('Data Mesh Book', 'Learn about Data Mesh architecture', 49.99, 'Books');

USE domain_orders;
INSERT INTO orders (customer_id, status, total_amount) VALUES
    (1, 'delivered', 999.99),
    (2, 'processing', 79.98),
    (3, 'pending', 49.99);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 999.99),
    (2, 2, 2, 29.99),
    (2, 3, 1, 49.99),
    (3, 3, 1, 49.99);

