# 电商漏斗与转化率优化（CRO）分析项目 — 全面评审报告

> 评审日期：2026-05-21
> 评审视角：数据工程 · 统计分析 · 业务分析逻辑 · 可视化 · 代码工程 · 文档可维护性 · 数据质量
> 数据规模：2,205,177 条记录 / 633,450 个会话 / 3 年数据

---

## 一、数据工程层面

### 1.1 优点

- 五表关联建模完整，ER 图清晰（`events ↔ customers ↔ products ↔ campaigns ↔ transactions`）
- 清晰区分了 `page_category` 漏斗（页面覆盖）和 `event_type` 漏斗（行为级），避免口径混淆
- 深链识别逻辑正确：`has_plp & ~has_home`（深链直达）vs `has_home & has_plp`（首页路径）
- 五表关联完整性验证（data_loader.py）有专门的 `validate_data_integrity()` 函数

### 1.2 问题与建议

#### 问题 1.2.1：`transactions` 表无法直接关联到 session

**位置**：[data_cleaning.py:172-191](../../python/data_cleaning.py#L172-L191)

**描述**：`transactions` 表无 `session_id` 字段，只能聚合到 `customer_id` 再关联到 `funnel_wide`（会话粒度），导致：
- 一位用户多次购买产生的收入无法精确归属到特定会话的流量来源
- 同一客户在多个渠道的会话中产生了"收入归因模糊"问题

**解决方案**：
```sql
-- 在 transactions 表增加 session_id 字段
ALTER TABLE transactions ADD COLUMN session_id VARCHAR(64);

-- 关联时按 session_id 精确归因
SELECT
    ue.session_id,
    ue.traffic_source,
    SUM(t.gross_revenue) AS session_revenue
FROM user_events ue
JOIN transactions t ON t.customer_id = ue.customer_id
GROUP BY ue.session_id, ue.traffic_source;
```

#### 问题 1.2.2：品类漏斗的 product_id 缺失问题

**位置**：[04-results.md:194](docs/04-results.md#L194)（文档已承认）

**描述**："浏览会话"的统计仅包含有点击商品详情（`product_id` 非空）的事件，首页浏览和 PLP 列表页浏览无法关联品类。这导致：
- 品类"浏览会话"数被低估
- 浏览→加购转化率系统性偏高（分母偏小）

**解决方案**：在 `compute_category_funnel` 中添加说明注释，并建立 PLP 层面品类曝光的影子计量（即使 product_id 为空，也通过 page_category=PLP 时的产品列表品类分布估算）。

---

## 二、统计分析层面

### 2.1 优点

- Bonferroni 多重比较校正应用正确（α=0.0125，4个维度同时检验）
- Cohen's d 效应量配合显著性检验，避免大样本下"统计显著但无实际意义"的问题
- Shift-Share 分解方法正确区分了结构效应和质量效应
- 卡方检验配合 Cramér's V 效应量，提供了关联强度的量化指标

### 2.2 问题与建议

#### 问题 2.2.1：Welch's t 检验的前提假设未验证

**位置**：[funnel_analysis.py:688](../../python/funnel_analysis.py#L688)

```python
t_stat, p_val = stats.ttest_ind(lost[feat], conv[feat], equal_var=False)
```

**描述**：代码正确使用了 `equal_var=False`（Welch's t-test）处理方差不齐情况，但未验证数据是否接近正态分布。在样本量极大时（流失组/转化组各数万人），中心极限定理可提供一定稳健性保证，但这一假设未被明确说明。

**解决方案**：添加正态性诊断日志或 Shapiro-Wilk 抽样验证（对大样本可随机抽样 5000 条验证）：

```python
# 在 compute_churn_features 开头添加
sample_size = min(5000, len(lost), len(conv))
_, p_norm_lost = stats.shapiro(lost[feat].sample(sample_size, random_state=42))
_, p_norm_conv = stats.shapiro(conv[feat].sample(sample_size, random_state=42))
logger.info("  正态性检验 p值: 流失组=%.4f, 转化组=%.4f", p_norm_lost, p_norm_conv)
```

#### 问题 2.2.2：Cohen's d 函数使用总体方差而非样本方差

**位置**：[funnel_analysis.py:677](../../python/funnel_analysis.py#L677)

```python
pooled = np.sqrt(((na - 1) * a.std() ** 2 + (nb - 1) * b.std() ** 2) / (na + nb - 2))
```

**描述**：`a.std()` 和 `b.std()` 默认使用 `ddof=0`（总体方差），但公式中分子用了 `na-1` 和 `nb-1`（样本方差的不偏估计量）。两者不匹配——当 na、nb 较大时影响可忽略，但小样本下会产生偏差。

**解决方案**：显式传入 `ddof=1`：

```python
pooled = np.sqrt(((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2) / (na + nb - 2))
```

#### 问题 2.2.3：Cramér's V 的 min_dim 参数逻辑

**位置**：[funnel_analysis.py:865](../../python/funnel_analysis.py#L865)

```python
def cramers_v(chi2: float, n: int, min_dim: int) -> float:
    return float(np.sqrt(chi2 / (n * (min_dim - 1))))
```

**描述**：`min(ct.shape)` 取行列数的较小值，但 Cramér's V 的自由度是 `min(行数, 列数) - 1`，当列联表为 5×2 时 min_dim=2，公式变为 `sqrt(chi2 / (n * 1))`。这在技术上是正确的（因为 V 的上限取决于较小维度），但命名 `min_dim` 容易与"维度数"混淆。

**解决方案**：重命名为 `min_cat`（较小类别数）并增加说明注释：

```python
def cramers_v(chi2: float, n: int, min_cat: int) -> float:
    """Cramér's V 效应量 — min_cat 为列联表的较小维度（类别数），决定 V 的上限"""
    if min_cat <= 1 or n == 0:
        return 0.0
    return float(np.sqrt(chi2 / (n * (min_cat - 1))))
```

#### 问题 2.2.4：流失特征分析的因果困境

**位置**：[funnel_analysis.py:664-668](../../python/funnel_analysis.py#L664-L668)

**描述**：文档已指出——"event_count 和 total_duration_sec 的差异部分反映'完成更多漏斗步骤'的自然结果"，即存在自我指涉问题（tautology）：转化组因为转化了所以互动更多，还是互动更多所以转化？当前数据字段无法区分两者。

**解决方案**：这是数据字段限制导致的固有局限，无法通过分析修复。建议在 `03-methodology.md` 的"三、流失根因诊断"章节中增加"方法论局限性"说明，并在输出结论时明确标注"互动深度与转化存在相关性，但因果方向需独立验证"。

---

## 三、业务分析逻辑层面

### 3.1 优点

- 双漏斗（覆盖 vs 严格路径）并行的设计非常合理，能捕捉真实用户行为的复杂性
- PIE 优先级矩阵使用 WiderFunnel 方法论，量化了 Potential/Importance/Ease 三个维度
- 损失金额计算中"流失会话级联去重"逻辑正确（`cumulative_lost |= lost_sessions`）
- 新老用户分层分析揭示了"页面路径一致但行为深度不同"这一关键洞察
- 策略摘要自动生成（`generate_strategy_brief`）能快速输出业务建议

### 3.2 问题与建议

#### 问题 3.2.1：PIE 矩阵的 Ease 分数是主观赋值

**位置**：[funnel_analysis.py:833-839](../../python/funnel_analysis.py#L833-L839)

```python
ease_map = {
    '首页 → 列表页': 7,
    '列表页 → 详情页': 6,
    '详情页 → 购物车': 6,
    '购物车 → 结算页': 8,
}
```

**描述**：Ease 分数（1-10）没有数据支撑，不同人可能给出不同分数，导致 PIE 排名存在主观性。

**解决方案**：两种改进路径——
1. **量化 Ease**：基于该环节的历史 A/B 测试数据或已知技术实现难度赋值，公式：`Ease = 10 - avg_test_duration_weeks / 2`（实现周期越长，Ease 越低）
2. **透明化说明**：在输出 PIE 矩阵时增加 `ease_source: "expert_score"` 字段，标注这是专家打分，并说明各分数的含义区间

#### 问题 3.2.2：年度损失估算使用三年均值，但三年数据质量不一致

**位置**：[04-results.md:288](docs/04-results.md#L288)

**描述**：`¥59,760,920` 的年损失估算基于三年综合数据，但 2021-2023 各年会话量差异巨大（421K→155K→56K）且呈下降趋势，用"三年均值 × 客单价"推算单年损失会产生误导——会高估 2021 年也低估 2023 年。

**解决方案**：分年度独立估算并输出：

```python
# 在 compute_loss_amount 中按年分组
for year in funnel_wide['year'].unique():
    year_data = funnel_wide[funnel_wide['year'] == year]
    year_loss = compute_year_loss(year_data, aov)
    logger.info("  %d 年损失估算: ¥%s", int(year), f"{year_loss:,.0f}")

# 输出时标注
logger.warning(
    "注意：年度损失基于当年各环节流失率估算。"
    "2022-2023 数据完整性存疑，结论需结合数据覆盖率校正。"
)
```

#### 问题 3.2.3：Shift-Share 归因的数据完整性前提未明确

**位置**：[funnel_analysis.py:976-988](../../python/funnel_analysis.py#L976-L988)

**描述**：代码中已添加数据完整性警示（会话量变化 >30% 时报警），但 `compute_trend_attribution` 的循环逻辑假设每年各渠道数据均存在，若某年份新增渠道会导致 KeyError。

**解决方案**：在循环开始前验证所有年份渠道一致性：

```python
# 检查 base year 渠道是否在所有年份都存在
base_channels = set(attr_df[attr_df['year'] == base_year]['channel'].unique())
for y in years[1:]:
    curr_channels = set(attr_df[attr_df['year'] == y]['channel'].unique())
    missing = base_channels - curr_channels
    if missing:
        logger.warning(
            "  %d 年缺少渠道 %s (基准年有但当年无), 已跳过这些渠道的归因计算",
            int(y), missing
        )
```

#### 问题 3.2.4：渠道 × 设备热力图的样本量门槛过于简单

**位置**：[funnel_analysis.py:650](../../python/funnel_analysis.py#L650)

```python
worst = cross[cross['会话数'] >= 1000].nsmallest(3, '转化率(%)')
```

**描述**：仅用 1000 会话的绝对门槛判断，在 tablet（7,601 会话）这种小样本渠道中，任何波动都可能产生误导。建议增加统计显著性检验或展示置信区间。

**解决方案**：增加 Wilson 置信区间估计：

```python
from math import sqrt

def wilson_ci(successes, total, z=1.96):
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    n = total
    den = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / den
    margin = z * sqrt((p*(1-p) + z**2/(4*n)) / n) / den
    return max(0, center - margin), min(1, center + margin)

# 对每个交叉组合计算 95% CI
for (ch, dev), row in cross_df.iterrows():
    ci_low, ci_high = wilson_ci(row['购买会话数'], row['会话数'])
    cross_df.loc[(ch, dev), 'CR_95CI_low'] = ci_low * 100
    cross_df.loc[(ch, dev), 'CR_95CI_high'] = ci_high * 100
```

---

## 四、可视化层面

### 4.1 优点

- 18 张图表覆盖面广，从清洗流程到 Cohort 留存都有覆盖
- matplotlib 使用 `bbox_inches='tight'` 避免标签被截断
- Plotly 漏斗图的信息密度合理（同时展示绝对值和转化率）
- 双轴图（时长 vs 转化率）配色区分清晰
- 渠道专属漏斗（03 号图）用同色系深浅色标注瓶颈，非一刀切配色

### 4.2 问题与建议

#### 问题 4.2.1：瀑布图累积线连接的是柱顶而非柱底

**位置**：[visualization.py:320-322](../../python/visualization.py#L320-L322)

```python
ax.plot(range(n), cumulative[:-1], 'D-', color=C_BLUE, linewidth=2.2,
        markersize=9, markerfacecolor='white', markeredgecolor=C_BLUE,
        markeredgewidth=2, zorder=5, label='累积损失')
```

**描述**：`cumulative[:-1]` 连接的是每根柱子的**顶部**（结束位置），而非柱子的**底部**（起始位置），导致累积线与柱子视觉上分离，违反了瀑布图"阶梯式累积"的标准视觉语言。

**解决方案**：使用 `bottoms` 数组连接柱底：

```python
# 瀑布的核心是每根柱子的起始位置（bottoms[i]）到累积值（cumulative[i]）
# 累积线应连接 bottoms 的上沿，即每步的起点
ax.plot(range(n), cumulative[:-1] - values, 'D-', ...)
// 或者改用 step 形式
ax.step(range(n), cumulative[:-1], 'D-', where='post', ...)
```

#### 问题 4.2.2：热力图文字对比度判断过于简单

**位置**：[visualization.py:395](../../python/visualization.py#L395)

```python
text_color = 'white' if val < mid_val else C_DARK
```

**描述**：用中高阈值（vmin+vmax）/2 判断文字颜色，当转化率在 14-16% 区间时，mid_val≈15%，数值在阈值附近的单元格文字颜色可能与背景接近（如淡橙色背景配深灰色文字，可读性差）。

**解决方案**：改用感知亮度判断或对低值区域统一用深色文字：

```python
# 方案1：统一阈值偏向深色（热力图红色系背景偏暗，深色文字永远可读）
text_color = 'white' if val > vmax * 0.7 else C_DARK

# 方案2：采用双色调色板（低值绿→高值红），绿色区域用深色文字，红色区域用白色
if val < (vmin + vmax) / 2:
    text_color = C_DARK  # 浅色背景用深色文字
else:
    text_color = 'white'  # 深色背景用白色文字
```

#### 问题 4.2.3：深链流量对比图缺少显著性标注

**位置**：[visualization.py:757-764](../../python/visualization.py#L757-L764)

**描述**：右侧分渠道对比图标注了"↑+7.1pp"等数值差异，但没有标注这些差异是否在统计上显著。两个渠道间的 5pp 差异在 1000 样本和 100000 样本下含义完全不同。

**解决方案**：增加卡方检验的 p 值标注或用误差线（error bar）展示置信区间。

---

## 五、代码工程层面

### 5.1 优点

- `_stage_runner` 和 `_safe_plot` 的异常处理设计合理，单图失败不中断全流程
- 配置集中管理（`config.py`），颜色方案、漏斗定义、常量均由此处获取
- 日志格式统一，支持 DEBUG/INFO/WARNING/ERROR 多级别，支持输出到文件和终端双 Handler
- 类型提示使用 Python 3.13+ 语法（`pd.DataFrame | None`）
- 六阶段主流程结构清晰，每个阶段职责单一

### 5.2 问题与建议

#### 问题 5.2.1：`funnel_wide` 被原地修改的风险

**位置**：
- [funnel_analysis.py:190](../../python/funnel_analysis.py#L190)（`compute_deep_link_analysis`）
- [funnel_analysis.py:483](../../python/funnel_analysis.py#L483)（`compute_weekend_analysis`）
- [funnel_analysis.py:556](../../python/funnel_analysis.py#L556)（`compute_duration_analysis`）

**描述**：多个函数对 `funnel_wide` 进行 `copy()` 或直接修改列后再返回。若调用方保留了旧引用，可能导致后续分析使用被篡改的数据。`compute_deep_link_analysis` 是唯一一个在函数体内对 funnel_wide 做 `copy()` 后再修改的函数，模式不一致。

**解决方案**：统一模式——在所有修改 `funnel_wide` 的函数开头做 `copy()`：

```python
def compute_deep_link_analysis(funnel_wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    funnel_wide = funnel_wide.copy()  # 统一在函数开头复制
    # ... 后续操作均在副本上进行
```

#### 问题 5.2.2：`compute_trend_attribution` 的渠道 KeyError 风险

**位置**：[funnel_analysis.py:938-945](../../python/funnel_analysis.py#L938-L945)

```python
for ch in channels:
    if ch in base.index and ch in curr.index:
        base_share = base.loc[ch, 'share'] / 100
        curr_share = curr.loc[ch, 'share'] / 100
        base_ch_cr = base.loc[ch, 'cr'] / 100
        curr_ch_cr = curr.loc[ch, 'cr'] / 100
        struct_effect += base_ch_cr * (curr_share - base_share)
        quality_effect += base_share * (curr_ch_cr - base_ch_cr)
```

**描述**：代码已有 `if ch in base.index and ch in curr.index` 保护，不会有 KeyError，但当某渠道在 base year 存在而在 curr year 不存在时，该渠道被完全忽略而非报错。若当年新增渠道（如新增了"Affiliate"渠道），也不会计入结构效应。

**解决方案**：增加"缺失渠道"和"新增渠道"的日志记录，使归因结果完整可追溯：

```python
missing = base_channels - curr_channels  # 基准年有、当年无
new_ch = curr_channels - base_channels  # 当年新增、基准年无

if missing:
    logger.warning("  归因跳过缺失渠道(基准年有当年无): %s", missing)
if new_ch:
    logger.warning("  归因跳过新增渠道(当年有基准年无): %s (需单独归因)", new_ch)
```

#### 问题 5.2.3：PIE Importance 值的分母锚定问题

**位置**：[funnel_analysis.py:828-831](../../python/funnel_analysis.py#L828-L831)

```python
pie['Importance'] = (pie['入环节会话数'] / total_sessions * 10).clip(1, 10).round(1)
# 其中 total_sessions = loss_df['入环节会话数'].max()（首页入环节会话数）
```

**描述**：不同漏斗阶段的"入环节会话数"分母不同（首页 300K → 列表页 396K → 详情页 323K），导致 I 值无法跨阶段比较——两个阶段 I=8 的含义不同（一个基于 300K，一个基于 396K）。

**解决方案**：统一使用"总会话数"作为分母，或者将 Importance 改为相对排名（rank-based）：

```python
# 方案1：使用统一的总会话数分母
pie['Importance'] = (pie['入环节会话数'] / len(funnel_wide) * 10).clip(1, 10).round(1)

# 方案2：改用 rank-based（避免比例被 clip 截断）
pie['Importance'] = pie['入环节会话数'].rank(pct=True) * 9 + 1  # 1-10 scale
```

#### 问题 5.2.4：集成测试未覆盖"AOV=0"的边界情况

**位置**：[test_integration.py:231](../../tests/test_integration.py#L231)

**描述**：`test_loss_amount_no_transactions` 测试了"无 transactions 数据"的场景，但测试数据中所有会话都有 `total_revenue > 0`，没有覆盖"所有会话都未购买导致 AOV 无法计算"的边界情况。

**解决方案**：增加边界测试：

```python
def test_loss_amount_all_unpurchased(self):
    """测试所有会话均未购买时，AOV=0 的处理"""
    np.random.seed(42)
    n = 20
    wide = pd.DataFrame({
        'session_id': [f's{i}' for i in range(n)],
        'customer_id': [f'u{i}' for i in range(n)],
        'traffic_source': ['Organic'] * n,
        'device_type': ['desktop'] * n,
        'experiment_group': ['Control'] * n,
        'campaign_id': [1] * n,
        'total_duration_sec': np.random.uniform(10, 600, n),
        'event_count': np.random.randint(2, 20, n),
        'hour': np.random.randint(0, 24, n),
        'weekday': np.random.randint(0, 7, n),
        'year': [2023] * n,
        'month': [1] * n,
        'has_refund': np.zeros(n),
        'total_revenue': np.zeros(n),  # 所有用户收入为0
        'total_transactions': np.zeros(n, dtype=int),
        'loyalty_tier': ['Bronze'] * n,
        'country': ['US'] * n,
        'acquisition_channel': ['Organic'] * n,
        'session_start': pd.Timestamp('2023-01-01'),
        'session_end': pd.Timestamp('2023-01-01'),
        'step1_home': np.ones(n, dtype=int),
        'step2_plp': np.random.choice([0, 1], n, p=[0.5, 0.5]),
        'step3_pdp': np.zeros(n, dtype=int),
        'step4_cart': np.zeros(n, dtype=int),
        'step5_checkout': np.zeros(n, dtype=int),
        'step_view': np.ones(n, dtype=int),
        'step_click': np.zeros(n, dtype=int),
        'step_add_cart': np.zeros(n, dtype=int),
        'step_purchase': np.zeros(n, dtype=int),
        'is_bounced': np.zeros(n, dtype=int),
        'is_purchased': np.zeros(n, dtype=int),
    })
    loss = compute_loss_amount(wide, transactions=None)
    assert loss['估算损失金额'].sum() == 0  # AOV=0 时损失为0
    assert not loss.isnull().any().any()
```

---

## 六、文档与可维护性

### 6.1 优点

- `03-methodology.md` 方法论文档详细说明了每个分析方法的原理和适用场景
- `04-results.md` 中的"核心发现一览"表格结构清晰，便于快速掌握结论
- 双口径转化率（Session CR vs View-to-Purchase CR）的说明避免了混淆
- README 中的六阶段闭环流程图清晰，项目结构一目了然
- 代码中的注释覆盖了关键逻辑（如"级联去重"的原因）

### 6.2 问题与建议

#### 问题 6.2.1：部分工具函数缺少文档字符串

**位置**：`_dimension_analysis`（[funnel_analysis.py:339](../../python/funnel_analysis.py#L339)）、`_safe_plot`（[main.py:34](../../python/main.py#L34)）、`_stage_runner`（[main.py:42](../../python/main.py#L42)）

**描述**：这些是被其他模块调用的工具函数，但完全无文档注释。

**解决方案**：添加 Google 风格的文档字符串：

```python
def _dimension_analysis(funnel_wide: pd.DataFrame, dim_col: str,
                        label: str = '') -> pd.DataFrame:
    """通用维度转化率分析 — 按指定维度分组计算会话数和购买转化率。

    Args:
        funnel_wide: 漏斗宽表 DataFrame
        dim_col: 分组维度列名（如 'traffic_source', 'device_type'）
        label: 日志输出的维度名称前缀

    Returns:
        DataFrame，含 总会话数、购买会话数、转化率(%)、流量占比(%)
    """
```

#### 问题 6.2.2：baseline snapshot JSON 包含自然语言说明

**位置**：[funnel_analysis.py:1133-1137](../../python/funnel_analysis.py#L1133-L1137)

**描述**：`metric_definitions` 字段中包含中文 note："双口径定义不同, 不可直接比较"。JSON 作为机器可读输出不适合放自然语言说明。

**解决方案**：拆分为独立字段或移到文档：

```python
snapshot = {
    'analysis_timestamp': datetime.now().isoformat(),
    'analysis_version': '2.0',
    'metric_definitions': {
        'session_conversion_rate': {'formula': 'purchase_sessions / total_sessions * 100', 'denominator': 'all_sessions'},
        'view_to_purchase_rate': {'formula': 'purchase_sessions / view_sessions * 100', 'denominator': 'sessions_with_view'},
    },
    'metric_notes_url': 'docs/04-results.md#metric-definitions',  # 人类可读说明的文档链接
}
```

#### 问题 6.2.3：中文文件名可能引发跨平台问题

**位置**：
- `docs/260520_总体问题.md`
- `docs/260520_输出结果问题.md`
- `docs/260520_深度求索多阶段审查意见汇总.md`（推测存在）

**描述**：中文文件名在 Windows 以外的系统（Linux/macOS）可能产生编码问题或排序异常，建议统一使用英文文件名或拼音。

**解决方案**：重命名为：
- `2026-05-20-funnel-critique.md`（已存在）
- `docs/issues-overview-20260520.md`
- `docs/output-issues-20260520.md`

---

## 七、数据质量风险总览

| 风险点 | 严重度 | 位置 | 状态 |
|:---|:---:|:---|:---|
| 2022-2023 会话量骤降（数据完整性存疑） | ⚠️ 高 | [funnel_analysis.py:629-634](../../python/funnel_analysis.py#L629-L634) | 已有日志警告 |
| Cohort size=0 时除零导致虚高留存率（100%） | ⚠️ 中 | [funnel_analysis.py:1083](../../python/funnel_analysis.py#L1083) | **需修复** |
| 品类浏览统计仅含有点击商品的事件 | ⚠️ 中 | [04-results.md:194](docs/04-results.md#L194) | 文档已承认 |
| 渠道归因中某年份新增渠道被静默跳过 | ⚠️ 低 | [funnel_analysis.py:938-945](../../python/funnel_analysis.py#L938-L945) | 已有条件判断 |
| Cohen's d 函数未使用样本标准差（ddof=1） | ⚠️ 低 | [funnel_analysis.py:677](../../python/funnel_analysis.py#L677) | **需修复** |
| funnel_wide 被原地修改可能导致数据污染 | ⚠️ 低 | 多处 | **需审查修复** |
| PIE Ease 主观赋值缺乏透明度 | ⚠️ 中 | [funnel_analysis.py:833-839](../../python/funnel_analysis.py#L833-L839) | **需说明** |
| AOV=0 时损失计算未覆盖边界情况 | ⚠️ 低 | 测试文件 | **需补充测试** |

---

## 八、总结评价

### 8.1 项目亮点

1. **分析框架完整**：六阶段闭环（探查→建模→诊断→根因→量化→策略）可落地执行
2. **双漏斗设计**：覆盖分析（Page Coverage）vs 严格路径（Strict Sequential）并行，揭示真实用户行为复杂性
3. **统计方法使用得当**：Bonferroni 校正 + Cohen's d + Shift-Share 分解 + Cramér's V，方法论严谨
4. **代码结构清晰**：异常处理健壮，配置集中管理，日志多级别输出
5. **业务洞察深刻**：新老用户行为深度差异、首页筛选价值、渠道专属瓶颈等发现具有实际指导价值

### 8.2 最需优先修复的问题（按优先级）

| 优先级 | 问题 | 影响 |
|:---:|:---|:---|
| P0 | Cohort size=0 时除零导致虚高留存率 | 可能产生完全错误的留存结论 |
| P0 | funnel_wide 被原地修改的数据污染风险 | 可能导致分析结果不可复现 |
| P1 | Cohen's d 使用总体方差而非样本方差 | 小样本下效应量估算偏差 |
| P1 | PIE Ease 主观赋值缺乏透明化说明 | 影响业务方对 PIE 排名的信任度 |
| P1 | 年度损失估算未标注数据完整性前提 | 可能导致错误的年度预算规划 |
| P2 | 瀑布图累积线连接柱顶而非柱底 | 视觉信息传达不准确 |
| P2 | AOV=0 边界情况未覆盖 | 测试存在漏洞 |

### 8.3 后续优化建议

1. **短期（1-2周）**：修复上述 P0/P1 问题（除零、funnel_wide 拷贝、Cohen's d）
2. **中期（1个月）**：完善测试覆盖（边界情况、AOV=0）、增加可视化置信区间、改进 PIE Ease 透明度
3. **长期（季度）**：
   - 在 transactions 表增加 session_id 字段，从根本上解决收入归因问题
   - 增加埋点字段（搜索使用、评价查看、比价行为）以提升流失根因的诊断可操作性
   - 建立数据质量监控看板，自动检测年度会话量异常波动

---

*本评审报告由 Claude 依据项目代码、文档和运行结果生成，评审深度覆盖数据工程、统计方法、业务逻辑、可视化、代码质量和文档可维护性六大维度。*