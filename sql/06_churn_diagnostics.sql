-- 06: Churn Amount Quantification — Revenue loss at each stage

USE ecommerce;

-- Estimated cart value: 100 yuan
WITH loss_estimate AS (
    SELECT
        SUM(step2_product) - SUM(step3_cart) AS lost_at_product,
        SUM(step3_cart) - SUM(step4_checkout) AS lost_at_cart,
        SUM(step4_checkout) - SUM(step5_confirm) AS lost_at_checkout
    FROM funnel_wide
)
SELECT 'Browse->Cart' AS churn_point, lost_at_product AS lost_sessions,
    ROUND(lost_at_product * 50, 0) AS estimated_loss_yuan FROM loss_estimate
UNION ALL
SELECT 'Cart->Checkout', lost_at_cart, ROUND(lost_at_cart * 100, 0) FROM loss_estimate
UNION ALL
SELECT 'Checkout->Confirm', lost_at_checkout, ROUND(lost_at_checkout * 120, 0) FROM loss_estimate;

-- Cart abandonment by channel
SELECT '=== Cart Abandonment by Channel ===' AS section;
SELECT ReferralSource,
    SUM(CASE WHEN step3_cart = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END) AS cart_abandon_sessions,
    SUM(step3_cart) AS cart_sessions,
    ROUND(SUM(CASE WHEN step3_cart = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END)
        * 100.0 / NULLIF(SUM(step3_cart), 0), 2) AS abandon_rate_pct
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY abandon_rate_pct DESC;

-- Browse->Cart churn by channel
SELECT '=== Browse->Cart Churn by Channel ===' AS section;
SELECT ReferralSource,
    SUM(CASE WHEN step2_product = 1 AND step3_cart = 0 THEN 1 ELSE 0 END) AS lost_sessions,
    SUM(step2_product) AS product_sessions,
    ROUND(SUM(CASE WHEN step2_product = 1 AND step3_cart = 0 THEN 1 ELSE 0 END)
        * 100.0 / SUM(step2_product), 2) AS loss_rate_pct
FROM funnel_wide
GROUP BY ReferralSource
ORDER BY loss_rate_pct DESC;
