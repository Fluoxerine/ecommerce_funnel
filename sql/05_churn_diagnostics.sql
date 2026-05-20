-- 05: 流失诊断 — 各环节流失特征 + 渠道×流失交叉

USE ecommerce;

-- ── 5.1 各环节流失的用户行为特征对比 ──────────────────
SELECT '=== Churn Feature Comparison: PDP→Cart ===' AS section;

-- 流失组: 到过PDP但未加购
WITH lost_group AS (
    SELECT ue.* FROM user_events ue
    WHERE ue.session_id IN (
        SELECT session_id FROM user_events WHERE page_category = 'PDP'
    )
    AND ue.session_id NOT IN (
        SELECT session_id FROM user_events WHERE event_type = 'add_to_cart'
    )
),
conv_group AS (
    SELECT ue.* FROM user_events ue
    WHERE ue.session_id IN (
        SELECT session_id FROM user_events WHERE page_category = 'PDP'
    )
    AND ue.session_id IN (
        SELECT session_id FROM user_events WHERE event_type = 'add_to_cart'
    )
)
SELECT
    'Lost' AS user_type,
    ROUND(AVG(session_duration_sec), 1) AS avg_duration,
    COUNT(DISTINCT session_id) AS session_count
FROM lost_group
UNION ALL
SELECT
    'Converted',
    ROUND(AVG(session_duration_sec), 1),
    COUNT(DISTINCT session_id)
FROM conv_group;

-- ── 5.2 渠道×流失环节交叉矩阵 ────────────────────────
SELECT '=== Churn by Channel × Stage ===' AS section;

WITH session_funnel AS (
    SELECT session_id, traffic_source,
        MAX(CASE WHEN page_category = 'Home' THEN 1 ELSE 0 END) AS has_home,
        MAX(CASE WHEN page_category = 'PLP'  THEN 1 ELSE 0 END) AS has_plp,
        MAX(CASE WHEN page_category = 'PDP'  THEN 1 ELSE 0 END) AS has_pdp,
        MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN page_category = 'Checkout' THEN 1 ELSE 0 END) AS has_checkout
    FROM user_events GROUP BY session_id, traffic_source
)
SELECT
    traffic_source,
    SUM(CASE WHEN has_home = 1 AND has_plp = 0 THEN 1 ELSE 0 END) AS lost_home_to_plp,
    SUM(CASE WHEN has_plp  = 1 AND has_pdp = 0 THEN 1 ELSE 0 END) AS lost_plp_to_pdp,
    SUM(CASE WHEN has_pdp  = 1 AND has_cart = 0 THEN 1 ELSE 0 END) AS lost_pdp_to_cart,
    SUM(CASE WHEN has_cart = 1 AND has_checkout = 0 THEN 1 ELSE 0 END) AS lost_cart_to_checkout,
    COUNT(*) AS total_sessions
FROM session_funnel
GROUP BY traffic_source
ORDER BY total_sessions DESC;

-- ── 5.3 退款分析 ────────────────────────────────────
SELECT '=== Refund Analysis ===' AS section;

SELECT
    p.category,
    COUNT(DISTINCT t.transaction_id) AS total_txn,
    SUM(t.refund_flag) AS refund_count,
    ROUND(SUM(t.refund_flag) / COUNT(DISTINCT t.transaction_id) * 100, 2) AS refund_rate,
    ROUND(AVG(t.gross_revenue), 2) AS avg_order_value
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.category
ORDER BY refund_rate DESC;
