-- 03: 全链路漏斗概览 — 页面级漏斗 + 行为级漏斗

USE ecommerce;

-- ── 页面级漏斗 ──────────────────────────────────────
SELECT '=== Page-Level Funnel ===' AS report_section;

SELECT
    COUNT(DISTINCT CASE WHEN page_category = 'Home'     THEN session_id END) AS step1_home,
    COUNT(DISTINCT CASE WHEN page_category = 'PLP'      THEN session_id END) AS step2_plp,
    COUNT(DISTINCT CASE WHEN page_category = 'PDP'      THEN session_id END) AS step3_pdp,
    COUNT(DISTINCT CASE WHEN page_category = 'Cart'     THEN session_id END) AS step4_cart,
    COUNT(DISTINCT CASE WHEN page_category = 'Checkout' THEN session_id END) AS step5_checkout
FROM user_events;

-- ── 行为级漏斗 ──────────────────────────────────────
SELECT '=== Event-Level Funnel ===' AS report_section;

SELECT
    COUNT(DISTINCT CASE WHEN event_type = 'view'        THEN session_id END) AS step_view,
    COUNT(DISTINCT CASE WHEN event_type = 'click'       THEN session_id END) AS step_click,
    COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) AS step_add_cart,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase'    THEN session_id END) AS step_purchase
FROM user_events;

-- ── 流失率计算 (页面级) ───────────────────────────────
SELECT '=== Page Churn Rates ===' AS report_section;

WITH steps AS (
    SELECT
        COUNT(DISTINCT CASE WHEN page_category = 'Home'     THEN session_id END) AS home,
        COUNT(DISTINCT CASE WHEN page_category = 'PLP'      THEN session_id END) AS plp,
        COUNT(DISTINCT CASE WHEN page_category = 'PDP'      THEN session_id END) AS pdp,
        COUNT(DISTINCT CASE WHEN page_category = 'Cart'     THEN session_id END) AS cart,
        COUNT(DISTINCT CASE WHEN page_category = 'Checkout' THEN session_id END) AS checkout
    FROM user_events
)
SELECT
    'Home→PLP'       AS transition, ROUND((home - plp) / home * 100, 2)          AS churn_rate FROM steps
UNION ALL
SELECT 'PLP→PDP',       ROUND((plp - pdp) / NULLIF(plp, 0) * 100, 2)             FROM steps
UNION ALL
SELECT 'PDP→Cart',      ROUND((pdp - cart) / NULLIF(pdp, 0) * 100, 2)            FROM steps
UNION ALL
SELECT 'Cart→Checkout', ROUND((cart - checkout) / NULLIF(cart, 0) * 100, 2)      FROM steps;
