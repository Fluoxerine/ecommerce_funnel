# 电商漏斗分析项目 — 资深数据分析师 × HR 双视角评审

> 评审日期：2026-05-20 | 评审范围：Python/SQL/文档/测试/Power BI/可视化 | 全量代码阅读

---

## 目录

1. [数据分析师视角](#一数据分析师视角)
   - 1.1 [做得好的地方](#11-做得好的地方)
   - 1.2 [需要修正的问题](#12-需要修正的问题)
   - 1.3 [建议新增的分析](#13-建议新增的分析)
2. [HR / 面试官视角](#二hr--面试官视角)
   - 2.1 [能力矩阵评估](#21-能力矩阵评估)
   - 2.2 [面试高频追问模拟](#22-面试高频追问模拟)
   - 2.3 [整体定位与提升建议](#23-整体定位与提升建议)
3. [附录：逐文件代码走查记录](#三附录逐文件代码走查记录)

---

## 一、数据分析师视角

### 1.1 做得好的地方

#### 漏斗方法论经过深度思考

项目从最初"页面漏斗倒挂"（PLP 到达数 > Home 到达数）的问题出发，经历了完整的诊断 → 讨论 → 重构过程：

| 阶段 | 问题 | 解决方案 |
|:---|:---|:---|
| V1 | 页面漏斗 Home < PLP，人数倒挂 | 识别为"多入口/深链"问题 |
| V2 | 交叉引用转化率本质是 Overlap Rate | 新增严格路径漏斗作为对照 |
| V3 | 深链流量占 54.9% PLP 但缺乏分析 | 新增深链分析模块（路径分类 + 分渠道对比） |
| V4 | 需要进一步分层 | 新增新用户 vs 老用户漏斗、周末 vs 工作日对比 |

这个迭代过程（完整记录在 [2026-05-20-funnel-critique.md](2026-05-20-funnel-critique.md)）本身就是分析能力的证明——不是"画一个漏斗图就结束"，而是真正思考了多入口、非线性路径这些电商真实场景。

最终形成了三套互补的漏斗体系：

- **页面覆盖分析**（宽松漏斗）：统计到达过各页面的会话，允许倒挂，反映页面触达能力
- **严格路径漏斗**（顺序漏斗）：必须按 Home→PLP→PDP→Cart→Checkout 时间顺序，反映理想路径流转
- **行为级漏斗**（事件漏斗）：view→click→add_to_cart→purchase，反映用户意图升级

#### 统计方法使用规范

| 方法 | 代码位置 | 评价 |
|:---|:---|:---|
| Welch's t-test + Cohen's d | [funnel_analysis.py:608-643](../../python/funnel_analysis.py#L608-L643) | Welch 不假设方差齐性，Cohen's d 避免大样本 p-hacking。正确 |
| 卡方独立性检验 + Bonferroni 校正 | [funnel_analysis.py:784-803](../../python/funnel_analysis.py#L784-L803) | 4 个维度 → α=0.0125。正确 |
| Shift-Share 归因分解 | [funnel_analysis.py:807-888](../../python/funnel_analysis.py#L807-L888) | 结构效应 vs 质量效应分解。合理 |
| PIE 优先级矩阵 | [funnel_analysis.py:749-777](../../python/funnel_analysis.py#L749-L777) | WiderFunnel 方法论，行业标准 |
| GA4 行为阈值分桶 | [config.py:72-78](../../python/config.py#L72-L78) | 固定阈值比等频分桶更适合跨周期对比 |

方法选择合理，没有为了炫技而滥用复杂模型。

#### 六阶段闭环结构完整

```
数据探查 → 漏斗建模 → 多维诊断 → 流失根因 → 损失量化 → 策略闭环
```

每一阶段都有对应的代码函数、日志输出、可视化图表。PIE 优先级矩阵、策略摘要自动生成（[funnel_analysis.py:1009-1045](../../python/funnel_analysis.py#L1009-L1045)）、基准快照（[funnel_analysis.py:977-1006](../../python/funnel_analysis.py#L977-L1006)）都体现了"分析要能落地"的意识。

#### 自我审查与持续改进

[2026-05-18-review-findings.md](2026-05-18-review-findings.md) 是一份质量很高的代码审查文档——P0-P3 分类、具体的修复代码、验证命令都有。从 git 记录可以看到，审查中发现的以下问题已经被修复：

- 测试代码重写（匹配当前 API 和数据模型）
- 流失会话级联去重（解决 704K > 633K 的逻辑错误）
- `total_revenue` 不再静默取绝对值
- 品类漏斗 view 计数增加 event_type 过滤
- 转化率改为双口径（会话转化率 + 浏览转化率）

---

### 1.2 需要修正的问题

#### P0 — 三年趋势分析的因果推断不够严谨

**问题**：

2021 年 421,309 会话 → 2022 年 155,307 会话 → 2023 年仅 56,834 会话。数据量三年下降 86%，这不是正常的业务波动。

在这种数据完整性存疑的情况下，把转化率从 16.97% 降到 7.98%（降幅 53%）直接归因为"全渠道质量恶化"，并将 Shift-Share 分解结果（质量效应 -9.3pp）作为核心结论呈现，是不够严谨的。

更可能的解释：

- 2022-2023 年数据只是完整数据的一个子集（例如仅包含特定渠道或特定地区）
- 采样偏差导致低转化率时段/渠道被过度代表
- 数据生成时的 artifact（如果这是模拟数据）

**建议修复**：

在 [04-results.md](../04-results.md) 的"十二、月度趋势"部分增加一个明确的数据完整性警示：

> **数据完整性警示**：2022 年和 2023 年的会话量分别仅为 2021 年的 37% 和 13%。转化率下降趋势可能部分或全部由数据不完整/采样偏差导致。Shift-Share 归因分解作为方法演示，在数据完整性验证前不应作为确定性业务结论。

同时，在 `compute_trend_analysis` 函数中增加会话量变化率的日志输出：

```python
# 在 funnel_analysis.py compute_trend_analysis 末尾增加
for y in years[1:]:
    prev_sessions = yearly_sessions[years[i-1]]
    curr_sessions = yearly_sessions[y]
    change_pct = (curr_sessions - prev_sessions) / prev_sessions * 100
    logger.warning(
        "  %d 年会话量较上年变化: %+.1f%% (%s → %s) — 数据完整性存疑",
        y, change_pct, f"{prev_sessions:,}", f"{curr_sessions:,}"
    )
```

---

#### P0 — 损失金额计算的客单价基准有问题

**问题位置**：[python/funnel_analysis.py:687-689](../../python/funnel_analysis.py#L687-L689)

```python
purchased = funnel_wide[funnel_wide['step_purchase'] == 1]
purchased_revenue = purchased[['customer_id', 'total_revenue']].drop_duplicates('customer_id')
aov = purchased_revenue['total_revenue'].mean()
```

`total_revenue` 在宽表中是客户级累计值（在 [data_cleaning.py:173-179](../../python/data_cleaning.py#L173-L179) 中按 customer_id sum 聚合）。一个购买了 5 次、每次 ¥100 的客户，其 `total_revenue = ¥500`，会被当作"一个流失用户 = ¥500 潜在损失"。

这导致 AOV 被高估约 N 倍（N ≈ 人均购买次数）。对于本项目，这直接导致：
- 年估算损失 ¥59,760,920 被高估
- 各环节损失金额被等比例高估
- PIE 得分中的 Potential 维度失真

**建议修复**：

方案一（推荐）：直接使用 transactions 表的单笔 `gross_revenue` 均值：

```python
def compute_loss_amount(funnel_wide: pd.DataFrame,
                        transactions: pd.DataFrame | None = None) -> pd.DataFrame:
    # 使用单笔交易级别的客单价，而非客户累计值
    if transactions is not None and len(transactions) > 0:
        valid_txn = transactions[transactions['gross_revenue'].notna()]
        aov = valid_txn['gross_revenue'].mean()
    else:
        # fallback: funnel_wide 中已转化用户的 per-transaction 估算
        purchased = funnel_wide[funnel_wide['step_purchase'] == 1]
        # total_revenue / total_transactions ≈ per-transaction AOV
        purchased_cust = purchased[['customer_id', 'total_revenue', 'total_transactions']].drop_duplicates('customer_id')
        purchased_cust = purchased_cust[purchased_cust['total_transactions'] > 0]
        aov = (purchased_cust['total_revenue'] / purchased_cust['total_transactions']).mean()

    logger.info("单笔订单客单价: ¥%.2f（来源: %s）",
                aov,
                'transactions表' if transactions is not None else 'funnel_wide估算')
```

方案二：在宽表构建时就增加 `avg_order_value` 列（total_revenue / total_transactions），分析时使用该列。

**影响评估**：

- 当前 AOV ≈ ¥100.25（客户累计值均值）
- 修正后 AOV 可能约为 ¥80-90（单笔订单均值，取决于人均购买次数）
- 年估算损失将从 ¥59.76M 下调约 10-20%
- 但 PIE 的相对排序（哪个环节优先）不会改变——各环节等比例缩放

---

#### P1 — 渠道瓶颈分析中"瓶颈"的定义混淆

**问题位置**：[04-results.md](../04-results.md) 第 102-112 行，以及 [python/funnel_analysis.py:263-292](../../python/funnel_analysis.py#L263-L292)

当前 `compute_channel_funnels` 通过找 `上一阶段转化率(%)` 的最小值来确定瓶颈：

```python
churn_idx = funnel_df[1:]['上一阶段转化率(%)'].idxmin()
```

但在跨环节比较中，"上一阶段转化率最低"不等于"绝对流失最严重"。例如：

| 环节 | 到达会话 | 转化率 | 绝对流失 |
|:---|:---|:---|:---|
| 详情页→购物车 | 323,259 | 25.8% | 239,854 |
| 购物车→结算页 | 99,102 | 25.9% | 73,361 |

两个环节转化率几乎一样（25.8% vs 25.9%），但详情页→购物车的绝对流失是购物车→结算页的 3.3 倍。仅仅因为转化率差 0.1pp 就把某个环节标为"瓶颈"是不合理的。

**建议修复**：

在 `compute_channel_funnels` 中同时报告两个指标：

```python
# 在 churn_idx 计算后增加
worst_absolute = funnel_df.iloc[1:].copy()
worst_absolute['绝对流失'] = [
    counts[i-1] - overlap_counts[i-1]
    for i in range(1, len(counts))
]
abs_churn_idx = worst_absolute['绝对流失'].idxmax()
logger.info("  %s: 转化率瓶颈=%s (%.2f%%), 绝对流失瓶颈=%s (%s 会话)",
            channel,
            funnel_df.loc[churn_idx, '漏斗阶段'],
            funnel_df.loc[churn_idx, '上一阶段转化率(%)'],
            funnel_df.loc[abs_churn_idx, '漏斗阶段'],
            f"{int(worst_absolute.loc[abs_churn_idx, '绝对流失']):,}")
```

---

#### P1 — 流失特征分析存在部分循环论证

**问题位置**：[python/funnel_analysis.py:606-643](../../python/funnel_analysis.py#L606-L643)

用 `event_count` 和 `total_duration_sec` 对比"流失组 vs 转化组"，结论是"事件数差异大（d=-0.74），转化用户互动更深"。

但"转化"的定义就是完成了更多漏斗步骤——完成更多步骤天然产生更多事件和更长停留时间。这是一定程度的同义反复（tautology），不提供真正的诊断价值。事件数差异是"转化更多的自然结果"，而不是"转化的驱动因素"。

[2026-05-18-review-findings.md](2026-05-18-review-findings.md) 第 282-294 行已经指出了这个问题，并建议了替代特征（加购前浏览品类数、是否使用搜索、同一商品重复查看次数等），但这些替代特征受限于数据集字段未能实现。

**建议**：

在当前数据限制下，保留现有分析但修改结论措辞：

> **修正前**：事件互动深度比停留时长更重要，优化重点应放在增加页面内交互
>
> **修正后**：流失组与转化组在事件数和停留时长上存在显著差异（p<0.001），但这部分反映了完成更多漏斗步骤的自然结果。在当前数据字段限制下，无法进一步区分"互动驱动转化"和"转化带来互动"。建议在埋点层面增加搜索使用、评价查看、比价行为等独立事件，以提升流失诊断的可操作性。

---

#### P2 — 品类分析的"浏览会话"被系统性低估

**问题位置**：[python/funnel_analysis.py:471-509](../../python/funnel_analysis.py#L471-L509)

品类分析通过 `events['product_id'].notna()` 过滤后关联 products 表获取 category。但大量浏览事件（首页浏览、PLP 列表页浏览、搜索结果页浏览等）没有 product_id。这意味着：

- 品类浏览会话数被系统性低估
- 浏览→加购转化率被系统性高估
- Electronics 和 Fashion 这类搜索驱动品类受影响更大

**当前代码**（已修复 event_type 过滤）：

```python
events_with_cat = events[events['product_id'].notna()].copy()
view_by_cat = (
    events_with_cat[events_with_cat['event_type'] == 'view']
    .groupby('category')['session_id'].nunique()
    .reset_index(name='浏览会话')
)
```

**影响评估**：

这个问题在当前数据集中影响有限——因为数据是模拟的，event 表中 product_id 缺失率可能不高。但在真实电商数据中，这会是一个严重问题。建议在文档中注明此局限。

---

#### P2 — Bounce 事件数据质量问题未在输出中体现

**数据验证**（[2026-05-20-funnel-critique.md](2026-05-20-funnel-critique.md) 第 229-255 行）：

| 指标 | 观察值 | 真实电商预期 |
|:---|:---|:---|
| 各页面 Bounce 率 | 全部约 9.5% | 首页通常高于详情页 |
| 各渠道 Bounce 率 | 全部约 30% | Display > Social > Search > Email |
| Bounce 用户购买率 | 14.31% | 几乎不可能购买 |
| Bounce vs 非 Bounce CR 差 | 仅 1.04pp | 通常 10pp+ |

结论很明确：这个数据集中的 bounce 事件更像是随机标记，而非真实行为信号。

**但**：[sql/08_operational_export.sql:44-48](../../sql/08_operational_export.sql#L44-L48) 仍在计算 Bounce Rate 作为监控 KPI，与内部结论矛盾。

**建议**：从监控 KPI 中移除 Bounce Rate，或增加注释说明数据质量问题。

---

#### P3 — 各国家转化率高度一致暗示数据生成方式

| 国家 | 会话数 | 转化率 |
|:---|---:|---:|
| AU | 44,078 | 15.22% |
| CA | 62,776 | 15.17% |
| BR | 63,864 | 15.16% |
| IN | 126,687 | 15.13% |
| DE | 50,015 | 15.05% |
| US | 221,479 | 15.05% |
| UK | 64,551 | 14.85% |

七个国家的转化率极差仅 0.37 个百分点，卡方检验 p=0.6295（不显著）。这在真实电商中几乎不可能——不同国家的支付习惯、物流体系、消费文化差异通常会导致至少 3-5pp 的转化率差异。这是数据为模拟生成的又一佐证。

建议在分析中坦诚说明数据的模拟性质，而非将其作为"发现"呈现。

---

### 1.3 建议新增的分析

#### Cohort 留存分析（最高优先级）

有 timestamp + customer_id，完全有条件做周度/月度留存 cohort。这是本项目最大的分析空白。

```python
def compute_cohort_retention(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """按首次购买月份分组的留存 Cohort 分析"""
    funnel_wide = funnel_wide.copy()
    funnel_wide['first_purchase_month'] = pd.to_datetime(
        funnel_wide['first_purchase_date']
    ).dt.to_period('M')

    purchased = funnel_wide[funnel_wide['step_purchase'] == 1]
    purchased['purchase_month'] = pd.to_datetime(
        purchased['session_start']
    ).dt.to_period('M')

    # cohort index = 购买月份 - 首次购买月份
    purchased['cohort_index'] = (
        purchased['purchase_month'] - purchased['first_purchase_month']
    ).apply(lambda x: x.n if hasattr(x, 'n') else 0)

    # 构建留存矩阵
    cohort_pivot = purchased.pivot_table(
        index='first_purchase_month',
        columns='cohort_index',
        values='customer_id',
        aggfunc='nunique',
    )
    cohort_pivot['cohort_size'] = cohort_pivot[0]
    for col in cohort_pivot.columns:
        if col != 'cohort_size':
            cohort_pivot[col] = (
                cohort_pivot[col] / cohort_pivot['cohort_size'] * 100
            ).round(1)

    return cohort_pivot
```

这个分析可以直接回答：
- 首购后第 2/3/6 个月的回购率是多少？
- 不同渠道获客的留存曲线有何差异？
- 留存率是否也在三年间下降了？

#### Cramér's V 效应量

卡方检验在 63 万样本下几乎必然显著（p<0.0001），需要 Cramér's V 来判断关联强度：

```python
def cramers_v(chi2: float, n: int, min_dim: int) -> float:
    """Cramér's V 效应量 — 卡方检验的补充"""
    return np.sqrt(chi2 / (n * (min_dim - 1))) if min_dim > 1 else 0

# 在 statistical_tests 中增加
n = len(funnel_wide)
min_dim = min(ct.shape)
v = cramers_v(chi2, n, min_dim)
strength = '强' if v > 0.3 else '中' if v > 0.1 else '弱'
logger.info("  %s: Cramér's V = %.3f (%s)", dim, v, strength)
```

---

## 二、HR / 面试官视角

### 2.1 能力矩阵评估

| 能力维度 | 证据 | 强度 | 面试中如何追问 |
|:---|:---|:---|:---|
| **Python 数据分析** | 5 个模块、~1500 行、pandas/scipy/numpy/plotly | ★★★★ | "你用到了 scipy 的哪些统计函数？为什么选 Welch's t-test 而不是 Student's t-test？" |
| **SQL** | 8 个 SQL 脚本、CTE、窗口函数、聚合 | ★★★ | "08_operational_export.sql 中的 session_funnel CTE 能直接用吗？" |
| **统计方法** | t 检验、Cohen's d、卡方、Bonferroni、Shift-Share | ★★★★ | "为什么用 Bonferroni 而不是 FDR？样本量 63 万时卡方检验有什么问题？" |
| **数据可视化** | 16 张图、matplotlib + plotly、配色统一 | ★★★★ | "为什么行为漏斗用 plotly 而多维分析用 matplotlib？" |
| **业务思维** | 六阶段闭环、PIE 优先级、策略自动生成 | ★★★★ | "PIE 的 Ease 评分是你主观给的还是有数据支撑？" |
| **工程质量** | 测试、配置管理、日志、类型提示、`__init__.py` | ★★★ | "pytest 全跑通了吗？覆盖率多少？" |
| **文档能力** | 8 篇文档、方法论 + 结果 + 审查 | ★★★★ | 文档本身就是答案 |
| **Power BI** | PBIR + TMDL、4 页 12 视觉对象 | ★★★ | "TMDL 和 TMSL 的区别是什么？为什么选 PBIR 格式？" |
| **版本控制** | Git、有意义的 commit message | ★★★ | — |

---

### 2.2 面试高频追问模拟

#### Q1: "这个数据是真实的还是模拟的？"

**面试官意图**：考察诚信 + 对数据质量的判断力。

**数据中的线索**（面试官自己能看出来）：
- 七个国家转化率极差仅 0.37pp
- Bounce 率在所有页面/渠道惊人一致
- 200 万条事件但模式高度规律
- event_type 和 page_category 各恰好 5 个值，无缺失无异常

**建议回答策略**：
> "数据集是从 Kaggle/UCI 获取的电商用户行为模拟数据，包含约 200 万条事件。虽然是模拟数据，但它具备真实电商数据的大部分字段（事件类型、页面分类、设备、渠道、交易金额等），可以用来验证分析方法论。我在分析过程中也发现了一些模拟数据的特征——比如各国家转化率高度一致、Bounce 事件分布过于均匀——并在文档中做了标注。我认为分析方法论是可迁移的，换成真实数据也适用。"

---

#### Q2: "转化率三年降了 53%，你觉得真实原因是什么？"

**面试官意图**：考察因果推理能力 + 对数据局限的敏感性。

**陷阱**：如果直接回答"全渠道质量恶化"，面试官会继续追问"你怎么排除数据不完整的可能？"

**建议回答策略**：
> "这个结论需要谨慎对待。我注意到三年间会话量从 42 万降到了 5.7 万，下降了 86%。在数据量如此剧烈变化的情况下，转化率下降更可能是数据不完整或采样偏差导致的，而非真实的业务恶化。我做了 Shift-Share 归因分解作为方法演示——分解为结构效应和质量效应——但在数据完整性验证之前，这个结果更适合作为方法论示例而非业务结论。如果是真实工作场景，我会先和数据工程团队确认 2022-2023 年的数据管道是否有变更。"

---

#### Q3: "你估算年损失 6000 万，但三年总收入才 837 万，这怎么解释？"

**面试官意图**：考察数字敏感度 + 指标定义清晰度。

**问题实质**：
- ¥59.76M 是"潜在年损失" = 所有流失会话 × 客单价（理论最大值）
- ¥8.37M 是"实际三年收入" = 已转化用户的累计交易额（实际值）
- 两者分子/分母/时间窗口都不一致

**建议回答策略**：
> "这两个数字的口径不同。¥59.76M 是假设所有流失用户都完成购买的理论最大机会空间——用流失会话数 × 客单价估算。而 ¥8.37M 是已转化用户的实际三年累计交易额。它们的基数不同：前者基于 596K 流失会话，后者基于 95K 购买会话。需要承认的是，当前客单价使用的是客户级累计值而非单笔订单均值，这可能导致损失被高估。如果要更精确，我会用 transactions 表的单笔 gross_revenue 均值作为 AOV。修正后损失估算大约会下调 10-20%。"

---

#### Q4: "如果只让你保留三个分析，你留哪三个？"

**面试官意图**：考察优先级判断 + 抓重点的能力。

**建议回答策略**：
> "第一，漏斗建模——页面覆盖分析 + 严格路径漏斗，这是整个分析的起点，定位瓶颈。第二，渠道分层漏斗——不同渠道的瓶颈不同（搜索/社交在 PDP→Cart，邮件/直接访问在 Cart→Checkout），直接指导差异化策略。第三，新老用户对比漏斗——两组的页面漏斗几乎一样但行为漏斗差 1.7 倍，这指向了用户激活策略的方向。
>
> 损失量化和 PIE 是前三个分析的延伸应用。趋势分析在数据完整性存疑的情况下参考价值有限。"

---

#### Q5: "PIE 的 Ease 评分（6/7/8）是你主观给的还是有依据的？"

**面试官意图**：考察方法论透明度。

**建议回答策略**：
> "Ease 评分目前是基于行业经验的主观判断——购物车→结算页优化（如一键结算）相对容易，所以给了 8 分；详情页改版涉及 UX 重构，给了 6 分。在真实业务中，Ease 应该由工程团队评估开发工作量，或者参考历史迭代周期。这个 PIE 框架的价值更多在于提供一个结构化的优先级讨论起点，而不是给出绝对评分。"

---

### 2.3 整体定位与提升建议

#### 当前定位

作为数据分析师的求职项目，这个项目处于 **75-80 分位**：

- 认真程度和反思能力明显超过大多数"画个漏斗图 + 写个转化率"的候选人
- 方法论体系完整，能展示从数据到策略的完整链路
- 代码规范和工程意识高于平均水平（测试、配置分离、日志）

**但与顶尖候选人的差距在于**：

1. 数据是模拟的，缺少"在混乱真实数据中找答案"的经历
2. 分析的广度够但深度不足——20 个结论但缺少一两个真正"钻下去"的深度分析
3. 缺少实际业务影响的验证（哪怕是模拟的"如果优化 X，预期提升 Y"）

#### 三个最高优先级的提升事项

**1. 加一个 Cohort 留存分析（1-2 天工作量）**

这是本项目最大的缺失。Cohort 分析能回答"用户来了之后会不会回来"，是漏斗分析的天然延伸。具体实现参考上面 1.3 节的代码草稿。

有了留存分析后，可以和现有发现交叉：
- 哪个渠道不仅转化率高，而且留存好？（真正的优质渠道）
- 新用户的留存曲线和老用户差多少？（首购激活的价值）
- 三年间留存率是否也在下降？（系统性问题的进一步证据）

**2. 写一页 Executive Summary（半天工作量）**

假设你要给 VP of Product 或 CMO 汇报。用半页纸把以下内容讲清楚：

- 核心瓶颈在哪（PDP→Cart）
- 损失有多大（附注估算方法限制）
- 三个最值得做的优化（按优先级）
- 每个优化的预期影响范围
- 需要多少资源和时间

这个文档本身就是面试中的展示亮点——证明你能把复杂分析压缩到决策者能消费的格式。

**3. 修正损失金额计算（1 小时工作量）**

用 transactions 表的单笔 AOV 替代客户级累计值。具体修复方案见上面 P0 问题。

数字会下调 10-20%，但经得起推敲。

#### 面试中的项目讲述结构建议

用 STAR 法则，但更强调"我发现了什么问题→我怎么想的→我做了什么→结果是什么"：

```
S (Situation):
   "这是一个电商用户行为分析项目。200 万条事件，5 张表，覆盖 3 年。"

T (Task):
   "最初的问题是：转化率在下降，但不知道卡在哪个环节。"

A (Action):
   "我做了三件事：
    1. 建了双漏斗（页面覆盖 + 严格路径）来区分'触达问题'和'流转问题'
    2. 发现 PDP→Cart 是全局瓶颈后，按渠道/设备/新老用户分层拆解
    3. 用 PIE 框架量化优先级，输出分渠道的差异化优化策略"

R (Result):
   "核心发现：
    - PDP→Cart 流失 74%，年机会空间约 ¥24M（注：估算值，AOV 修正后）
    - 但 Email/Direct 渠道的瓶颈在结算页，不是 PDP→Cart
    - 新老用户的页面漏斗几乎一样，但行为漏斗差 1.7x——老用户赢在互动深度
    - 三年 CR 下降 53%，但会话量下降 86%，数据完整性存疑"

如果面试官追问细节:
   "在这个过程中，我还发现第一个版本的漏斗定义有问题——
    Home < PLP 的人数倒挂其实是深链流量引起的，不是数据错误。
    所以我补充了严格路径漏斗和深链分析，用来区分真实流失和入口差异。"
```

这段叙述比"我建了一个漏斗，算了转化率"强 10 倍——因为它展示了发现问题 → 深入思考 → 修正方法的完整过程。

---

## 三、附录：逐文件代码走查记录

### python/config.py — 配置管理

**评分：★★★★☆**

优点：
- 所有路径、参数、颜色、阈值集中在 140 行内
- MYSQL_CONFIG 从环境变量读取，有 fallback
- 漏斗阶段定义有中英文对照
- 日志同时输出到控制台和文件

小问题：
- `DURATION_BINS` 和 `DURATION_LABELS` 的注释写的是"GA4 行业标准"，但 GA4 的 engaged session 阈值是 10 秒或 1 次 conversion/2+ pageviews。60/180/420 更像是自定义分桶。已在 [2026-05-18-review-findings.md](2026-05-18-review-findings.md) 中指出并修复。
- `CRO_BENCHMARKS` 和 `STRATEGY_ROI` 中的数字无来源引用。建议注明数据来源或标注为估算值。

---

### python/data_loader.py — 数据加载

**评分：★★★★☆**

优点：
- `load_all_tables()` 统一在加载阶段做 traffic_source 标准化
- `print_data_overview()` 打印关键分布，方便快速了解数据
- `validate_data_integrity()` 检查跨表关联完整性（customer_id/product_id/campaign_id 覆盖率）

小问题：
- 日志输出和 return 语句交织——建议将日志输出与数据返回分离，方便测试
- `traffic_source` 在 load 时做了 `.str.title()` 标准化，但在 cleaning 中又做了一次（[data_cleaning.py:55-58](../../python/data_cleaning.py#L55-L58)）。虽然不会出错，但重复了。两处保留一处即可。

---

### python/data_cleaning.py — 数据清洗与宽表构建

**评分：★★★★☆**

优点：
- 清洗流程清晰（去重→非空→时长异常值→事件类型白名单→标准化）
- 每步有 before/after 日志对比，可追溯
- `build_session_attributes` 使用 mode 聚合类别字段，比 first/last 更稳健
- `build_funnel_wide` 对"购买但无 checkout"做了校验日志
- 用户级 experiment_group 聚合（[data_cleaning.py:107-115](../../python/data_cleaning.py#L107-L115)）已修复

潜在问题：
- `build_funnel_wide` 中 transactions 的 `total_revenue` 为客户级 sum（[data_cleaning.py:173-179](../../python/data_cleaning.py#L173-L179)），这个设计选择会影响后续所有使用该字段的计算（见上文 P0 问题）
- 对 broken transactions（缺失 product_id/revenue）的处理：先用 valid_txn 做 revenue 聚合，再用 all_purchasers 补充 transaction 计数。逻辑正确但嵌套了两层 merge，可读性一般

---

### python/funnel_analysis.py — 核心分析引擎

**评分：★★★★☆**

优点：
- ~1045 行，25+ 个函数，职责分明
- `_dimension_analysis` 作为通用维度分析内部函数，避免了 5 个维度函数的重复代码
- `compute_page_funnel` 使用交叉引用转化率处理多入口场景
- `compute_strict_page_funnel` 使用时间排序实现严格路径
- `compute_deep_link_analysis` 路径分类 + 分渠道对比，有业务深度
- `compute_trend_attribution` Shift-Share 分解实现正确
- `compute_new_vs_returning_funnel` 四象限对比（新/老 × 页面/行为）
- `compute_loss_amount` 已修复级联去重

小问题：
- `compute_churn_features` 的流失特征选择存在循环论证（见上文 P1 问题）
- `compute_pie_priority` 的 Ease 评分硬编码（[funnel_analysis.py:762-768](../../python/funnel_analysis.py#L762-L768)），无数据支持
- `compute_channel_funnels` 返回 `dict[str, pd.DataFrame]`，类型不一致（其他分析函数返回 DataFrame）
- `generate_strategy_brief` 的阈值判断过于简化（CR peak hour 建议"此时段加大投放"），缺少预算约束和边际效益考虑

---

### python/visualization.py — 可视化

**评分：★★★★☆**

优点：
- 16 张图表，覆盖了所有分析维度
- matplotlib + plotly 混用合理（静态用 mpl，交互用 plotly）
- 配色统一，有全局调色板
- 中文字体自动检测 fallback

小问题：
- `_save` 函数同时处理 matplotlib 和 plotly，但耦合在一个函数里。建议分成 `_save_mpl` 和 `_save_plotly`
- 16 张图全部在 main.py 中顺序调用，如果某个图出错会中断后续所有图的生成。建议用 try/except 包裹单个图

---

### python/main.py — 主入口

**评分：★★★★☆**

优点：
- 六阶段结构清晰，注释标注了每个阶段
- `sys.path.insert` 处理了模块导入路径问题

小问题：
- 没有错误处理——如果某阶段出错，整个流程会中断。建议至少在最外层加 try/except
- 没有命令行参数——如果要只跑某几个分析或切换年份，需要改代码

---

### tests/ — 测试

**评分：★★★☆☆**

优点：
- 两个测试文件共 30 个测试用例
- 覆盖了核心的 cleaning 和 analysis 函数
- 测试数据构造合理（`_make_wide_df` 保证了漏斗逻辑一致性）

不足：
- 未测试的函数：`data_loader` 模块全部、`compute_strict_page_funnel`、`compute_deep_link_analysis`、`compute_trend_attribution`、`compute_new_vs_returning_funnel`、`compute_campaign_roas`、`statistical_tests`、`visualization` 模块全部、`import_to_mysql` 模块全部
- 没有集成测试——没有测试"main.py 从头跑到尾"
- 没有测试覆盖报告

---

### sql/ — SQL 脚本

**评分：★★★☆☆**

优点：
- 8 个 SQL 文件，覆盖 DDL/DML/分析/导出
- `08_operational_export.sql` 中的 CTE + 监控 KPI 设计合理

不足：
- SQL 03-07 实际上是 Python 分析的 SQL 翻版，但两者独立维护，存在不一致风险
- `08_operational_export.sql` 中的 session_funnel 是 CTE 而非 VIEW，Python 端无法直接查询（已通过改为从 funnel_wide.csv 导出来规避）
- SQL 脚本无任何注释说明与 Python 版本的关系

---

### docs/ — 文档

**评分：★★★★★**

优点：
- 8 篇文档覆盖了从背景到方法的全部内容
- [04-results.md](../04-results.md) 有 20 个分析章节、清晰的表格、核心结论
- [2026-05-18-review-findings.md](2026-05-18-review-findings.md) 和 [2026-05-20-funnel-critique.md](2026-05-20-funnel-critique.md) 展示了迭代改进过程
- `两个漏斗图的问题.md` 和 `整体建议参考.md` 是外部反馈的完整记录

小问题：
- docs/05 有两个文件（`05-architecture.md` 和 `2026-05-18-review-findings.md`），编号冲突
- 部分文档中的数字可能与最新代码运行结果不一致（修复后未重新运行验证）

---

### powerbi/ — Power BI 报告

**评分：★★★☆☆**

这是一个 PBIR 格式的完整 Power BI 报告，包含 TMDL 语义模型定义和 4 个报表页面。

优点：
- 结构完整，可以直接在 Power BI Desktop 中打开
- 4 个页面（funnel_health / traffic_quality / churn_diagnostics / priority_matrix）与 Python 分析的六个阶段对应
- 12 个视觉对象配置了数据绑定

不足：
- 对于数据分析师岗位，Power BI 报告是锦上添花而非核心
- 数据源绑定需要 MySQL 连接，增加了环境依赖
- 没有截图或预览，面试中难以展示

---

## 修复优先级汇总

| 优先级 | 问题 | 影响 | 工作量 |
|:---:|:---|:---|:---:|
| **P0** | 三年趋势分析归因不严谨 | 核心结论可能错误 | 0.5h |
| **P0** | 损失金额 AOV 基准错误 | 金额数字被高估 | 1h |
| **P1** | 渠道瓶颈定义混淆 | 渠道策略依据不精确 | 0.5h |
| **P1** | 流失特征循环论证 | 诊断结论可信度 | 0.5h（修改措辞） |
| **P1** | 新增 Cohort 留存分析 | 最大分析空白 | 1-2d |
| **P2** | 品类浏览低估 | 品类结论偏倚 | 0.5h（加文档注释） |
| **P2** | Bounce 数据质量未标注 | SQL KPI 矛盾 | 0.5h |
| **P2** | 新增 Cramér's V | 卡方检验补充 | 0.5h |
| **P3** | 写 Executive Summary | 面试展示效果 | 0.5d |
| **P3** | main.py 无错误处理 | 鲁棒性 | 1h |
| **P3** | 测试覆盖率低 | 工程质量 | 1-2d |

---

> **评审结论**：这是一个用心做了迭代和改进的分析项目，双漏斗 + 深链分析 + 新老用户对比的组合已经有了"电商数据分析师应该怎么思考问题"的雏形。当前最大的提升空间不是做更多分析维度，而是把已有的分析做深——修正几个关键计算错误、增加 Cohort 留存、把核心发现压缩到决策者能用的格式。
