# 电商漏斗 CRO 分析项目 — 实施计划 (v2.0)

> 2026-05-20 | v2.0 — 更新以反映实际 6 阶段流水线实现

## 架构概览

```
输入: data/
  events.csv (2M 行) ← transactions.csv ← customers.csv ← products.csv ← campaigns.csv

6 阶段流水线 (python/main.py):
  Stage 1: load_all_tables() → 5 表加载
  Stage 2: basic_cleaning_events() + build_session_attributes() + build_funnel_wide()
  Stage 3: compute_page_funnel + compute_channel_analysis + ... + compute_cohort_retention
  Stage 4: compute_churn_features + compute_churn_matrix
  Stage 5: compute_loss_amount + compute_pie_priority + statistical_tests + ...
  Stage 6: save_baseline + generate_strategy_brief

输出:
  output/cleaned_events.csv
  output/funnel_wide.csv (633,450 会话 × 38 列)
  output/baseline_snapshot.json
  output/charts/ (18 张图)
```

---

## Task 1: 项目结构验证

**验证所有文件存在且内容一致：**

```bash
# 验证数据文件
ls data/events.csv data/transactions.csv data/customers.csv data/products.csv data/campaigns.csv

# 验证核心 Python 模块
python -c "from python.data_loader import load_all_tables; print('OK')"
python -c "from python.data_cleaning import basic_cleaning_events, build_funnel_wide; print('OK')"
python -c "from python.funnel_analysis import compute_page_funnel, compute_loss_amount; print('OK')"
python -c "from python.visualization import plot_page_funnel, plot_loss_waterfall; print('OK')"

# 验证主流程
python -m python.main 2>&1 | tail -20
```

---

## Task 2: 数据模型验证（与 design doc 一致性检查）

**检查列名一致性：**

```python
# events.csv 预期列
expected_events_cols = ['event_id', 'customer_id', 'session_id', 'timestamp',
                        'page_category', 'event_type', 'traffic_source',
                        'device_type', 'session_duration_sec', 'experiment_group',
                        'campaign_id', 'product_id']

# transactions.csv 预期列
expected_txn_cols = ['transaction_id', 'customer_id', 'timestamp',
                     'gross_revenue', 'discount_applied', 'refund_flag',
                     'product_id', 'campaign_id']
```

---

## Task 3: 漏斗列名验证（最常见的"结果不对"来源）

**关键列名对照（已验证）：**

| Funnel Analysis 函数 | 使用的列 |
|----------------------|----------|
| compute_page_funnel | PAGE_FUNNEL_COLS = ['step1_home', 'step2_plp', 'step3_pdp', 'step4_cart', 'step5_checkout'] |
| compute_event_funnel | EVENT_FUNNEL_COLS = ['step_view', 'step_click', 'step_add_cart', 'step_purchase'] |
| compute_loss_amount | stage_pairs 用 step1_home→step2_plp→step3_pdp→step4_cart |
| compute_churn_features | CHURN_STAGES = [('首页→列表页', step1_home, step2_plp), ...] |
| compute_deep_link_analysis | step1_home, step2_plp, step_purchase |

**visualization.py 中列名兼容处理（已实现）：**

```python
# 01_page_funnel — 兼容新旧列名
rate_col = '交叉到达率(%)' if '交叉到达率(%)' in funnel_df.columns else '上一阶段转化率(%)'

# 03_channel_funnels — 兼容新旧列名
_rate_col = next(
    c for c in ['交叉到达率(%)', '上一阶段转化率(%)']
    if c in next(iter(channel_funnels.values())).columns
)
```

---

## Task 4: 输出结果验证（运行完整流程）

```bash
python -m python.main 2>&1 | grep -E "(完成|失败|WARNING|ERROR|漏斗|损失)"

# 检查输出文件
ls -la output/cleaned_events.csv  # 应存在且 > 0
ls -la output/funnel_wide.csv      # 应存在且 > 0
ls -la output/charts/             # 应有 17-18 个文件
ls -la output/baseline_snapshot.json
```

**预期关键数字（来自 analysis.log）：**

| 指标 | 预期值 |
|------|--------|
| 总会话数 | 633,450 |
| 购买会话数 | 95,535 |
| 整体会话转化率 | 15.08% |
| 浏览→购买转化率 | 18.13% |
| 首页会话数 | 300,782 |
| PLP 会话数 | 396,329（超过首页，深链正常） |
| 损失金额合计 | ¥59,760,920 |
| P0 瓶颈 | 详情页→购物车，年损失 ¥24.0M |

---

## Task 5: 文档一致性检查

**检查 docs/04-results.md 与实际运行结果是否一致：**

```bash
# 对比 04-results.md 中的数字与 analysis.log 中的数字
# 核心验证点：
# 1. Session CR = 15.08% 对应 95,535 / 633,450
# 2. View-to-Purchase CR = 18.13% 对应 95,535 / 526,869
# 3. 首页 300,782, PLP 396,329, Cart 172,491, Checkout 172,734
# 4. 损失合计 ¥59,760,920
```

**不一致常见原因：**
- 文档写的是旧版分析结果，代码经过多次修改后输出变化了
- 口径定义变化（如转化率从"上阶段转化率"改为"交叉到达率"）
- 列名变化（漏斗步骤列名改了，但文档没同步）

---

## Task 6: 常见问题排查

| 症状 | 可能原因 | 排查命令 |
|------|----------|----------|
| 图表为空或报错 | 列名不匹配 | 检查 PAGE_FUNNEL_COLS 是否与 funnel_df.columns 一致 |
| 损失金额为 0 | stage_pairs 列名错误 | 检查 CHURN_STAGES 中的列名 |
| 漏斗数字对不上 | 口径混淆（覆盖 vs 严格路径） | 检查 compute_page_funnel vs compute_strict_page_funnel |
| funnel_wide 为空 | data_cleaning 阶段失败 | 检查 `python -c "from python.data_cleaning import build_funnel_wide"` |
| 可视化失败 | 某 DataFrame 列为空 | 检查 funnel_df.columns，特别是 rate_col 兼容逻辑 |

---

## Task 7: 完整运行验证

```bash
cd "d:\D30360\Documents\ecommerce_funnel_analysis"

# 1. 完整流程
python -m python.main

# 2. 验证输出数量
echo "=== 图表文件 ===" && ls output/charts/ | wc -l
echo "=== funnel_wide 行数 ===" && wc -l output/funnel_wide.csv
echo "=== cleaned_events 行数 ===" && wc -l output/cleaned_events.csv

# 3. 验证关键 KPI
python -c "
import json
with open('output/baseline_snapshot.json') as f:
    snap = json.load(f)
print('Session CR:', snap['session_conversion_rate'], '%')
print('View-to-Purchase CR:', snap['view_to_purchase_rate'], '%')
print('Total sessions:', snap['total_sessions'])
print('Purchase sessions:', snap['purchase_sessions'])
"
```

---

## Task 8: 提交更新后的文档

```bash
git add docs/superpowers/specs/2026-05-20-funnel-cro-design-v2.md
git add docs/superpowers/plans/2026-05-20-funnel-cro-implementation-v2.md
git commit -m "docs: sync design and plan with actual v2.0 implementation"
```