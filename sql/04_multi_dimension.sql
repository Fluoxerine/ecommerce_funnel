-- 04: 多维度漏斗拆解 — 渠道/设备/品类/用户分层

USE ecommerce;

-- ── 4.1 渠道维度 ────────────────────────────────────
SELECT '=== Funnel by Channel ===' AS section;
SELECT
    ue.traffic_source AS channel,
    COUNT(DISTINCT ue.session_id) AS total_sessions,
    COUNT(DISTINCT CASE WHEN ue.page_category = 'PDP'   THEN ue.session_id END) AS pdp_sessions,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'add_to_cart' THEN ue.session_id END) AS cart_sessions,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase'   THEN ue.session_id END) AS purchase_sessions,
    ROUND(COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END)
        / COUNT(DISTINCT ue.session_id) * 100, 2) AS conversion_rate
FROM user_events ue
GROUP BY ue.traffic_source
ORDER BY conversion_rate DESC;

-- ── 4.2 设备维度 ────────────────────────────────────
SELECT '=== Funnel by Device ===' AS section;
SELECT
    ue.device_type,
    COUNT(DISTINCT ue.session_id) AS total_sessions,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END) AS purchase_sessions,
    ROUND(COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END)
        / COUNT(DISTINCT ue.session_id) * 100, 2) AS conversion_rate
FROM user_events ue
GROUP BY ue.device_type
ORDER BY conversion_rate DESC;

-- ── 4.3 实验分组对比 ─────────────────────────────────
SELECT '=== A/B Test Groups ===' AS section;
SELECT
    ue.experiment_group,
    COUNT(DISTINCT ue.session_id) AS sessions,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END) AS purchases,
    ROUND(COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END)
        / COUNT(DISTINCT ue.session_id) * 100, 2) AS conversion_rate
FROM user_events ue
GROUP BY ue.experiment_group;

-- ── 4.4 国家维度 ────────────────────────────────────
SELECT '=== Conversion by Country ===' AS section;
SELECT
    c.country,
    COUNT(DISTINCT ue.session_id) AS sessions,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END) AS purchases,
    ROUND(COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END)
        / COUNT(DISTINCT ue.session_id) * 100, 2) AS conversion_rate
FROM user_events ue
JOIN customers c ON ue.customer_id = c.customer_id
GROUP BY c.country
HAVING sessions > 1000
ORDER BY conversion_rate DESC;

-- ── 4.5 忠诚度维度 ──────────────────────────────────
SELECT '=== Conversion by Loyalty Tier ===' AS section;
SELECT
    c.loyalty_tier,
    COUNT(DISTINCT ue.session_id) AS sessions,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END) AS purchases,
    ROUND(COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END)
        / COUNT(DISTINCT ue.session_id) * 100, 2) AS conversion_rate
FROM user_events ue
JOIN customers c ON ue.customer_id = c.customer_id
GROUP BY c.loyalty_tier
ORDER BY conversion_rate DESC;
