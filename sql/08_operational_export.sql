-- 08: Operational Export — PIE Priority + Actionable List

USE ecommerce;

-- PIE priority assessment (based on actual funnel data)
SELECT '=== PIE Priority ===' AS section;
SELECT 'Browse->Cart' AS bottleneck, 2388 AS lost_sessions, 'High' AS ease,
    'Optimize product detail page (images/price/descriptions); Add personalized recommendations'
    AS action, 'P0-Immediate' AS priority
UNION ALL
SELECT 'Cart->Checkout', 476, 'Medium',
    'Shopping cart recovery email (1h after abandon); Display shipping cost early',
    'P0-Immediate'
UNION ALL
SELECT 'Checkout->Confirm', 113, 'High',
    'Simplify payment flow; Mobile checkout optimization; Payment failure retry',
    'P1-This Week';

-- High-value lost users (added to cart but did not checkout, sorted by cart items)
SELECT '=== Top 20 High-Value Lost Users (Cart Abandoners) ===' AS section;
SELECT f.SessionID, f.UserID, f.DeviceType, f.Country, f.ReferralSource,
    d_max.ItemsInCart AS max_cart_items
FROM funnel_wide f
JOIN (
    SELECT SessionID, MAX(ItemsInCart) AS ItemsInCart
    FROM user_behavior WHERE PageType = 'cart'
    GROUP BY SessionID
) d_max ON f.SessionID = d_max.SessionID
WHERE f.step3_cart = 1 AND f.step4_checkout = 0
ORDER BY d_max.ItemsInCart DESC
LIMIT 20;

SELECT '08_operational_export: Complete' AS status;
