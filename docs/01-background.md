# Project Background

## Business Scenario

A mid-size e-commerce platform with the following data profile:
- 5,000 user sessions
- 1,872 unique users
- 12,719 page-view records
- 5 funnel stages: Home -> Product -> Cart -> Checkout -> Confirmation
- 4 traffic channels: Direct, Email, Google, Social Media
- 3 device types: Desktop, Mobile, Tablet

### Problem 1: Low Conversion, Unknown Bottleneck

Overall conversion rate is 20.2% (1,010 / 5,000). The operations team doesn't know:
- Which funnel stage causes the most drop-off
- How conversion differs by traffic channel
- Whether device experience varies significantly

### Problem 2: No Data-Driven Prioritization

Both tech and ops teams have competing improvement proposals (product page redesign, cart recovery emails, payment flow simplification), but no data to rank them — what to fix first, and how much revenue will it recover?

## Project Goals

1. **Quantify churn at each funnel stage**: How many sessions drop off, and what is the estimated revenue loss
2. **Diagnose root causes**: Which dimensions (channel/device/country/time) have significantly higher churn rates
3. **Prioritize fixes**: PIE (Potential x Importance x Ease) ranking, so the tech team knows what to fix first
4. **Visual dashboard**: For management and operations monitoring

## Success Criteria

| Dimension | Standard |
|-----------|----------|
| Funnel coverage | All 5 stages counted, no double-counting |
| Churn location | Channel x device conversion rate differences identified |
| Statistical validation | At least 2 significant differences found (chi2, t-test) |
| Actionable output | At least 3 bottlenecks with specific fix recommendations and estimated recovery |
| Visualization | At least 10 reusable charts |
