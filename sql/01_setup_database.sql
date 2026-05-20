-- 01: 数据库与表结构创建
-- 基于 E-Commerce Transactions + Clickstream 五表模型

CREATE DATABASE IF NOT EXISTS ecommerce
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ecommerce;

-- 用户行为事件表
DROP TABLE IF EXISTS user_events;
CREATE TABLE user_events (
    event_id BIGINT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    customer_id INT NOT NULL,
    session_id INT NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    product_id INT,
    device_type VARCHAR(20),
    traffic_source VARCHAR(50),
    campaign_id INT,
    page_category VARCHAR(20),
    session_duration_sec DOUBLE,
    experiment_group VARCHAR(20),
    INDEX idx_event_type (event_type),
    INDEX idx_session (session_id),
    INDEX idx_customer (customer_id),
    INDEX idx_traffic (traffic_source),
    INDEX idx_device (device_type),
    INDEX idx_experiment (experiment_group),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- 交易表
DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    transaction_id BIGINT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    customer_id INT NOT NULL,
    product_id INT,
    quantity INT NOT NULL DEFAULT 1,
    discount_applied DECIMAL(10, 4) DEFAULT 0,
    gross_revenue DECIMAL(12, 2) NOT NULL,
    campaign_id INT,
    refund_flag TINYINT DEFAULT 0,
    INDEX idx_customer (customer_id),
    INDEX idx_product (product_id),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB;

-- 用户画像表
DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    signup_date DATE,
    country VARCHAR(50),
    age INT,
    gender VARCHAR(10),
    loyalty_tier VARCHAR(20),
    acquisition_channel VARCHAR(30),
    INDEX idx_loyalty (loyalty_tier),
    INDEX idx_country (country),
    INDEX idx_acquisition (acquisition_channel)
) ENGINE=InnoDB;

-- 商品表
DROP TABLE IF EXISTS products;
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    category VARCHAR(50),
    brand VARCHAR(100),
    base_price DECIMAL(10, 2),
    launch_date DATE,
    is_premium TINYINT DEFAULT 0,
    INDEX idx_category (category),
    INDEX idx_brand (brand)
) ENGINE=InnoDB;

-- 广告活动表
DROP TABLE IF EXISTS campaigns;
CREATE TABLE campaigns (
    campaign_id INT PRIMARY KEY,
    channel VARCHAR(30),
    objective VARCHAR(30),
    start_date DATE,
    end_date DATE,
    target_segment VARCHAR(50),
    expected_uplift DECIMAL(6, 4)
) ENGINE=InnoDB;
