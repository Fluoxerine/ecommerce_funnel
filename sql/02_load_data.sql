-- 02: Data Import — CSV to MySQL
-- Prerequisite: customer_journey.csv copied to container /var/lib/mysql/upload/

USE ecommerce;

SET GLOBAL local_infile = ON;

LOAD DATA INFILE '/var/lib/mysql/upload/customer_journey.csv'
INTO TABLE user_behavior
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

SELECT COUNT(*) AS total_records FROM user_behavior;
SELECT COUNT(DISTINCT SessionID) AS total_sessions FROM user_behavior;
SELECT '02_load_data: Import complete' AS status;
