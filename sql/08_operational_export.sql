-- 08: 运营导出 — Power BI 数据源 + 监控指标

USE ecommerce;

-- ── 8.1 漏斗宽表导出 ─────────────────────────────────
SELECT '=== Funnel Wide Export ===' AS section;

WITH session_funnel AS (
    SELECT
        ue.session_id,
        MAX(ue.customer_id) AS customer_id,
        MAX(ue.traffic_source) AS traffic_source,
        MAX(ue.device_type) AS device_type,
        MAX(ue.experiment_group) AS experiment_group,
        MAX(ue.campaign_id) AS campaign_id,
        MAX(CASE WHEN ue.page_category = 'Home' THEN 1 ELSE 0 END) AS step1_home,
        MAX(CASE WHEN ue.page_category = 'PLP'  THEN 1 ELSE 0 END) AS step2_plp,
        MAX(CASE WHEN ue.page_category = 'PDP'  THEN 1 ELSE 0 END) AS step3_pdp,
        MAX(CASE WHEN ue.page_category = 'Cart' THEN 1 ELSE 0 END) AS step4_cart,
        MAX(CASE WHEN ue.page_category = 'Checkout' THEN 1 ELSE 0 END) AS step5_checkout,
        MAX(CASE WHEN ue.event_type = 'purchase' THEN 1 ELSE 0 END) AS is_purchased
    FROM user_events ue
    GROUP BY ue.session_id
)
SELECT
    sf.*,
    c.country,
    c.loyalty_tier,
    c.acquisition_channel,
    c.age
FROM session_funnel sf
JOIN customers c ON sf.customer_id = c.customer_id
LIMIT 1000;

-- ── 8.2 监控 KPI ──────────────────────────────────
SELECT '=== Monitoring KPIs ===' AS section;

SELECT
    'Overall Conversion Rate' AS metric,
    ROUND(COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END)
        / COUNT(DISTINCT session_id) * 100, 2) AS value
FROM user_events
UNION ALL
SELECT
    'PDP→Cart Rate',
    ROUND(COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END)
        / COUNT(DISTINCT CASE WHEN page_category = 'PDP' THEN session_id END) * 100, 2)
FROM user_events
-- 注: Bounce Rate 已从监控 KPI 中移除 —
-- 数据集中 bounce 事件在各页面/渠道分布过于均匀,
-- bounce 用户与非 bounce 用户转化率仅差 1pp,
-- 判断为随机标记而非真实行为信号 (详见 docs/06-funnel-critique-and-refinement.md)
SELECT
    'Refund Rate',
    ROUND(SUM(refund_flag) / COUNT(*) * 100, 2)
FROM transactions;
