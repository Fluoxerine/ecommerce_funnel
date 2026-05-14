-- 04: Full Funnel + Stage Conversion Rates
-- FIXED: Highest churn is "Browse->Cart" (40.11%), NOT "Cart->Checkout"

USE ecommerce;

WITH steps AS (
    SELECT
        SUM(step1_home) AS s1, SUM(step2_product) AS s2,
        SUM(step3_cart) AS s3, SUM(step4_checkout) AS s4,
        SUM(step5_confirm) AS s5
    FROM funnel_wide
)
SELECT '1.Home' AS stage, s1 AS sessions, 100.00 AS step_rate, 100.00 AS overall_rate FROM steps
UNION ALL
SELECT '2.Product', s2,
    ROUND(s2 * 100.0 / NULLIF(s1, 0), 2),
    ROUND(s2 * 100.0 / s1, 2) FROM steps
UNION ALL
SELECT '3.Cart', s3,
    ROUND(s3 * 100.0 / NULLIF(s2, 0), 2),
    ROUND(s3 * 100.0 / s1, 2) FROM steps
UNION ALL
SELECT '4.Checkout', s4,
    ROUND(s4 * 100.0 / NULLIF(s3, 0), 2),
    ROUND(s4 * 100.0 / s1, 2) FROM steps
UNION ALL
SELECT '5.Confirm', s5,
    ROUND(s5 * 100.0 / NULLIF(s4, 0), 2),
    ROUND(s5 * 100.0 / s1, 2) FROM steps;

SELECT '04_funnel_overview: NOTE: Highest churn is Browse->Cart (40.11%), not Cart->Checkout (70.23%)' AS note;
