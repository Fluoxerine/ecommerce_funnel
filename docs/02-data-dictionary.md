# Data Dictionary

## Raw Data: user_behavior / customer_journey.csv

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| SessionID | string | Unique session ID | session_0 ~ session_4999 |
| UserID | string | Unique user ID | user_1001 ~ user_2999 |
| Timestamp (CSV) | datetime | Page view time | 2025-01-01 ~ 2025-12-31 |
| EventTime (MySQL) | timestamp | Same as Timestamp, renamed in MySQL | |
| PageType | string | Page type | home, product_page, cart, checkout, confirmation |
| DeviceType | string | Device type | Desktop, Mobile, Tablet |
| Country | string | User country | USA, UK, Germany, France, Canada, India, Australia |
| ReferralSource | string | Traffic source | Direct, Email, Google, Social Media |
| TimeOnPage_seconds | int | Time spent on page (seconds) | 15 ~ 180 |
| ItemsInCart | int | Items currently in cart | 0 ~ 5 |
| Purchased | int | Whether purchased (session-level flag) | 0 or 1 |

## Cleaned Wide Table: funnel_wide

| Field | Type | Description |
|-------|------|-------------|
| SessionID | string | Session ID (PK) |
| UserID | string | User ID |
| DeviceType | string | Primary device (mode) |
| Country | string | Primary country (mode) |
| ReferralSource | string | Primary channel (mode) |
| step1_home | 0/1 | Visited homepage |
| step2_product | 0/1 | Visited product page |
| step3_cart | 0/1 | Visited cart |
| step4_checkout | 0/1 | Visited checkout |
| step5_confirm | 0/1 | Visited confirmation |
| is_purchased | 0/1 | Session-level purchase flag |

## Derived Features (Python)

| Feature | Source | Description |
|---------|--------|-------------|
| hour | Timestamp | Hour of day (0-23) |
| weekday | Timestamp | Day of week (0=Mon, 6=Sun) |
| stage | PageType mapping | Chinese funnel stage label |
| session_is_converted | Purchased aggregation | Session-level conversion label |
