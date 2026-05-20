-- 07: 损失金额量化 + ROAS 分析

USE ecommerce;

-- ── 7.1 退款损失量化 ─────────────────────────────────
SELECT '=== Refund Loss Quantification ===' AS section;

SELECT
    p.category,
    SUM(CASE WHEN t.refund_flag = 1 THEN t.gross_revenue ELSE 0 END) AS refund_revenue,
    SUM(t.gross_revenue) AS total_revenue,
    ROUND(SUM(CASE WHEN t.refund_flag = 1 THEN t.gross_revenue ELSE 0 END)
        / SUM(t.gross_revenue) * 100, 2) AS refund_revenue_rate
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.category
ORDER BY refund_revenue DESC;

-- ── 7.2 广告 ROAS 估算 ────────────────────────────────
SELECT '=== Campaign ROAS Estimation ===' AS section;

SELECT
    c.campaign_id,
    c.channel,
    c.objective,
    c.target_segment,
    COUNT(DISTINCT t.transaction_id) AS orders,
    SUM(t.gross_revenue) AS total_revenue,
    ROUND(AVG(t.gross_revenue), 2) AS avg_order_value,
    ROUND(c.expected_uplift * 100, 2) AS expected_uplift_pct
FROM campaigns c
LEFT JOIN transactions t ON c.campaign_id = t.campaign_id
GROUP BY c.campaign_id, c.channel, c.objective, c.target_segment, c.expected_uplift
ORDER BY total_revenue DESC;

-- ── 7.3 品类 PIE 近似 ────────────────────────────────
SELECT '=== Category Loss Ranking ===' AS section;

SELECT
    p.category,
    COUNT(DISTINCT ue.session_id) AS viewing_sessions,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'add_to_cart' THEN ue.session_id END) AS cart_sessions,
    COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END) AS purchase_sessions,
    ROUND((
        COUNT(DISTINCT CASE WHEN ue.event_type = 'add_to_cart' THEN ue.session_id END)
        - COUNT(DISTINCT CASE WHEN ue.event_type = 'purchase' THEN ue.session_id END)
    ) / NULLIF(COUNT(DISTINCT ue.session_id), 0) * 100, 2) AS effective_loss_rate
FROM user_events ue
JOIN products p ON ue.product_id = p.product_id
WHERE ue.product_id IS NOT NULL
GROUP BY p.category
ORDER BY effective_loss_rate DESC;
