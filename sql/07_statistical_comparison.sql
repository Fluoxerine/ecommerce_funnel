-- 07: Lost vs Converted Feature Comparison (SQL-side)

USE ecommerce;

-- 7.1 Cart abandoners vs converters
SELECT '=== Cart: Lost vs Converted ===' AS section;
SELECT 'Lost' AS user_type,
    ROUND(AVG(d.TimeOnPage_seconds), 1) AS avg_duration,
    ROUND(AVG(d.ItemsInCart), 1) AS avg_cart_items,
    COUNT(DISTINCT d.SessionID) AS session_count
FROM tmp_deduped d
JOIN funnel_wide f ON d.SessionID = f.SessionID
WHERE f.step3_cart = 1 AND f.step4_checkout = 0
UNION ALL
SELECT 'Converted',
    ROUND(AVG(d.TimeOnPage_seconds), 1),
    ROUND(AVG(d.ItemsInCart), 1),
    COUNT(DISTINCT d.SessionID)
FROM tmp_deduped d
JOIN funnel_wide f ON d.SessionID = f.SessionID
WHERE f.step3_cart = 1 AND f.step4_checkout = 1;

-- 7.2 Churn type distribution by channel
SELECT '=== Churn Type by Channel ===' AS section;
SELECT ReferralSource,
    SUM(CASE WHEN step2_product = 1 AND step3_cart = 0 THEN 1 ELSE 0 END) AS lost_at_browse,
    SUM(CASE WHEN step3_cart = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END) AS lost_at_cart,
    SUM(CASE WHEN step4_checkout = 1 AND step5_confirm = 0 THEN 1 ELSE 0 END) AS lost_at_checkout,
    COUNT(DISTINCT SessionID) AS total_sessions
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY total_sessions DESC;
