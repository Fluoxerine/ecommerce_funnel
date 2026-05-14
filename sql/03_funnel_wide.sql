-- 03: Funnel Wide Table (clean + dedup + build)

USE ecommerce;

-- Step 1: Dedup + basic cleaning
DROP TEMPORARY TABLE IF EXISTS tmp_deduped;
CREATE TEMPORARY TABLE tmp_deduped AS
WITH clean_base AS (
    SELECT DISTINCT
        SessionID, UserID, EventTime,
        LOWER(PageType) AS PageType, DeviceType,
        COALESCE(Country, 'Unknown') AS Country,
        COALESCE(ReferralSource, 'Unknown') AS ReferralSource,
        COALESCE(TimeOnPage_seconds, 0) AS TimeOnPage_seconds,
        COALESCE(ItemsInCart, 0) AS ItemsInCart,
        COALESCE(Purchased, 0) AS Purchased
    FROM user_behavior
    WHERE SessionID IS NOT NULL AND UserID IS NOT NULL
      AND EventTime IS NOT NULL AND PageType IS NOT NULL
      AND EventTime < NOW()
      AND TimeOnPage_seconds BETWEEN 0 AND 86400
      AND ItemsInCart >= 0
      AND Purchased IN (0, 1)
),
session_dedup AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY SessionID, PageType ORDER BY EventTime) AS rn
    FROM clean_base
)
SELECT * FROM session_dedup WHERE rn = 1;

-- Step 2: Filter invalid sessions (total duration < 5s)
DROP TEMPORARY TABLE IF EXISTS tmp_valid_sessions;
CREATE TEMPORARY TABLE tmp_valid_sessions AS
SELECT SessionID FROM tmp_deduped
GROUP BY SessionID
HAVING SUM(TimeOnPage_seconds) >= 5;

-- Step 3: Extract session attributes (mode)
DROP TEMPORARY TABLE IF EXISTS tmp_top_attributes;
CREATE TEMPORARY TABLE tmp_top_attributes AS
WITH session_attributes AS (
    SELECT SessionID, DeviceType, Country, ReferralSource, UserID,
        ROW_NUMBER() OVER (PARTITION BY SessionID ORDER BY COUNT(*) DESC) as rn
    FROM tmp_deduped
    GROUP BY SessionID, DeviceType, Country, ReferralSource, UserID
)
SELECT * FROM session_attributes WHERE rn = 1;

-- Step 4: Build funnel wide table
TRUNCATE TABLE funnel_wide;
INSERT INTO funnel_wide
SELECT
    d.SessionID, ta.UserID, ta.DeviceType,
    ta.Country, ta.ReferralSource,
    MAX(CASE WHEN d.PageType = 'home' THEN 1 ELSE 0 END) AS step1_home,
    MAX(CASE WHEN d.PageType = 'product_page' THEN 1 ELSE 0 END) AS step2_product,
    MAX(CASE WHEN d.PageType = 'cart' THEN 1 ELSE 0 END) AS step3_cart,
    MAX(CASE WHEN d.PageType = 'checkout' THEN 1 ELSE 0 END) AS step4_checkout,
    MAX(CASE WHEN d.PageType = 'confirmation' THEN 1 ELSE 0 END) AS step5_confirm,
    MAX(d.Purchased) AS is_purchased
FROM tmp_deduped d
JOIN tmp_top_attributes ta ON d.SessionID = ta.SessionID
WHERE d.SessionID IN (SELECT SessionID FROM tmp_valid_sessions)
GROUP BY d.SessionID, ta.UserID, ta.DeviceType, ta.Country, ta.ReferralSource;

SELECT COUNT(*) AS wide_table_sessions FROM funnel_wide;

-- Validation
SELECT
    SUM(CASE WHEN step5_confirm = 1 AND step4_checkout = 0 THEN 1 ELSE 0 END) AS logic_error_1,
    SUM(CASE WHEN is_purchased != step5_confirm THEN 1 ELSE 0 END) AS logic_error_2
FROM funnel_wide;

SELECT '03_funnel_wide: Complete' AS status;
