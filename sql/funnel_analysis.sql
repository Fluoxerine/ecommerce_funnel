-- 电商用户行为漏斗分析SQL脚本
-- 表名：user_behavior，字段与数据集完全一致
-- 融合基础清洗 + 漏斗专属清洗 + 多维度分析，与Python分析逻辑完全一致



-- 创建数据库,导入数据等前置操作
show DATABASES;
CREATE DATABASE if not EXISTS ecommerce;
use ecommerce;
select database();


-- ==============================================
-- 原始数据表（CSV导入，无主键约束）
-- ==============================================
CREATE TABLE IF NOT EXISTS user_behavior (
    SessionID varchar(255),
    UserID varchar(255),
    EventTime timestamp,
    PageType varchar(255),
    DeviceType varchar(255),
    Country varchar(255),
    ReferralSource varchar(255),
    TimeOnPage_seconds int,
    ItemsInCart int,
    Purchased int
);

SET GLOBAL local_infile = ON; # 允许LOAD DATA INFILE导入数据

LOAD DATA INFILE '/var/lib/mysql/upload/customer_journey.csv' # 已经上传到MySQL服务器的指定目录
INTO TABLE user_behavior
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;


-- ==============================================
-- 1. 基础脏数据清洗（保障数据准确性）
-- ==============================================
-- 验证：查看Purchased=1且ItemsInCart=0的记录分布在哪些页面
SELECT 
    LOWER(PageType) AS page_type,
    COUNT(*) AS record_count,
    COUNT(DISTINCT SessionID) AS session_count
FROM user_behavior
WHERE 
    Purchased = 1 
    AND ItemsInCart = 0
    AND SessionID IS NOT NULL
GROUP BY LOWER(PageType)
ORDER BY record_count DESC;
# Purchased 是会话级别的最终状态，ItemsInCart 是页面级别的状态

-- 检查会话中所有页面的ItemsInCart都为0，但最终Purchased为1的情况(即直接购买)
WITH session_items AS (
    SELECT 
        SessionID,
        MAX(ItemsInCart) AS max_items_in_cart,
        MAX(Purchased) AS is_purchased
    FROM user_behavior
    WHERE SessionID IS NOT NULL
    GROUP BY SessionID
)
SELECT 
    SessionID,
    max_items_in_cart,
    is_purchased
FROM session_items
WHERE 
    is_purchased = 1 
    AND max_items_in_cart = 0;
# 结果为空,说明没有会话中所有页面的ItemsInCart都为0，但最终Purchased为1的情况(直接购买)，数据质量较好


-- ==============================================
-- 2. 漏斗专属清洗（关键！保证漏斗真实有效）
-- ==============================================

-- 2.1 & 2.2 创建去重后的临时表
DROP TEMPORARY TABLE IF EXISTS tmp_deduped;
CREATE TEMPORARY TABLE tmp_deduped AS
WITH clean_base AS (
    SELECT DISTINCT
        SessionID,
        UserID,
        EventTime,
        LOWER(PageType) AS PageType,
        DeviceType,
        COALESCE(Country, 'Unknown') AS Country,
        COALESCE(ReferralSource, 'Unknown') AS ReferralSource,
        COALESCE(TimeOnPage_seconds, 0) AS TimeOnPage_seconds,
        COALESCE(ItemsInCart, 0) AS ItemsInCart,
        COALESCE(Purchased, 0) AS Purchased
    FROM user_behavior
    WHERE 
        SessionID IS NOT NULL
        AND UserID IS NOT NULL
        AND EventTime IS NOT NULL
        AND PageType IS NOT NULL
        AND EventTime < NOW()
        AND TimeOnPage_seconds BETWEEN 0 AND 86400
        AND ItemsInCart >= 0
        AND Purchased IN (0, 1)
),
session_dedup AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (PARTITION BY SessionID, PageType ORDER BY EventTime) AS rn
    FROM clean_base
)
SELECT * FROM session_dedup WHERE rn = 1;

-- 2.2 无效会话过滤：总停留时长>=5秒
DROP TEMPORARY TABLE IF EXISTS tmp_valid_sessions;
CREATE TEMPORARY TABLE tmp_valid_sessions AS
SELECT SessionID
FROM tmp_deduped
GROUP BY SessionID
HAVING SUM(TimeOnPage_seconds) >= 5;

-- 2.3 提取会话核心属性（取众数/最频繁出现的值）
DROP TEMPORARY TABLE IF EXISTS tmp_top_attributes;
CREATE TEMPORARY TABLE tmp_top_attributes AS
WITH session_attributes AS (
    SELECT 
        SessionID,
        DeviceType,
        Country,
        ReferralSource,
        UserID,
        ROW_NUMBER() OVER (PARTITION BY SessionID ORDER BY COUNT(*) DESC) as rn
    FROM tmp_deduped
    GROUP BY SessionID, DeviceType, Country, ReferralSource, UserID
)
SELECT * FROM session_attributes WHERE rn = 1;

-- 2.4 漏斗宽表（适配多维度分析）
DROP TABLE IF EXISTS funnel_wide;
CREATE TABLE funnel_wide AS
SELECT
    d.SessionID,
    ta.UserID,
    ta.DeviceType,
    ta.Country,
    ta.ReferralSource,
    MAX(CASE WHEN d.PageType = 'home' THEN 1 ELSE 0 END) AS step1_home,
    MAX(CASE WHEN d.PageType = 'product_page' THEN 1 ELSE 0 END) AS step2_product,
    MAX(CASE WHEN d.PageType = 'cart' THEN 1 ELSE 0 END) AS step3_cart,
    MAX(CASE WHEN d.PageType = 'checkout' THEN 1 ELSE 0 END) AS step4_checkout,
    MAX(CASE WHEN d.PageType = 'confirmation' THEN 1 ELSE 0 END) AS step5_confirm,
    MAX(d.Purchased) AS is_purchased
FROM tmp_deduped d
JOIN tmp_top_attributes ta ON d.SessionID = ta.SessionID
WHERE d.SessionID IN (SELECT SessionID FROM tmp_valid_sessions)
GROUP BY d.SessionID, ta.UserID, ta.DeviceType, ta.Country, ta.ReferralSource;

-- ==============================================
-- 3. 核心分析：全链路转化漏斗（会话维度）
-- ==============================================
WITH funnel_steps AS (
    SELECT
        SUM(step1_home) AS s1,
        SUM(step2_product) AS s2,
        SUM(step3_cart) AS s3,
        SUM(step4_checkout) AS s4,
        SUM(step5_confirm) AS s5
    FROM funnel_wide
)
SELECT '1.访问首页' AS stage, s1 AS session_count, 100.00 AS conversion_rate FROM funnel_steps
UNION ALL
SELECT '2.浏览商品', s2, ROUND(s2 * 100.0 / NULLIF(s1, 0), 2) FROM funnel_steps
UNION ALL
SELECT '3.加入购物车', s3, ROUND(s3 * 100.0 / NULLIF(s2, 0), 2) FROM funnel_steps
UNION ALL
SELECT '4.提交订单', s4, ROUND(s4 * 100.0 / NULLIF(s3, 0), 2) FROM funnel_steps
UNION ALL
SELECT '5.支付成功', s5, ROUND(s5 * 100.0 / NULLIF(s4, 0), 2) FROM funnel_steps;

-- ==============================================
-- 4. 各流量来源渠道转化率统计（渠道运营核心）
-- ==============================================
SELECT
    ReferralSource,
    COUNT(DISTINCT SessionID) AS total_sessions,
    SUM(is_purchased) AS converted_sessions,
    ROUND(
        SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID),
        2
    ) AS conversion_rate,
    ROUND(
        COUNT(DISTINCT SessionID) * 100.0 / (SELECT COUNT(DISTINCT SessionID) FROM funnel_wide),
        2
    ) AS traffic_ratio
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY conversion_rate DESC;

-- ==============================================
-- 5. 核心流失环节：购物车→提交订单 分渠道转化率(核心流失环节是转化率显著低于其他环节,是最低的环节,2.浏览商品→加入购物车转化率最低,后面重做该部分)
-- ==============================================
SELECT
    ReferralSource,
    COUNT(DISTINCT SessionID) AS cart_session_count,
    SUM(CASE WHEN step4_checkout = 1 THEN 1 ELSE 0 END) AS checkout_session_count,
    ROUND(
        SUM(CASE WHEN step4_checkout = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT SessionID),
        2
    ) AS cart_to_checkout_rate
FROM funnel_wide
WHERE step3_cart = 1
GROUP BY ReferralSource
ORDER BY cart_to_checkout_rate DESC;

-- ==============================================
-- 6. 不同设备类型转化率分析（端侧优化）
-- ==============================================
SELECT
    DeviceType,
    COUNT(DISTINCT SessionID) AS total_sessions,
    SUM(is_purchased) AS converted_sessions,
    ROUND(
        SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID),
        2
    ) AS conversion_rate,
    ROUND(
        COUNT(DISTINCT SessionID) * 100.0 / (SELECT COUNT(DISTINCT SessionID) FROM funnel_wide),
        2
    ) AS traffic_ratio
FROM funnel_wide
GROUP BY DeviceType
ORDER BY conversion_rate DESC;

-- ==============================================
-- 7. 购物车商品数与转化率关系（加购流失分析）
-- ==============================================
WITH session_cart AS (
    SELECT
        SessionID,
        MAX(ItemsInCart) AS max_items_in_cart,
        is_purchased
    FROM (
        SELECT d.SessionID, d.ItemsInCart, fw.is_purchased
        FROM tmp_deduped d
        JOIN funnel_wide fw ON d.SessionID = fw.SessionID
    ) t
    GROUP BY SessionID, is_purchased
)
SELECT
    CASE
        WHEN max_items_in_cart = 0 THEN '0件'
        WHEN max_items_in_cart BETWEEN 1 AND 2 THEN '1-2件'
        WHEN max_items_in_cart BETWEEN 3 AND 5 THEN '3-5件'
        WHEN max_items_in_cart BETWEEN 6 AND 10 THEN '6-10件'
        ELSE '10件+'
    END AS cart_bucket,
    COUNT(DISTINCT SessionID) AS session_count,
    SUM(is_purchased) AS converted_count,
    ROUND(SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID), 2) AS conversion_rate
FROM session_cart
GROUP BY
    CASE
        WHEN max_items_in_cart = 0 THEN '0件'
        WHEN max_items_in_cart BETWEEN 1 AND 2 THEN '1-2件'
        WHEN max_items_in_cart BETWEEN 3 AND 5 THEN '3-5件'
        WHEN max_items_in_cart BETWEEN 6 AND 10 THEN '6-10件'
        ELSE '10件+'
    END
ORDER BY
    CASE
        WHEN max_items_in_cart = 0 THEN '0件'
        WHEN max_items_in_cart BETWEEN 1 AND 2 THEN '1-2件'
        WHEN max_items_in_cart BETWEEN 3 AND 5 THEN '3-5件'
        WHEN max_items_in_cart BETWEEN 6 AND 10 THEN '6-10件'
        ELSE '10件+'
    END;