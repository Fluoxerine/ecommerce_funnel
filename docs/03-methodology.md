# CRO Methodology

## 1. Funnel Analysis

Classic AARRR funnel (Acquisition -> Activation -> Revenue), 5 key touchpoints:

```
Home -> Product Page -> Cart -> Checkout -> Confirmation
```

Each stage counts unique sessions (session counted once per stage). Conversion rate = next stage / current stage.

## 2. Revenue Loss Quantification

Cart abandonment value calculation (CRO standard):

- **Browse-stage loss**: Viewed product but didn't add to cart -> 50% of avg cart value (lower intent)
- **Cart-stage loss**: Added to cart but didn't checkout -> 100% of avg cart value
- **Checkout-stage loss**: Started checkout but didn't pay -> 120% of avg cart value (high intent premium)

## 3. Statistical Tests

| Method | Purpose | Assumption |
|--------|---------|------------|
| Chi-square independence | Is channel/device associated with conversion? | Expected freq >= 5 |
| Independent t-test | Continuous feature difference (lost vs converted) | Normality (robust with large N) |
| Cohen's d | t-test effect size | Reference: 0.2 small / 0.5 medium / 0.8 large (Cohen, 1988) |
| Kruskal-Wallis | Non-parametric multi-group comparison | Non-normal data |

## 4. PIE Priority Framework

PIE (Potential x Importance x Ease) — standard CRO prioritization from WiderFunnel:

- **Potential (1-10)**: Revenue recoverable by fixing this bottleneck
- **Importance (1-10)**: How many users are affected
- **Ease (1-10)**: Implementation difficulty (tech/design/ops cost)

PIE Score = P x I x E, sorted descending for optimization priority.
