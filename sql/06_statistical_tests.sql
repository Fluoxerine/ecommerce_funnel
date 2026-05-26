-- 06: 统计检验 — 渠道/设备卡方检验 + 品类 ANOVA 近似

USE ecommerce;

-- ── 6.1 卡方: 渠道×转化 (会话级) ──────────────────────────────
-- 先按 session 聚合判断是否购买，再用会话级列联表做卡方检验
-- 保证每个观测单位（session）独立，满足卡方独立性假设
SELECT '=== Chi-Square: Channel × Conversion (session-level) ===' AS section;

WITH session_purchase AS (
    SELECT
        session_id,
        traffic_source,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
    FROM user_events
    WHERE event_type IN ('view', 'click', 'add_to_cart', 'purchase')
    GROUP BY session_id, traffic_source
),
contingency AS (
    SELECT
        traffic_source,
        SUM(has_purchase) AS converted,
        COUNT(*) - SUM(has_purchase) AS not_converted
    FROM session_purchase
    GROUP BY traffic_source
)
SELECT
    traffic_source,
    converted,
    not_converted,
    ROUND(converted / (converted + not_converted) * 100, 2) AS conversion_rate
FROM contingency
ORDER BY conversion_rate DESC;

-- ── 6.2 卡方: 设备×转化 (会话级) ──────────────────────────────
SELECT '=== Chi-Square: Device × Conversion (session-level) ===' AS section;

WITH session_purchase AS (
    SELECT
        session_id,
        device_type,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
    FROM user_events
    WHERE event_type IN ('view', 'click', 'add_to_cart', 'purchase')
    GROUP BY session_id, device_type
),
contingency AS (
    SELECT
        device_type,
        SUM(has_purchase) AS converted,
        COUNT(*) - SUM(has_purchase) AS not_converted
    FROM session_purchase
    GROUP BY device_type
)
SELECT
    device_type,
    converted,
    not_converted,
    ROUND(converted / (converted + not_converted) * 100, 2) AS conversion_rate
FROM contingency
ORDER BY conversion_rate DESC;

-- ── 6.3 品类×时段转化率 ──────────────────────────────
SELECT '=== Category × Time of Day ===' AS section;

SELECT
    p.category,
    HOUR(ue.timestamp) AS event_hour,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END) AS purchases,
    COUNT(DISTINCT ue.session_id) AS sessions,
    ROUND(COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END)
        / COUNT(DISTINCT ue.session_id) * 100, 2) AS conversion_rate
FROM user_events ue
JOIN products p ON ue.product_id = p.product_id
WHERE ue.product_id IS NOT NULL
GROUP BY p.category, HOUR(ue.timestamp)
HAVING sessions > 50
ORDER BY conversion_rate DESC
LIMIT 20;
