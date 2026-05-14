-- 05: Multi-Dimension Analysis — Channel, Device, Country

USE ecommerce;

-- 5.1 Channel conversion
SELECT '=== Channel Conversion ===' AS section;
SELECT ReferralSource,
    COUNT(DISTINCT SessionID) AS total_sessions,
    SUM(is_purchased) AS converted,
    ROUND(SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID), 2) AS conversion_rate_pct,
    ROUND(COUNT(DISTINCT SessionID) * 100.0 /
        (SELECT COUNT(DISTINCT SessionID) FROM funnel_wide), 2) AS traffic_share_pct
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY conversion_rate_pct DESC;

-- 5.2 TRUE highest churn: Browse->Cart by channel
SELECT '=== Highest Churn (Browse->Cart) by Channel ===' AS section;
SELECT ReferralSource,
    SUM(step2_product) AS product_viewed,
    SUM(step3_cart) AS cart_added,
    ROUND(SUM(step3_cart) * 100.0 / SUM(step2_product), 2) AS product_to_cart_rate_pct
FROM funnel_wide
WHERE step2_product = 1
GROUP BY ReferralSource
ORDER BY product_to_cart_rate_pct DESC;

-- 5.3 Device conversion
SELECT '=== Device Conversion ===' AS section;
SELECT DeviceType,
    COUNT(DISTINCT SessionID) AS total_sessions,
    SUM(is_purchased) AS converted,
    ROUND(SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID), 2) AS conversion_rate_pct,
    ROUND(COUNT(DISTINCT SessionID) * 100.0 /
        (SELECT COUNT(DISTINCT SessionID) FROM funnel_wide), 2) AS traffic_share_pct
FROM funnel_wide
GROUP BY DeviceType
ORDER BY conversion_rate_pct DESC;

-- 5.4 Country conversion
SELECT '=== Country Conversion ===' AS section;
SELECT Country,
    COUNT(DISTINCT SessionID) AS total_sessions,
    SUM(is_purchased) AS converted,
    ROUND(SUM(is_purchased) * 100.0 / COUNT(DISTINCT SessionID), 2) AS conversion_rate_pct
FROM funnel_wide
GROUP BY Country
ORDER BY conversion_rate_pct DESC;
