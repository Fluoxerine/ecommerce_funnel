-- 02: 数据加载 (via LOAD DATA INFILE)
-- 注：实际加载通过 Python pandas 到 MySQL，此脚本供手动导入参考

USE ecommerce;

-- user_events (2M rows)
LOAD DATA LOCAL INFILE 'data/events.csv'
INTO TABLE user_events
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(event_id, timestamp, customer_id, session_id, event_type,
 product_id, device_type, traffic_source, campaign_id,
 page_category, session_duration_sec, experiment_group);

-- transactions (103K rows)
LOAD DATA LOCAL INFILE 'data/transactions.csv'
INTO TABLE transactions
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(transaction_id, timestamp, customer_id, product_id,
 quantity, discount_applied, gross_revenue, campaign_id, refund_flag);

-- customers (100K rows)
LOAD DATA LOCAL INFILE 'data/customers.csv'
INTO TABLE customers
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(customer_id, signup_date, country, age, gender, loyalty_tier, acquisition_channel);

-- products (2K rows)
LOAD DATA LOCAL INFILE 'data/products.csv'
INTO TABLE products
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(product_id, category, brand, base_price, launch_date, is_premium);

-- campaigns (50 rows)
LOAD DATA LOCAL INFILE 'data/campaigns.csv'
INTO TABLE campaigns
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(campaign_id, channel, objective, start_date, end_date, target_segment, expected_uplift);
