# Analysis Results & Business Insights

> Based on 5,000 sessions, 1,872 users, 12,719 behavior records.

## Key Findings

### 1. Full Funnel

| Stage | Sessions | Step Rate | Overall Rate |
|-------|----------|-----------|-------------|
| 1. Home | 5,000 | 100.00% | 100.00% |
| 2. Product | 3,987 | 79.74% | 79.74% |
| 3. Cart | 1,599 | 40.11% | 31.98% |
| 4. Checkout | 1,123 | 70.23% | 22.46% |
| 5. Confirm | 1,010 | 89.94% | 20.20% |

**Overall conversion: 20.2%**

### 2. Highest Churn

**Browse -> Cart is the highest churn stage** (40.11% step rate). 2,388 sessions browsed products but did not add to cart.

Note: Previous SQL analysis incorrectly labeled Cart->Checkout as the highest churn stage. This has been corrected.

### 3. Channel Differences

| Channel | Sessions | Conversion Rate | Traffic Share |
|---------|----------|-----------------|---------------|
| Google | 1,280 | 21.64% | 25.60% |
| Email | 1,251 | 20.06% | 25.02% |
| Direct | 1,226 | 19.82% | 24.52% |
| Social Media | 1,243 | 19.23% | 24.86% |

Google has the highest conversion rate, Social Media the lowest. Channel differences are modest (1-2pp range).

### 4. Device Differences

| Device | Sessions | Conversion Rate | Traffic Share |
|--------|----------|-----------------|---------------|
| Desktop | 1,666 | 20.35% | 33.32% |
| Mobile | 1,671 | 20.17% | 33.42% |
| Tablet | 1,663 | 20.08% | 33.26% |

Device differences are minimal — all three have essentially equal traffic and conversion rates.

### 5. Time Patterns

See runtime output from `compute_time_of_day_analysis()`.

### 6. PIE Priority

| Bottleneck | Potential | Importance | Ease | PIE Score |
|------------|-----------|------------|------|-----------|
| Browse->Cart | High | High | Med-High | Highest |
| Cart->Checkout | Med | Med | Medium | Medium |
| Checkout->Confirm | Low | Low | High | Low |

## Optimization Summary

| Priority | Bottleneck | Lost Sessions | Est. Loss | Action |
|----------|------------|---------------|-----------|--------|
| P0 | Browse->Cart | 2,388 | High | Product detail page optimization |
| P0 | Cart->Checkout | 476 | Med | Cart recovery email + transparent pricing |
| P1 | Checkout->Confirm | 113 | Low | Payment UX simplification + mobile adaptation |
