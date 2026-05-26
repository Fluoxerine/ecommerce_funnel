# 电商漏斗分析项目 — 多角度综合评审 (DeepSeek)

> 评审日期：2026-05-21 | 评审模型：DeepSeek V4 Pro | 基于全量代码阅读
>
> 评审范围：Python/SQL/测试/文档/Power BI/可视化 | 9 个专业角度

---

## 目录

1. [角度一：数据分析方法论](#角度一数据分析方法论)
2. [角度二：软件工程与代码质量](#角度二软件工程与代码质量)
3. [角度三：统计严谨性](#角度三统计严谨性)
4. [角度四：业务洞察深度](#角度四业务洞察深度)
5. [角度五：可视化与数据沟通](#角度五可视化与数据沟通)
6. [角度六：测试与质量保证](#角度六测试与质量保证)
7. [角度七：文档与可复现性](#角度七文档与可复现性)
8. [角度八：Power BI 实现](#角度八power-bi-实现)
9. [角度九：综合评分卡](#角度九综合评分卡)
10. [优先修复路线图](#优先修复路线图)
11. [附录：各问题详细修复方案](#附录各问题详细修复方案)

---

## 角度一：数据分析方法论

> 视角：资深数据分析师，关注分析逻辑、指标定义、方法选择、结论有效性

### 1.1 做得好的

**漏斗体系的演进是最大亮点。** 从 V1 单一漏斗 → V2 识别倒挂问题 → V3 新增严格路径漏斗 + 深链分析 → V4 新老用户 + 周末对比，这条演进路径完整记录在 [2026-05-20-funnel-critique.md](2026-05-20-funnel-critique.md) 中，本身就是分析能力的证明。

最终形成的三套互补漏斗体系：

| 漏斗类型 | 方法 | 用途 |
|:---|:---|:---|
| 页面覆盖分析 | 各页面独立到达统计（允许多入口/深链） | 衡量页面触达广度 |
| 严格路径漏斗 | Home→PLP→PDP→Cart→Checkout 时间顺序 | 衡量理想路径流转 |
| 行为级漏斗 | view→click→add_to_cart→purchase | 衡量用户意图升级 |

**统计方法选择规范。** [python/funnel_analysis.py](../../python/funnel_analysis.py) 中的方法选择有据可查：

| 方法 | 代码位置 | 评价 |
|:---|:---|:---|
| Welch's t-test + Cohen's d | L661-705 | 不假设方差齐性，Cohen's d 避免大样本 p-hacking |
| 卡方检验 + Bonferroni 校正 | L855-890 | 4 维度 → α=0.0125，正确 |
| Shift-Share 归因分解 | L893-990 | 结构效应 vs 质量效应，方法合理 |
| PIE 优先级矩阵 | L820-848 | WiderFunnel 行业标准 |
| GA4 固定阈值分桶 | config.py L72-78 | 比等频分桶更适合跨周期对比 |

**六阶段闭环结构完整。** `数据探查 → 漏斗建模 → 多维诊断 → 流失根因 → 损失量化 → 策略闭环`，每一阶段都有对应代码、日志和可视化。

### 1.2 需要修正的问题

#### P0-1：损失金额量化存在概念性缺陷

**问题**：[python/funnel_analysis.py:740-817](../../python/funnel_analysis.py#L740-L817) 的 `compute_loss_amount` 使用公式：

```
损失金额 = 流失会话数 × 客单价
```

这隐含假设：**每个流失会话如果不流失，就一定会以客单价完成购买。** 实际上，流失会话的预期转化概率远低于 100%。

**修复方案**：改用"预期增量收入"框架：

```python
# 当前（有问题）
loss_amount = lost_count * aov

# 修复后
expected_conversion_rate = continued_count / reached_count  # 该环节成功转化的会话的转化率
loss_amount = lost_count * expected_conversion_rate * aov
```

或者更保守地使用该环节下游的历史转化率作为预期转化概率。这样估算的损失会更接近真实机会空间。

**预期影响**：当前总损失估算 Y59.76M 可能高估了 2-5 倍，修复后预计在 Y12M-Y30M 范围内。

#### P0-2：PIE 矩阵的 Ease 评分缺乏依据

**问题**：[python/funnel_analysis.py:833-838](../../python/funnel_analysis.py#L833-L838) 中 Ease 是硬编码的固定值：

```python
ease_map = {
    '首页 → 列表页': 7,
    '列表页 → 详情页': 6,
    '详情页 → 购物车': 6,
    '购物车 → 结算页': 8,
}
```

这些值没有基于实际工程评估、历史项目数据或行业基准，直接影响 PIE 优先级排序的可靠性。

**修复方案**：

1. 至少标注 Ease 的假设来源和依据
2. 使用区间估计（如 `[5, 8]`）做敏感性分析，展示 Ease 变化对优先级排序的影响
3. 如果条件允许，基于实际工程团队评估（开发工时、技术难度、依赖项数量）重新打分

#### P1-3：品类漏斗未控制流量规模混杂

**问题**：[python/funnel_analysis.py:511-549](../../python/funnel_analysis.py#L511-L549) 的 `compute_category_funnel` 直接按品类聚合，但不同品类的流量基数差异可能很大。小品类（如会话数 < 100）的转化率估计方差极大，不可靠。

**修复方案**：

```python
# 在 compute_category_funnel 中增加最小样本量过滤和 Wilson 置信区间
from statsmodels.stats.proportion import proportion_confint

def _wilson_ci(success, total, alpha=0.05):
    if total == 0:
        return (0, 0)
    return proportion_confint(success, total, alpha=alpha, method='wilson')

# 过滤小样本品类
cat_stats = cat_stats[cat_stats['浏览会话'] >= 100]

# 增加置信区间
ci_low, ci_upp = [], []
for _, row in cat_stats.iterrows():
    lo, hi = _wilson_ci(int(row['购买会话']), int(row['浏览会话']))
    ci_low.append(round(lo * 100, 2))
    ci_upp.append(round(hi * 100, 2))
cat_stats['转化率_CI下界(%)'] = ci_low
cat_stats['转化率_CI上界(%)'] = ci_upp
```

---

## 角度二：软件工程与代码质量

> 视角：后端工程师，关注代码结构、性能、可维护性、DRY 原则

### 2.1 做得好的

- 模块拆分清晰：`loader → cleaning → analysis → visualization`，职责边界合理
- `_safe_plot` 单图失败不中断的容错设计（[main.py:34-38](../../python/main.py#L34-L38)）
- `_stage_runner` 统一的阶段执行器模式（[main.py:42-54](../../python/main.py#L42-L54)）
- [config.py](../../python/config.py) 集中管理所有常量和路径

### 2.2 需要修正的问题

#### P0-4：main.py 存在大量重复导入

**问题**：[python/main.py](../../python/main.py) 中同一个模块被导入了 3 次：

- 顶部（L10-22）：主 imports
- `_run_stage1_data_exploration` 内部（L58）：重复 `from python.data_loader import ...`
- `_run_stage3_funnel_modeling` 内部（L77-85）：重复 `from python.funnel_analysis import ...`

虽然 Python 的 import 有缓存不会重复加载模块代码，但这表明代码经过多轮修改后结构已经混乱，且增加了维护成本和阅读困惑。

**修复方案**：移除所有 `_run_stage*` 函数内部的 import 语句，统一使用文件顶部的 import。因为这些函数已经在 main.py 的闭包内，可以直接访问顶部的导入。

```python
# 修复前 (_run_stage1_data_exploration)
def _run_stage1_data_exploration(tables):
    from python.data_loader import load_all_tables, print_data_overview, validate_data_integrity  # 删除
    print_data_overview(tables)
    validate_data_integrity(tables)
    return tables

# 修复后
def _run_stage1_data_exploration(tables):
    print_data_overview(tables)
    validate_data_integrity(tables)
    return tables
```

#### P1-5：compute_new_vs_returning_funnel 复制了漏斗计算逻辑

**问题**：[python/funnel_analysis.py:406-424](../../python/funnel_analysis.py#L406-L424) 手动重新实现了交叉到达率计算，与 `compute_page_funnel`（L22-90）中的逻辑完全相同。

**修复方案**：抽取公共函数：

```python
def _compute_page_coverage(df: pd.DataFrame, steps: list[str],
                           labels: list[str]) -> pd.DataFrame:
    """通用页面覆盖分析 — 各页面独立到达 + 交叉到达率"""
    counts = [int(df[col].sum()) for col in steps]
    overlap_counts = []
    for i in range(len(steps) - 1):
        both = int(((df[steps[i]] == 1) & (df[steps[i + 1]] == 1)).sum())
        overlap_counts.append(both)
    rates = [100.0]
    for i in range(1, len(steps)):
        prev = counts[i - 1]
        both = overlap_counts[i - 1]
        rate = min(round(both / prev * 100, 2), 100.0) if prev > 0 else 0.0
        rates.append(rate)
    return pd.DataFrame({
        '漏斗阶段': labels,
        '到达会话数': counts,
        '交叉到达率(%)': rates,
    })
```

然后在 `compute_page_funnel` 和 `compute_new_vs_returning_funnel` 中复用。

#### P1-6：compute_cohort_retention 月差计算有精度问题

**问题**：[python/funnel_analysis.py:1067-1070](../../python/funnel_analysis.py#L1067-L1070)：

```python
purchases['cohort_index'] = (
    purchases['purchase_month'].astype(str).apply(lambda x: pd.Timestamp(x))
    - purchases['cohort_month'].astype(str).apply(lambda x: pd.Timestamp(x))
).dt.days // 30
```

`dt.days // 30` 对于跨月场景会产生错误：
- 1月31日 → 3月1日 = 29天 → `29 // 30 = 0` → 错误地归为 M0
- 正确应为 M+2（跨了 2 个月）

**修复方案**：使用 Period 的月份差：

```python
# 修复后
purchases['cohort_index'] = (
    purchases['purchase_month'].dt.year * 12 + purchases['purchase_month'].dt.month
) - (
    purchases['cohort_month'].dt.year * 12 + purchases['cohort_month'].dt.month
)
```

#### P2-7：build_funnel_wide 中 SET 操作可向量化

**问题**：[python/data_cleaning.py:128-158](../../python/data_cleaning.py#L128-L158) 对每个 page_category 和 event_type 分别做了：

```python
home_sessions = set(events[events['page_category'] == 'Home']['session_id'].unique())
# ... 重复 9 次
```

这导致 events DataFrame 被扫描了 9 次。

**修复方案**：使用 `pd.crosstab` 或一次 `groupby` 批量生成：

```python
# 页面漏斗 — 一次 groupby
page_pivot = pd.crosstab(
    events['session_id'], events['page_category']
).clip(upper=1)
for cat, col_name in [('Home', 'step1_home'), ('PLP', 'step2_plp'),
                       ('PDP', 'step3_pdp'), ('Cart', 'step4_cart'),
                       ('Checkout', 'step5_checkout')]:
    funnel_wide[col_name] = funnel_wide['session_id'].map(
        page_pivot.get(cat, pd.Series(0, index=page_pivot.index))
    ).fillna(0).astype(int)
```

---

## 角度三：统计严谨性

> 视角：统计学家/数据科学家，关注检验选择、多重比较、效应量、因果推断

### 3.1 做得好的

- Welch's t-test + Cohen's d 组合（不假设方差齐性 + 效应量）
- Bonferroni 校正应用于 4 维度卡方检验
- Cramér's V 效应量补充卡方检验
- 代码中 bereits 有数据完整性警示（会话量变化 >30%）

### 3.2 需要修正的问题

#### P0-8：SQL 版卡方检验用的是事件级数据而非会话级数据

**问题**：[sql/06_statistical_tests.sql](../../sql/06_statistical_tests.sql) L10-14：

```sql
SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS converted,
SUM(CASE WHEN event_type != 'purchase' THEN 1 ELSE 0 END) AS not_converted
FROM user_events
```

这统计的是 purchase **事件数**而非购买**会话数**。由于每个会话可能有多条事件，同一会话被重复计数，违反卡方检验的独立性假设。

注意：Python 版本的 `statistical_tests`（[funnel_analysis.py:855-890](../../python/funnel_analysis.py#L855-L890)）使用会话级宽表，无此问题。

**修复方案**：

```sql
-- 修复后：使用会话级聚合
WITH session_conversion AS (
    SELECT
        traffic_source,
        session_id,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS converted
    FROM user_events
    WHERE event_type IN ('view', 'click', 'add_to_cart', 'purchase')
    GROUP BY traffic_source, session_id
)
SELECT
    traffic_source,
    SUM(converted) AS converted_sessions,
    SUM(1 - converted) AS not_converted_sessions,
    ROUND(SUM(converted) / COUNT(*) * 100, 2) AS conversion_rate
FROM session_conversion
GROUP BY traffic_source
ORDER BY conversion_rate DESC;
```

#### P1-9：compute_churn_features 的多重比较未校正

**问题**：[python/funnel_analysis.py:661-705](../../python/funnel_analysis.py#L661-L705) 中执行了 8 个独立的 t 检验（4 环节 × 2 特征），但没有做任何多重比较校正。在 α=0.05 下，8 次检验至少出现一次假阳性的概率为 `1 - (1-0.05)^8 ≈ 34%`。

**修复方案**：对 churn_features 的 p 值也应用 Bonferroni 校正（α/8 = 0.00625），或在结果中显式标注"未校正，假阳性风险约 34%"。推荐方案：

```python
n_tests = len(CHURN_STAGES) * len(features)  # 8
alpha_corrected = 0.05 / n_tests

# 在结果字典中增加字段
results.append({
    ...
    'bonferroni_alpha': round(alpha_corrected, 6),
    'significance_corrected': '***' if p_val < alpha_corrected else 'ns',
})
```

#### P1-10：卡方检验缺少事后两两比较

**问题**：[python/funnel_analysis.py:855-890](../../python/funnel_analysis.py#L855-L890) 的卡方检验只能判断"5 个渠道之间总体存在差异"，无法确定具体哪些渠道对之间差异显著。

**修复方案**：当卡方检验显著时，增加事后两两比较（post-hoc pairwise comparison）。使用 adjusted standardized residuals 或 Marascuilo 程序：

```python
def _posthoc_chisquare(ct: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """卡方事后两两比较 — 基于 adjusted residuals"""
    from itertools import combinations
    from scipy.stats import norm
    
    n = ct.values.sum()
    row_totals = ct.sum(axis=1)
    col_totals = ct.sum(axis=0)
    
    results = []
    pairs = list(combinations(ct.index, 2))
    n_comparisons = len(pairs)
    alpha_corrected = alpha / n_comparisons
    z_crit = norm.ppf(1 - alpha_corrected / 2)
    
    for r1, r2 in pairs:
        # 对每个列水平做两两比较
        for col in ct.columns:
            p1 = ct.loc[r1, col] / row_totals[r1]
            p2 = ct.loc[r2, col] / row_totals[r2]
            p_pool = (ct.loc[r1, col] + ct.loc[r2, col]) / (row_totals[r1] + row_totals[r2])
            se = np.sqrt(p_pool * (1 - p_pool) * (1/row_totals[r1] + 1/row_totals[r2]))
            z = (p1 - p2) / se if se > 0 else 0
            sig = '***' if abs(z) > z_crit else 'ns'
            results.append({
                '对比': f'{r1} vs {r2}',
                '列': col,
                'p1': round(p1, 4),
                'p2': round(p2, 4),
                'z': round(z, 2),
                '显著性': sig,
            })
    return pd.DataFrame(results)
```

#### P2-11：Cohen's d 存在同义反复风险

**问题**：[python/funnel_analysis.py:663-667](../../python/funnel_analysis.py#L663-L667) 的注释已经承认了这个问题：

> event_count 和 total_duration_sec 的部分差异反映了"完成更多漏斗步骤"的自然结果 (tautology)

**修复方案**：

短期方案：在分析时控制已完成的漏斗步骤数。例如在比较"PDP→Cart 流失组 vs 转化组"的 event_count 时，只统计到达 PDP 之前的事件数。

长期方案：建议在数据埋点层面增加不受漏斗进度污染的独立行为特征，如：
- 搜索使用次数
- 评价/评论查看次数
- 商品对比次数
- 客服咨询次数

这些特征的差异才是真正可操作的洞察。

---

## 角度四：业务洞察深度

> 视角：业务分析师/策略顾问，关注可执行性、ROI、成本收益、竞品对标

### 4.1 做得好的

- PIE 矩阵提供了清晰的优化优先级排序
- 渠道差异化策略（[cro_strategy.md](../../operations/cro_strategy.md)）针对每个渠道的特定瓶颈给出了专项建议
- 策略摘要自动生成（[funnel_analysis.py:1162-1198](../../python/funnel_analysis.py#L1162-L1198)）体现了"分析要能落地"的意识
- 监控指标体系完整（会话转化率、PDP→Cart、退款率、快速跳出率等）

### 4.2 需要修正的问题

#### P0-12：CRO 策略缺乏实施成本估算

**问题**：[cro_strategy.md](../../operations/cro_strategy.md) 给出了详细的优化建议和预期效果（如"预期挽回 Y3.0M-5.0M/年"），但完全没有估算实施成本：

- 开发人力（前端/后端/设计 人天）
- A/B 测试平台成本
- 机会成本（占用开发资源期间的其他需求延迟）
- 维护成本

没有成本数据，ROI（Return on Investment）计算就不完整，策略优先级排序缺乏财务说服力。

**修复方案**：为每个策略增加成本估算表：

| 策略 | 预期年收益 | 实施成本估算 | ROI | 回本周期 |
|:---|:---|:---|:---|:---|
| PDP 改版 | Y3.0M-5.0M | 2人月 FE + 1人月 BE ≈ Y150K | 20x-33x | ~1月 |
| 购物车优化 | Y300K-600K | 1人月 FE ≈ Y50K | 6x-12x | ~2月 |
| 结算页优化 | Y400K-800K | 1.5人月 FE ≈ Y75K | 5x-11x | ~2.5月 |

#### P0-13：损失金额缺乏置信区间

**问题**：[python/funnel_analysis.py:740-817](../../python/funnel_analysis.py#L740-L817) 的损失计算只输出点估计（Y59,760,920）。考虑到：
- 客单价有方差（不同品类、渠道差异大）
- 流失会话的预期转化率本身有不确定性

点估计会给业务方造成"精确值"的错觉，可能被错误引用。

**修复方案**：增加 Bootstrap 置信区间：

```python
def _bootstrap_loss_ci(funnel_wide, aov, n_bootstrap=1000, ci=95):
    """Bootstrap 损失金额置信区间"""
    estimates = []
    n = len(funnel_wide)
    rng = np.random.default_rng(42)
    for _ in range(n_bootstrap):
        sample = funnel_wide.iloc[rng.integers(0, n, n)]
        # 重新计算各环节流失...
        estimates.append(total_loss)
    lo = np.percentile(estimates, (100 - ci) / 2)
    hi = np.percentile(estimates, 100 - (100 - ci) / 2)
    return lo, hi
```

在日志和文档中输出：`年估算损失: Y24.5M (95% CI: Y18.2M - Y32.1M)`

#### P1-14：行业基准未被积极用于分析

**问题**：[python/config.py:85-97](../../python/config.py#L85-L97) 已经定义了行业基准（`CRO_BENCHMARKS`）：

```python
'avg_pdp_to_cart': 10.0,     # 行业典型值 10%
'avg_cart_to_checkout': 25.0, # 行业典型值 25%
```

但代码中没有将项目实际数据与这些基准做对比。

项目的 PDP→Cart 交叉到达率 25.81%，远高于行业典型值 10%——这实际上是一个**正向发现**，说明项目的数据集或定义与行业基准不完全可比（交叉到达率 ≠ 顺序转化率），或者该平台的体验确实优于行业均值。无论哪种情况，都值得在分析中讨论。

**修复方案**：在 `compute_page_funnel` 或策略摘要中增加行业对标输出：

```python
# 在 generate_strategy_brief 中增加
benchmarks = CRO_BENCHMARKS
if 'avg_pdp_to_cart' in benchmarks:
    comparison = funnel_df.loc[funnel_df['漏斗阶段'] == '3.商品详情页', '交叉到达率(%)'].values[0]
    brief.append(
        f"行业对标: PDP→购物车交叉到达率 {comparison:.1f}% "
        f"(行业典型值 {benchmarks['avg_pdp_to_cart']}% — 注意口径差异: 本项目为交叉到达率, 行业为顺序转化率)"
    )
```

#### P1-15：策略建议缺乏速赢分析

**问题**：PIE 矩阵给出了优先级排序，但实际资源分配往往面临 trade-off：
- P0 详情页改版虽然潜力最大但周期长（预估 4 周+）
- P3 购物车优化虽然损失小但实施快（可能 1 周内上线）

业务方通常需要速赢（Quick Win）来证明 CRO 项目的价值。

**修复方案**：增加一个"速赢矩阵"：

| 策略 | 预期年化收益 | 实施难度 | 上线周期 | 速赢评分 |
|:---|:---|:---|:---|:---|
| Guest Checkout 一键结算 | Y1.5M-3.0M | 低 | 1-2周 | ⭐⭐⭐⭐⭐ |
| 免运费进度条 | Y800K-1.5M | 低 | 1-2周 | ⭐⭐⭐⭐ |
| 加购按钮固定底栏 | Y2.0M-4.0M | 中 | 2-4周 | ⭐⭐⭐⭐ |
| PDP 个性化推荐 | Y3.0M-5.0M | 高 | 4-8周 | ⭐⭐⭐ |
| SEO 商品详情页优化 | Y2.0M-3.5M | 中 | 4-8周 | ⭐⭐⭐ |

---

## 角度五：可视化与数据沟通

> 视角：数据可视化专家，关注图表设计、配色、可访问性、信息层次

### 5.1 做得好的

- 图表类型多样：漏斗图、瀑布图、热力图、气泡图、趋势图、分组柱状图
- 中文字体自动检测和回退机制（[visualization.py:14-26](../../python/visualization.py#L14-L26)）
- 瓶颈环节视觉突出（深色柱 vs 浅色柱）
- 损失瀑布图（[visualization.py:286-364](../../python/visualization.py#L286-L364)）的级联累积设计能清晰展示损失构成

### 5.2 需要修正的问题

#### P1-16：混合输出格式导致体验割裂

**问题**：16 张图表中，2 张是 Plotly HTML（交互式），14 张是 matplotlib PNG（静态）。需要同时打开浏览器和图片查看器来查看全部结果。

**修复方案**：

方案 A（推荐）：全部改为 Plotly HTML，统一交互体验。Plotly 支持 `write_image()` 同时导出 PNG。

方案 B：全部改为 matplotlib PNG，确保离线可查看。

方案 C：保持混合，但在 README 中明确标注哪些是 HTML、哪些是 PNG，并提供一键打开所有图表的脚本。

#### P1-17：配色方案缺乏无障碍设计

**问题**：[visualization.py](visualization.py) 中大量使用红绿色区分：
- `C_RED = '#D64545'` vs `C_GREEN = '#4CAF82'`
- 损失瀑布图使用红色系（#e8xx, #78xx 等）

约 8% 的男性用户有红绿色盲，无法区分这些颜色编码。

**修复方案**：使用 colorblind-friendly 配色方案：

```python
# 色盲友好配色 (来源: Wong, 2011 - Nature Methods)
CB_BLUE   = '#0072B2'  # 蓝
CB_ORANGE = '#E69F00'  # 橙
CB_GREEN  = '#009E73'  # 蓝绿 (非红绿)
CB_RED    = '#CC79A7'  # 紫红
CB_CYAN   = '#56B4E9'  # 浅蓝
CB_YELLOW = '#F0E442'  # 黄

# 替代方案：使用 viridis/magma/plasma 等 perceptually uniform colormap
```

#### P1-18：图表缺少元信息标注

**问题**：所有图表都没有标注数据来源、分析日期、样本量等元信息。阅读者无法判断图表的时效性和数据范围。

**修复方案**：在每张图右下角添加小字标注：

```python
def _add_metadata_annotation(fig, ax=None, n_sessions=None, date=None):
    """在图角添加元信息"""
    meta_text = f"数据: 2021-2023"
    if n_sessions:
        meta_text += f", N={n_sessions:,} sessions"
    if date:
        meta_text += f" | 分析: {date}"
    else:
        meta_text += f" | 分析: {datetime.now().strftime('%Y-%m-%d')}"
    
    if ax:
        ax.text(0.99, -0.08, meta_text, transform=ax.transAxes,
                ha='right', fontsize=7, color='#999999')
    # Plotly 版本用 fig.add_annotation()
```

#### P2-19：PIE 矩阵图信息密度过高

**问题**：[visualization.py:565-603](../../python/visualization.py#L565-L603) 的气泡图同时编码了 4 个维度：
- x = Potential（损失潜力）
- y = Importance（流量重要性）
- 气泡大小 = PIE 得分
- 颜色 = Ease（优化容易度）

加上每个气泡旁边还有 "#1 详情页→购物车 PIE=336" 等文字标注，阅读负担较重。

**修复方案**：拆分为两张互补的图：
- 图 A：Potential × Importance 气泡图（大小 = PIE，颜色 = Ease）
- 图 B：Ease × Impact 条形图（横轴 = PIE 得分，颜色 = Ease 等级）

---

## 角度六：测试与质量保证

> 视角：QA 工程师，关注测试覆盖、边界条件、回归测试、测试数据质量

### 6.1 做得好的

- 三层测试结构：单元测试（test_data_cleaning.py, test_funnel_analysis.py）+ 集成测试（test_integration.py）
- 边界条件测试存在（空 DataFrame 处理、无 transactions 的损失计算）
- 测试了漏斗逻辑一致性（购买必有 checkout、转化率 ≤ 100%）
- `_safe_plot` 和 `_stage_runner` 的异常处理有测试覆盖

### 6.2 需要修正的问题

#### P1-20：测试数据不反映真实数据分布

**问题**：[tests/test_funnel_analysis.py](../../tests/test_funnel_analysis.py) 中 `_make_wide_df` 使用均匀随机分布生成数据：

```python
'traffic_source': np.random.choice(['Organic', 'Paid Search', 'Social', 'Email', 'Direct'], n)
```

但真实数据中 Organic 占 47% 流量，Social 仅占 6.9%。使用均匀分布意味着测试永远覆盖不到某些真实场景（如"某个小渠道的转化率异常高/低"）。

**修复方案**：在测试数据中使用真实数据的分布参数：

```python
'traffic_source': np.random.choice(
    ['Organic', 'Paid Search', 'Social', 'Email', 'Direct'],
    n,
    p=[0.47, 0.13, 0.07, 0.18, 0.15]  # 基于真实分布
)
```

#### P1-21：缺少关键边界条件的测试

**问题**：以下场景没有测试覆盖：

| 场景 | 风险 | 建议测试 |
|:---|:---|:---|
| 全部会话都没有购买 | 除以零、空结果 | `test_all_zero_purchase` |
| 单一渠道（如只有 Organic） | 卡方检验退化 | `test_single_channel` |
| AOV = 0（全部退款场景） | 损失金额为 0 是否合理 | `test_zero_aov` |
| 跨年度 cohort（2021-12 → 2022-01） | 月差计算边界 | `test_cohort_cross_year` |
| 负收入（退款 > 购买） | 已在代码中有 warning | `test_negative_revenue` |

**修复方案**：

```python
def test_all_zero_purchase():
    """全部会话均未购买时的行为"""
    wide = _make_wide_df(100)
    wide['step_purchase'] = 0
    wide['step5_checkout'] = 0
    # 各分析函数应返回合理结果而非崩溃
    loss = compute_loss_amount(wide)
    page = compute_page_funnel(wide)
    # 断言正确性...

def test_single_channel():
    """只有单一渠道时的卡方检验"""
    wide = _make_wide_df(100)
    wide['traffic_source'] = 'Organic'
    result = statistical_tests(wide)  # 不应崩溃
    assert result['traffic_source']['sig'] == 'not significant'
```

#### P1-22：缺少回归测试的黄金数据集

**问题**：当前测试每次生成随机数据，无法检测代码修改是否改变了分析结果。如果某次重构不小心改变了漏斗计算公式，随机数据测试无法发现。

**修复方案**：

1. 存储一个小型黄金数据集（如 1000 行 events 的 CSV）在 `tests/fixtures/` 下
2. 对该数据集运行完整分析流程
3. 断言关键指标在可接受范围内不变：

```python
def test_golden_dataset_regression():
    """黄金数据集回归测试 — 关键指标不得漂移"""
    events = pd.read_csv('tests/fixtures/golden_events.csv')
    # ... 运行完整分析流程 ...
    
    # 关键指标断言 (允许 ±0.5% 的浮点误差)
    assert abs(snapshot['session_conversion_rate'] - 15.08) < 0.5
    assert snapshot['total_sessions'] == 633450
    
    # 漏斗瓶颈断言
    page_funnel = compute_page_funnel(funnel_wide)
    bottleneck = page_funnel.iloc[page_funnel[1:]['交叉到达率(%)'].idxmin()]
    assert '详情页' in bottleneck['漏斗阶段']  # 瓶颈必须一致
```

#### P2-23：test_integration.py 验证了"不报错"但未验证"算对了"

**问题**：[tests/test_integration.py](../../tests/test_integration.py) 的 `test_funnel_wide_logic` 构造了 10/100 会话有购买的数据，但只验证了：
- `len(page_funnel) == 5`
- `len(event_funnel) == 4`
- `pie['PIE得分'].notna().all()`

没有验证购买会话数确实为 10、转化率确实为 10%。

**修复方案**：

```python
def test_funnel_wide_logic(self):
    # ... 构造数据 (前 10 个有购买) ...
    
    # 验证具体数值而不只是"不报错"
    page_funnel = compute_page_funnel(wide)
    event_funnel = compute_event_funnel(wide)
    
    assert event_funnel[event_funnel['漏斗阶段'] == '购买']['会话数'].values[0] == 10
    assert abs(event_funnel[event_funnel['漏斗阶段'] == '购买']['整体转化率(%)'].values[0] - 10.0) < 0.01
    
    # 验证交叉到达率不超过 100%
    for i in range(1, len(page_funnel)):
        assert page_funnel.iloc[i]['交叉到达率(%)'] <= 100.0
```

---

## 角度七：文档与可复现性

> 视角：研究员/学术评审，关注可复现性、文档完整性、数据溯源

### 7.1 做得好的

- 文档体系完整：背景 → 数据字典 → 方法论 → 结果 → 架构 → 审查 → 策略
- 多轮自我审查记录（05/06/07 三份 review 文档）
- 方法论文档（[03-methodology.md](../03-methodology.md)）引用了行业标准和参考文献

### 7.2 需要修正的问题

#### P0-24：结果不可一键复现

**问题**：README 说 `python python/main.py` 即可运行，但：

- 没有说明需要先在 `data/` 目录下放置 5 个 CSV 文件
- 没有说明 CSV 文件的预期格式和字段
- 没有说明如果 CSV 不存在会报什么错
- 没有说明预期运行时间
- 没有说明预期输出内容清单

**修复方案**：在 README 增加"运行前检查清单"：

```markdown
## 运行前检查

1. 确认 `data/` 目录下存在以下 5 个文件：
   - `events.csv` (约 200MB, 2,000,000 行)
   - `transactions.csv` (约 5MB, 103,127 行)
   - `customers.csv` (约 8MB, 100,000 行)
   - `products.csv` (约 200KB, 2,000 行)
   - `campaigns.csv` (约 5KB, 50 行)

2. 安装依赖: `pip install -r requirements.txt`

3. (可选) 配置 MySQL: 复制 `.env.example` 为 `.env` 并填写密码

4. 运行分析: `python python/main.py` (预期耗时 3-5 分钟)

5. 预期生成:
   - `output/charts/` 下 16 张图表
   - `output/funnel_wide.csv` 漏斗宽表
   - `output/cleaned_events.csv` 清洗后事件表
   - `output/baseline_snapshot.json` 基准快照
   - `output/analysis.log` 分析日志
```

#### P1-25：文档版本同步问题

**问题**：[04-results.md](../04-results.md) 中的数值来自某次特定运行，但文档中没有标注：
- 代码版本（git commit hash）
- 运行时间
- 参数配置（如使用默认 AOV 还是 transactions 表 AOV）

**修复方案**：在文档头部增加运行元信息块：

```markdown
> **运行元信息**
> - 代码版本: `dcf44b7` (2026-05-20)
> - 运行时间: 2026-05-20 18:30 CST
> - 数据范围: 2021-01 ~ 2023-12
> - 总会话数: 633,450
> - AOV 来源: transactions 表单笔均值 (Y100.25)
```

可以从 `baseline_snapshot.json` 中自动提取这些信息并注入文档。

#### P2-26：多处文档存在重复内容

**问题**：以下文档包含相同的核心数据表格：
- `docs/04-results.md` — 漏斗数据、渠道对比
- `2026-05-20-funnel-critique.md` — 验证讨论中重复引用
- `docs/07-dual-perspective-review.md` — 评审中重复引用

当数据更新时，需要同时修改多处，容易遗漏。

**修复方案**：使用 `docs/_includes/` 目录存放共享数据片段，文档通过引用方式包含：

```
docs/
├── _includes/
│   ├── page_funnel_table.md      # 页面漏斗数据
│   ├── event_funnel_table.md     # 行为漏斗数据
│   ├── channel_comparison.md     # 渠道对比数据
│   └── key_metrics.md            # 核心 KPI
├── 04-results.md                 # 引用 _includes/
├── 06-funnel-critique.md         # 引用 _includes/
└── 07-dual-perspective-review.md # 引用 _includes/
```

---

## 角度八：Power BI 实现

> 视角：BI 工程师，关注数据模型、度量值、报告设计、性能

### 8.1 做得好的

- 完整的 PBIR 格式（`definition.pbir` + `definition/pages/` + `definition/` 结构）
- TMDL 格式的语义模型（易于版本控制和 diff）
- 独立的 `loss_data` 表用于损失量化和 PIE 矩阵
- 数据模型有明确的表间关系定义（relationships.tmdl）

### 8.2 需要修正的问题

#### P1-27：Power BI 数据源只导出了数据子集

**问题**：[python/import_to_mysql.py:148-181](../../python/import_to_mysql.py#L148-L181)：

```python
overview = fw[...].head(10000)      # 只导出前 10,000 行
fw.head(50000).to_csv(...)          # 只导出前 50,000 行
```

对于 633,450 个会话的完整数据，`funnel_overview.csv` 仅包含 1.6% 的数据，`funnel_wide_export.csv` 仅包含 7.9% 的数据。

更严重的是，`head()` 取的是前 N 行而非随机抽样——如果数据有某种排序（如按时间），则 Power BI 报告中看到的可能只是 2021 年初的数据。

**修复方案**：

```python
# 方案 A: 随机抽样
overview = fw[core_cols].sample(n=min(50000, len(fw)), random_state=42)

# 方案 B: 分层抽样 (按年份/渠道保持分布)
overview = fw.groupby(['year', 'traffic_source'], group_keys=False).apply(
    lambda x: x.sample(n=max(1, int(len(x) * 0.1)), random_state=42)
)

# 方案 C: 导出聚合数据替代明细数据
# channel_analysis, device_analysis, country_analysis 已经是聚合数据，可以直接使用
```

同时在文档（[HOWTO.md](../../powerbi/HOWTO.md)）中明确标注数据范围和不完整说明。

#### P1-28：语义模型缺少预定义 DAX 度量值

**问题**：查看 [model.tmdl](powerbi/funnel_report/Ecommerce%20Funnel%20CRO.SemanticModel/definition/model.tmdl) 和各个表的 `.tmdl` 文件，模型中缺少预定义的 DAX 度量值。这意味着每个 Power BI 用户都需要自己编写 DAX 来计算基础指标。

**修复方案**：在 TMDL 模型中预定义以下核心度量值：

```dax
-- Total Sessions
Total Sessions = DISTINCTCOUNT('funnel_wide_export'[session_id])

-- Conversion Rate
Session CR = 
    DIVIDE(
        CALCULATE(DISTINCTCOUNT('funnel_wide_export'[session_id]), 'funnel_wide_export'[step_purchase] = 1),
        DISTINCTCOUNT('funnel_wide_export'[session_id])
    )

-- MoM Change
CR MoM Change = 
    VAR CurrentCR = [Session CR]
    VAR PrevMonthCR = CALCULATE([Session CR], PREVIOUSMONTH('Calendar'[Date]))
    RETURN DIVIDE(CurrentCR - PrevMonthCR, PrevMonthCR)

-- PIE Score (用于 Priority Matrix 页)
PIE Score = 
    VAR P = [Loss Potential Score]
    VAR I = [Traffic Importance Score]
    VAR E = [Ease of Implementation]
    RETURN P * I * E
```

#### P2-29：Power BI 报告页面覆盖不完整

**问题**：4 个页面 vs Python 端的 16 张图表 + 6 个分析阶段：

| Python 分析 | Power BI 对应 | 状态 |
|:---|:---|:---|
| 月度趋势 (chart 07) | 无 | 缺失 |
| 新老用户漏斗 (chart 14) | 无 | 缺失 |
| 周末对比 (chart 15) | 无 | 缺失 |
| Cohort 留存 (chart 16) | 无 | 缺失 |
| 品类漏斗 (chart 11) | 无 | 缺失 |
| 深链分析 (chart 13) | 无 | 缺失 |

**修复方案**：至少增加以下页面：
- **趋势监控页**：月度转化率趋势 + 年度均值线 + 同比变化
- **用户分层页**：新老用户漏斗对比 + 忠诚度转化率 + Cohort 留存热力图

---

## 角度九：综合评分卡

| 维度 | 评分 | 关键优势 | 关键短板 |
|:---|:---:|:---|:---|
| 数据分析方法论 | ⭐⭐⭐⭐ | 三套漏斗体系互补、统计方法选择规范、闭环完整 | 损失量化概念缺陷、PIE Ease 无依据、趋势归因因果链不完整 |
| 软件工程质量 | ⭐⭐⭐ | 模块拆分清晰、容错设计到位 | main.py 重复导入、逻辑复制粘贴、SET 操作低效 |
| 统计严谨性 | ⭐⭐⭐⭐ | Welch+Cohen+Bonferroni 组合使用规范 | 多重比较不完整、SQL 版事件级vs会话级混淆、缺事后两两比较 |
| 业务洞察深度 | ⭐⭐⭐½ | PIE 优先级排序、渠道差异化策略、监控指标体系 | 缺成本估算、缺置信区间、缺少与行业基准的积极对标 |
| 可视化与沟通 | ⭐⭐⭐½ | 图表类型多样、瓶颈视觉突出、中文字体适配 | 格式不统一(HTML+PNG混用)、缺无障碍设计、缺元信息标注 |
| 测试与QA | ⭐⭐⭐ | 三层测试结构、边界条件测试存在 | 测试数据不反映真实分布、缺黄金数据集回归测试、验证"不报错"而非"算对了" |
| 文档与可复现性 | ⭐⭐⭐½ | 文档体系完整、多轮迭代记录、方法论引用了行业标准 | 不可一键复现、文档版本不同步、多处重复内容 |
| Power BI 实现 | ⭐⭐⭐ | 完整 PBIR 结构、TMDL 语义模型、独立 loss_data 表 | 数据子集导出(仅1.6%-7.9%)、缺预定义度量值、报告页面覆盖不完整 |
| **综合** | **⭐⭐⭐½** | 分析思考的深度 > 工程实现的成熟度 | 从"好的分析项目"到"企业级分析产品"之间还有工程化差距 |

---

## 优先修复路线图

### 本周立即修复 (P0)

| # | 问题 | 文件 | 预估工时 |
|:---|:---|:---|:---:|
| P0-1 | 损失金额公式改为预期增量收入框架 | funnel_analysis.py:740-817 | 1h |
| P0-2 | PIE Ease 标注假设来源 | funnel_analysis.py:833-838 | 0.5h |
| P0-4 | 移除 main.py 函数内部重复 import | main.py:58,77-85 | 0.5h |
| P0-8 | SQL 卡方检验改为会话级聚合 | sql/06_statistical_tests.sql | 0.5h |
| P0-12 | CRO 策略增加实施成本估算 | operations/cro_strategy.md | 1h |
| P0-13 | 损失金额增加 Bootstrap 置信区间 | funnel_analysis.py:740-817 | 1.5h |
| P0-24 | README 增加运行前检查清单 | README.md | 0.5h |

### 本月修复 (P1)

| # | 问题 | 文件 | 预估工时 |
|:---|:---|:---|:---:|
| P1-3 | 品类漏斗增加 Wilson 置信区间 | funnel_analysis.py:511-549 | 1h |
| P1-5 | 抽取公共 `_compute_page_coverage` 函数 | funnel_analysis.py | 1h |
| P1-6 | Cohort 月差计算改用 Period 差值 | funnel_analysis.py:1067-1070 | 0.5h |
| P1-9 | churn_features 增加多重比较校正 | funnel_analysis.py:661-705 | 0.5h |
| P1-10 | 卡方检验增加事后两两比较 | funnel_analysis.py:855-890 | 2h |
| P1-14 | 增加行业基准对标输出 | funnel_analysis.py:1162-1198 | 1h |
| P1-15 | 增加速赢矩阵 | operations/cro_strategy.md | 1h |
| P1-16 | 统一图表输出格式 | visualization.py | 2h |
| P1-17 | 配色改为无障碍方案 | visualization.py | 1.5h |
| P1-18 | 图表增加元信息标注 | visualization.py | 1h |
| P1-20 | 测试数据使用真实分布 | tests/*.py | 0.5h |
| P1-21 | 增加关键边界条件测试 | tests/*.py | 2h |
| P1-22 | 建立黄金数据集回归测试 | tests/ + tests/fixtures/ | 2h |
| P1-25 | 文档增加运行元信息块 | docs/04-results.md | 0.5h |
| P1-27 | Power BI 数据导出改为分层抽样 | import_to_mysql.py | 1h |
| P1-28 | TMDL 模型增加预定义 DAX 度量值 | *.tmdl | 2h |

### 择机优化 (P2)

| # | 问题 | 文件 | 预估工时 |
|:---|:---|:---|:---:|
| P2-7 | build_funnel_wide SET 操作向量化 | data_cleaning.py:128-158 | 2h |
| P2-11 | Cohen's d 控制漏斗步骤数 | funnel_analysis.py:661-705 | 1.5h |
| P2-19 | PIE 矩阵图拆分 | visualization.py:565-603 | 1h |
| P2-23 | test_integration 验证具体数值 | tests/test_integration.py | 1h |
| P2-26 | 文档去重，建立 _includes/ | docs/ | 1.5h |
| P2-29 | Power BI 增加趋势页+用户分层页 | powerbi/ PBIR | 3h |

---

## 附录：各问题详细修复方案

### 附录 A：损失金额概念修复（P0-1）

当前代码（[funnel_analysis.py:740-817](../../python/funnel_analysis.py#L740-L817)）：

```python
loss_amount = lost_count * aov
```

修复后：

```python
def compute_loss_amount(funnel_wide: pd.DataFrame,
                        transactions: pd.DataFrame | None = None) -> pd.DataFrame:
    # ... (AOV 计算保持不变) ...

    stage_pairs = [
        ('首页 → 列表页', 'step1_home', 'step2_plp'),
        ('列表页 → 详情页', 'step2_plp', 'step3_pdp'),
        ('详情页 → 购物车', 'step3_pdp', 'step4_cart'),
        ('购物车 → 结算页', 'step4_cart', 'step5_checkout'),
    ]

    losses = []
    cumulative_lost = set()

    for label, stage_col, next_col in stage_pairs:
        reached = set(
            funnel_wide[funnel_wide[stage_col] == 1]['session_id'].unique()
        ) - cumulative_lost
        continued = set(
            funnel_wide[funnel_wide[next_col] == 1]['session_id'].unique()
        ) - cumulative_lost
        lost_sessions = reached - continued
        cumulative_lost |= lost_sessions

        reached_count = len(reached)
        lost_count = len(lost_sessions)
        loss_rate = round(lost_count / reached_count * 100, 2) if reached_count > 0 else 0

        # === 修复核心 ===
        # 不使用 lost_count * aov
        # 改用：流失会话数 × 该环节下游预期转化概率 × 客单价
        # 预期转化概率 = continued / reached（即该环节成功转化的比例）
        expected_cr = continued / reached if reached > 0 else 0
        expected_lost_revenue = lost_count * expected_cr * aov
        # =================

        losses.append({
            '漏斗环节': label,
            '流失会话数': lost_count,
            '入环节会话数': reached_count,
            '环节流失率(%)': loss_rate,
            '客单价': round(aov, 2),
            '预期转化概率': round(expected_cr, 4),
            '估算损失金额': round(expected_lost_revenue, 2),
        })

    loss_df = pd.DataFrame(losses)
    # ... (后续不变) ...
    return loss_df
```

### 附录 B：Bootstrap 置信区间（P0-13）

```python
def _compute_loss_with_bootstrap(funnel_wide, aov, stage_pairs,
                                  n_bootstrap=1000, ci=95, seed=42):
    """带 Bootstrap 置信区间的损失估算"""
    rng = np.random.default_rng(seed)
    n = len(funnel_wide)
    bootstrap_losses = []

    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, n)
        sample = funnel_wide.iloc[idx]
        # 重新计算各环节流失... (复用 compute_loss_amount 的核心逻辑)
        total = sum(stage_losses)
        bootstrap_losses.append(total)

    lo = np.percentile(bootstrap_losses, (100 - ci) / 2)
    hi = np.percentile(bootstrap_losses, 100 - (100 - ci) / 2)
    median = np.median(bootstrap_losses)
    return median, lo, hi
```

在日志中输出：

```
估算总损失: Y24.5M (95% CI: Y18.2M - Y32.1M, Bootstrap N=1000)
```

### 附录 C：无障碍配色方案（P1-17）

```python
# 替换 visualization.py 中的颜色常量
# 来源: Wong, B. (2011) "Points of view: Color blindness"
#       Nature Methods 8, 441. doi:10.1038/nmeth.1618

# 色盲友好配色 (蓝-橙-绿-粉-青-黄)
CB_PALETTE = [
    '#0072B2',  # 蓝 — 替代原红色作为主强调色
    '#E69F00',  # 橙 — 替代原绿色
    '#009E73',  # 蓝绿 — 替代原红色用作正向指标
    '#CC79A7',  # 紫粉 — 替代原橙色
    '#56B4E9',  # 青
    '#F0E442',  # 黄
]

# 渐变 colormap 使用 viridis (perceptually uniform)
from matplotlib.cm import viridis, magma

# 替代原来的红绿自定义 colormap
# custom_cmap = LinearSegmentedColormap.from_list(...)  # 删除
im = ax.imshow(data, cmap='viridis', aspect='auto', vmin=vmin, vmax=vmax)
```

---

> **评审总结**：这个项目在分析思考的深度上已经超过了多数同类项目——三套漏斗体系互补、多轮自我审查迭代、统计方法选择有据可查——这些都是真正的分析能力的体现。主要短板在工程实践（重复代码、低效操作）和业务沟通（损失数字缺乏区间估计、策略缺乏成本收益分析）两个层面，这也是从"好的分析项目"到"企业级分析产品"之间需要跨越的鸿沟。
>
> 建议按照上述优先修复路线图逐步改进，预计 P0 项约 5.5 工时可在本周内完成，P1 项约 21.5 工时可在一个月内分批完成。
