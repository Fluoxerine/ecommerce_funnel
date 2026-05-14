-- 01: Ecommerce Funnel Data Warehouse — Create DB & Tables
-- Note: CSV column `Timestamp` maps to MySQL column `EventTime` by position

CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

DROP TABLE IF EXISTS user_behavior;
CREATE TABLE user_behavior (
    SessionID VARCHAR(255),
    UserID VARCHAR(255),
    EventTime TIMESTAMP,
    PageType VARCHAR(255),
    DeviceType VARCHAR(255),
    Country VARCHAR(255),
    ReferralSource VARCHAR(255),
    TimeOnPage_seconds INT,
    ItemsInCart INT,
    Purchased INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS funnel_wide;
CREATE TABLE funnel_wide (
    SessionID VARCHAR(255) PRIMARY KEY,
    UserID VARCHAR(255),
    DeviceType VARCHAR(255),
    Country VARCHAR(255),
    ReferralSource VARCHAR(255),
    step1_home TINYINT DEFAULT 0,
    step2_product TINYINT DEFAULT 0,
    step3_cart TINYINT DEFAULT 0,
    step4_checkout TINYINT DEFAULT 0,
    step5_confirm TINYINT DEFAULT 0,
    is_purchased TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT '01_setup_database: Tables created' AS status;
