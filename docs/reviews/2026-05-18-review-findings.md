# 项目全面审查报告

> 审查日期：2026-05-18 | 审查范围：全部 Python/SQL/文档/测试

---

## 目录

1. [逻辑错误与结果冲突](#一逻辑错误与结果冲突)
2. [代码错误](#二代码错误)
3. [行业方法评估](#三行业方法评估)
4. [企业级闭环评估](#四企业级闭环评估)
5. [修复方案](#五修复方案)

---

## 一、逻辑错误与结果冲突

### 1.1 页面漏斗转化率超过 100%（严重）

**问题**：[04-results.md](../04-results.md) 报告首页→列表页转化率为 **131.77%**，数学上不可能。

**根因**：[python/funnel_analysis.py](../python/funnel_analysis.py#L39) 的 `compute_page_funnel` 使用交叉引用计算转化率：

```python
both = ((funnel_wide[steps[i]] == 1) & (funnel_wide[steps[i + 1]] == 1)).sum()
rate = both / prev * 100
```

`both` 是同时到达前后两个页面的会话数，它 ≤ 前页会话数，所以转化率不可能超过 100%。

文档中 131.77% = 396,329（PLP 会话数）/ 300,782（Home 会话数），说明文档数值**不是从代码实际运行获取的**，而是手工用错误公式计算的。

**修复**：重新运行 `python/python/main.py`，将实际输出的 `上一阶段转化率(%)` 填入文档。

---

### 1.2 核心指标「转化率」有两套矛盾的口径（严重）

| 来源 | 转化率 | 计算方式 |
|:---|:---:|:---|
| [baseline_snapshot.json](../output/baseline_snapshot.json#L6) | **15.08%** | `step_purchase.mean()` 在全部 633,450 会话中 |
| [README.md](../README.md#L30) / [docs/04-results.md](../docs/04-results.md#L32) | **18.13%** | 95,535 / 526,869（行为漏斗 view→purchase） |

两个值都叫"转化率"，但分母不同（全部会话 vs 浏览会话），差了 3 个百分点。

**修复**：在项目中统一定义两类指标，全文一致使用：

| 指标名 | 定义 | 计算 |
|:---|:---|:---|
| 会话转化率 (Session CR) | 购买会话 / 全部会话 | `step_purchase.sum() / total_sessions` |
| 浏览转化率 (View-to-Purchase Rate) | 购买会话 / 浏览会话 | `step_purchase.sum() / step_view.sum()` |

更新 `baseline_snapshot.json` 的 `conversion_rate` 计算，或在快照中同时记录两个指标。

---

### 1.3 流失会话数超过总会话数（严重）

[docs/04-results.md](../docs/04-results.md#L192-L196) 损失量表中：

| 流失环节 | 流失会话数 |
|:---|---:|
| 首页 → 列表页 | 121,895 |
| 列表页 → 详情页 | 160,998 |
| 详情页 → 购物车 | 293,462 |
| 购物车 → 结算页 | 127,703 |
| **合计** | **704,058** |

但项目总共只有 **633,450** 个会话。同一个会话在多个环节被重复计数，损失金额也因此被重复累加。

**根因**：[python/funnel_analysis.py](../python/funnel_analysis.py#L408-L411) 的 `compute_loss_amount` 对每个环节独立计算流失会话，未去重：

```python
lost = funnel_wide[
    (funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 0)
]
```

同一会话如果在首页流失，就不会到达列表页——但它可能在详情页也"到达过但未继续"。

**修复**：

```python
# 用累计到达标记避免重复计数
reached_home = funnel_wide[funnel_wide['step1_home'] == 1]
lost_home = reached_home[reached_home['step2_plp'] == 0]

# 列表页流失 = 到达了列表页但没到详情页
# 这些会话已经排除了首页流失的
reached_plp = reached_home[reached_home['step2_plp'] == 1]
lost_plp = reached_plp[reached_plp['step3_pdp'] == 0]

# 以此类推...
```

---

## 二、代码错误

### 2.1 测试代码全部失效（严重）

**问题**：[tests/test_data_cleaning.py](../tests/test_data_cleaning.py#L4-L6) 导入不存在的函数：

```python
from python.data_cleaning import (
    basic_cleaning, funnel_specific_cleaning, build_funnel_wide
)
```

当前模块实际导出为 `basic_cleaning_events`, `build_session_attributes`, `build_funnel_wide`。

[tests/test_funnel_analysis.py](../tests/test_funnel_analysis.py#L4-L6) 同样导入 `compute_funnel`（已重命名为 `compute_page_funnel` / `compute_event_funnel`）。

测试数据格式（`SessionID`, `PageType`, `ReferralSource`, `TimeOnPage_seconds`）也与当前数据模型完全不匹配。

**运行 `pytest` 会 100% 失败。**

**修复**：重写两个测试文件，匹配当前 API 和数据模型。见[第五节修复方案](#51-测试重写)。

---

### 2.2 MySQL 导出引用不存在的表（严重）

**问题**：[python/import_to_mysql.py](../python/import_to_mysql.py#L136-L138) `step5_export_powerbi()` 执行：

```sql
SELECT sf.*, c.country, c.loyalty_tier, c.acquisition_channel
FROM session_funnel sf JOIN customers c ON sf.customer_id = c.customer_id
```

`session_funnel` 只是 `08_operational_export.sql` 中的一个 CTE（WITH 子句），不是持久化表。Python 脚本在调用 `step3_run_analysis()` 时执行了 `08_operational_export.sql`，但 CTE 在 SQL 文件执行完后就消失了。后续 `step5_export_powerbi()` 中直接 `FROM session_funnel` 会报错：`Table 'ecommerce.session_funnel' doesn't exist`。

此外，`category_analysis.csv` 的导出查询（第 149-153 行）包含未在代码中定义的 SQL，也会失败。

**修复**：

方案一：将 `session_funnel` 改为 `CREATE VIEW` 持久化：

```sql
CREATE OR REPLACE VIEW session_funnel_view AS
WITH session_funnel AS (...)
SELECT * FROM session_funnel;
```

然后在 Python 中查询 `session_funnel_view`。

方案二：在 Python 中用 pandas 直接从 funnel_wide CSV 导出 Power BI 数据，绕过 MySQL。

---

### 2.3 `total_revenue` 无故取绝对值（中等）

**问题**：[python/data_cleaning.py](../python/data_cleaning.py#L145)：

```python
funnel_wide['total_revenue'] = funnel_wide['total_revenue'].abs()
```

对收入取绝对值会静默抹除负收入数据（可能来自退款超过收入的异常订单），且无任何日志记录。

**修复**：

```python
negative = funnel_wide['total_revenue'] < 0
if negative.any():
    logger.warning("发现 %d 条负收入记录, 已标记但保留原值", negative.sum())
    funnel_wide['has_negative_revenue'] = negative.astype(int)
# 删除 .abs() 调用
```

---

### 2.4 品类漏斗「浏览会话」计数错误（中等）

**问题**：[python/funnel_analysis.py](../python/funnel_analysis.py#L199-L201)：

```python
view_by_cat = (
    events_with_cat.groupby('category')['session_id'].nunique()
    .reset_index(name='浏览会话')
)
```

这里没有过滤 `event_type == 'view'`，导致「浏览会话」包括了所有事件类型（purchase、add_to_cart、click 等），浏览会话数被严重高估。

**修复**：

```python
view_by_cat = (
    events_with_cat[events_with_cat['event_type'] == 'view']
    .groupby('category')['session_id'].nunique()
    .reset_index(name='浏览会话')
)
```

---

### 2.5 `traffic_source` 聚合可能抛异常（低）

**问题**：[python/data_cleaning.py](../python/data_cleaning.py#L60-L61)：

```python
traffic_source=('traffic_source', lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]),
```

当会话内所有 `traffic_source` 值都不同时（理论上极小概率但仍可能），`mode()` 返回空 Series，fallback 到 `x.iloc[0]` 可以兜底，但 `device_type` 也是同样逻辑——这段代码脆弱但暂不影响运行。

**修复**（防御性）：提取公共函数：

```python
def _safe_mode(series):
    modes = series.mode()
    return modes.iloc[0] if not modes.empty else series.iloc[0]
```

---

## 三、行业方法评估

### 3.1 标准方法（过关）

| 方法 | 代码位置 | 评价 |
|:---|:---|:---|
| Welch's t-test + Cohen's d | [funnel_analysis.py:312-350](../python/funnel_analysis.py#L312-L350) | 正确。Welch 不假设方差齐性，Cohen's d 避免大样本 p-hacking |
| 卡方独立性检验 + Bonferroni 校正 | [funnel_analysis.py:482-502](../python/funnel_analysis.py#L482-L502) | 正确。4 个维度 → α=0.0125 |
| GA4 固定阈值分桶 | [config.py:67-74](../python/config.py#L67-L74) | 方向正确，比等频分桶更适合跨周期对比 |
| PIE 优先级矩阵 | [funnel_analysis.py:447-475](../python/funnel_analysis.py#L447-L475) | WiderFunnel 方法论，行业标准 |
| 页面级 + 行为级双漏斗 | [funnel_analysis.py:21-98](../python/funnel_analysis.py#L21-L98) | Amplitude/Mixpanel 标准范式 |

### 3.2 有争议的方法

#### a) 损失量化权重无实证依据

**位置**：[python/funnel_analysis.py](../python/funnel_analysis.py#L415)

```python
weight = 0.3 if '首页' in label else 0.5 if '列表' in label else 0.8 if '详情' in label else 1.0
```

0.3/0.5/0.8/1.0 的权重体系无任何文献引用或数据支持。行业替代方案：

- **倾向性得分匹配**（Propensity Score Matching）：用已转化用户的特征建模，估计流失用户的反事实转化概率 × 客单价
- **历史均值法**：直接用同类已转化用户的平均客单价，而非自定义权重
- **CausalImpact**（Google）：贝叶斯结构时间序列估计因果效应

**修复**：

```python
# 方案：计算各环节已转化用户的客单价作为流失用户的潜在价值
def compute_stage_potential_value(funnel_wide, stage_col, next_col):
    """流失用户如果转化了，按同类转化用户客单价估算"""
    converted = funnel_wide[(funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 1)]
    converted_revenue = funnel_wide[
        funnel_wide['customer_id'].isin(converted['customer_id'])
    ]['total_revenue']
    return converted_revenue[converted_revenue > 0].mean()
```

#### b) 流失特征分析存在循环论证

**位置**：[python/funnel_analysis.py](../python/funnel_analysis.py#L312-L350)

用 `total_duration_sec` 和 `event_count` 对比"流失组 vs 转化组"。但"转化"的定义就是完成了更多漏斗步骤——完成更多步骤必然产生更多事件和更长停留时间。结论"转化用户互动更深"是同义反复（tautology），不提供诊断价值。

**修复**：对比更有意义的特征：

- 加购前页面浏览品类数
- 是否使用了搜索功能
- 同一商品的重复查看次数
- 加入购物车后是否查看了其他商品（比价行为）
- 距上次购买的间隔天数

#### c) 「GA4 行业标准」引用不准确

**位置**：[docs/03-methodology.md](../docs/03-methodology.md#L48-L57)

文档声称时长分桶参考 GA4，但 GA4 的 engaged session 阈值是 10 秒或 1 次 conversion / 2+ pageviews。60/180/420 秒分桶并非 GA4 定义。

**修复**：删除对 GA4 的引用，改为"参考电商行业行为分桶最佳实践"。

### 3.3 缺失的标准分析方法

| 方法 | 数据可行性 | 业务价值 |
|:---|:---:|:---|
| 留存 Cohort 分析 | 有 timestamp + customer_id | 衡量长期用户价值 |
| RFM 客户分层 | 有 recency + frequency + monetary 字段 | 精细化运营策略 |
| Sankey 路径分析 | 有 page_category + session_id | 比漏斗更能反映真实行为 |
| 提升度分析（Lift Analysis） | 可做 | 渠道×环节的标准诊断方法 |

---

## 四、企业级闭环评估

### 4.1 做得好

- 六阶段闭环结构完整：探查→建模→诊断→根因→量化→策略
- 双引擎（Python 探索 + SQL 生产化）
- 12 张可视化覆盖主要维度
- Power BI 完整报告（TMDL 模型 + PBIR 报告 + 4 页 12 视觉对象）
- 文档四件套（背景、字典、方法论、结果）
- 基准快照支持优化前后对比

### 4.2 缺失项

| 项目 | 重要性 | 说明 |
|:---|:---:|:---|
| 数据质量报告 | **高** | 缺失率、异常值分布、关联完整性——目前只有 logger 输出 |
| 增量效果预估 | **高** | "如果 PDP→Cart 提升 5%，年增量收入是多少？" |
| 监控告警阈值 | 中 | 什么指标跌破什么值触发什么动作 |
| 数据管道调度 | 中 | CI/CD / Airflow / cron |
| 代码能从头跑到尾 | **最高** | 目前测试跑不通，MySQL 导出跑不通 |

---

## 五、修复方案

### 5.1 测试重写

**文件**：[tests/test_data_cleaning.py](../tests/test_data_cleaning.py)

```python
"""数据清洗模块 — 单元测试"""
import pandas as pd
import numpy as np
from python.data_cleaning import (
    basic_cleaning_events, build_session_attributes, build_funnel_wide
)


def _make_events_df() -> pd.DataFrame:
    return pd.DataFrame({
        'event_id': [1, 2, 3, 4, 5, 6, 7, 8],
        'timestamp': pd.to_datetime([
            '2023-01-01 10:00:00', '2023-01-01 10:02:00',
            '2023-01-01 10:00:00', '2023-01-01 10:03:00',
            '2023-01-01 10:05:00', '2023-01-01 10:00:00',
            '2023-01-01 10:00:00', '2023-01-01 10:01:00',
        ]),
        'customer_id': [1, 1, 2, 2, 2, 3, 4, 4],
        'session_id': [101, 101, 102, 102, 102, 103, 104, 104],
        'event_type': ['view', 'add_to_cart', 'view', 'click', 'purchase',
                       'bounce', 'view', 'click'],
        'product_id': [10, 10, 20, 20, 20, None, 30, 30],
        'device_type': ['desktop', 'desktop', 'mobile', 'mobile', 'mobile',
                        'tablet', 'desktop', 'desktop'],
        'traffic_source': ['Organic', 'Organic', 'Email', 'Email', 'Email',
                           'Direct', 'Social', 'Social'],
        'campaign_id': [1, 1, 2, 2, 2, None, 3, 3],
        'page_category': ['PLP', 'PDP', 'Home', 'PDP', 'Checkout',
                          'Home', 'PLP', 'PDP'],
        'session_duration_sec': [55, 120, 40, 90, 30, 3, 200, 100],
        'experiment_group': ['Control', 'Control', 'Variant_B', 'Variant_B',
                             'Variant_B', 'Control', 'Variant_A', 'Variant_A'],
    })


def _make_customers_df() -> pd.DataFrame:
    return pd.DataFrame({
        'customer_id': [1, 2, 3, 4],
        'country': ['US', 'UK', 'FR', 'IN'],
        'age': [25, 34, 28, 42],
        'gender': ['Male', 'Female', 'Male', 'Female'],
        'loyalty_tier': ['Silver', 'Gold', 'Bronze', 'Platinum'],
        'acquisition_channel': ['Organic', 'Paid Search', 'Social', 'Email'],
        'signup_date': pd.to_datetime(['2022-06-01', '2022-03-15', '2023-01-10', '2021-11-20']),
    })


class TestBasicCleaningEvents:
    def test_drop_duplicates(self):
        df = _make_events_df()
        df_dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        cleaned = basic_cleaning_events(df_dup)
        assert len(cleaned) == len(df)

    def test_dropna_core_columns(self):
        df = _make_events_df()
        df.loc[0, 'session_id'] = np.nan
        cleaned = basic_cleaning_events(df)
        assert 0 not in cleaned.index

    def test_filter_session_duration(self):
        df = _make_events_df()
        df.loc[0, 'session_duration_sec'] = 999999  # exceeds MAX
        cleaned = basic_cleaning_events(df)
        assert len(cleaned) < len(df)

    def test_filter_invalid_event_type(self):
        df = _make_events_df()
        df.loc[0, 'event_type'] = 'invalid_type'
        cleaned = basic_cleaning_events(df)
        assert 'invalid_type' not in cleaned['event_type'].values


class TestBuildSessionAttributes:
    def test_output_shape(self):
        events = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        assert len(attr) == events['session_id'].nunique()

    def test_derived_time_features(self):
        events = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        for col in ['hour', 'weekday', 'date', 'year', 'month']:
            assert col in attr.columns


class TestBuildFunnelWide:
    def test_all_sessions_present(self):
        events = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        txn = pd.DataFrame({
            'transaction_id': [1], 'timestamp': pd.to_datetime(['2023-01-01 10:05:00']),
            'customer_id': [2], 'product_id': [20], 'quantity': [1],
            'discount_applied': [0], 'gross_revenue': [99.0],
            'campaign_id': [2], 'refund_flag': [0],
        })
        wide = build_funnel_wide(events, attr, txn)
        assert len(wide) == attr['session_id'].nunique()

    def test_step_columns_binary(self):
        events = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        txn = pd.DataFrame(columns=['transaction_id', 'timestamp', 'customer_id',
                                     'product_id', 'quantity', 'discount_applied',
                                     'gross_revenue', 'campaign_id', 'refund_flag'])
        wide = build_funnel_wide(events, attr, txn)
        for col in ['step1_home', 'step2_plp', 'step3_pdp', 'step4_cart', 'step5_checkout']:
            assert wide[col].isin([0, 1]).all()
```

---

### 5.2 转化率统一定义

**文件**：[python/funnel_analysis.py](../python/funnel_analysis.py) — `save_baseline` 函数

当前：

```python
'conversion_rate': round(funnel_wide['step_purchase'].mean() * 100, 2),
```

修改为同时记录两个口径：

```python
total_sessions = len(funnel_wide)
view_sessions = int(funnel_wide['step_view'].sum())
purchase_sessions = int(funnel_wide['step_purchase'].sum())

snapshot = {
    ...
    'conversion_rate': round(purchase_sessions / total_sessions * 100, 2),
    'view_to_purchase_rate': round(purchase_sessions / view_sessions * 100, 2) if view_sessions > 0 else 0,
    ...
}
```

更新 [README.md](../README.md) 中的"会话级转化率"说明，写明分母是全部会话。

---

### 5.3 品类漏斗修复

**文件**：[python/funnel_analysis.py](../python/funnel_analysis.py#L199-L201)

```python
# 修改前
view_by_cat = (
    events_with_cat.groupby('category')['session_id'].nunique()
    .reset_index(name='浏览会话')
)

# 修改后
view_by_cat = (
    events_with_cat[events_with_cat['event_type'] == 'view']
    .groupby('category')['session_id'].nunique()
    .reset_index(name='浏览会话')
)
```

---

### 5.4 损失计算修复

**文件**：[python/funnel_analysis.py](../python/funnel_analysis.py) — `compute_loss_amount` 函数

修复两个问题：流失会话去重 + 权重改为数据驱动。

```python
def compute_loss_amount(funnel_wide: pd.DataFrame,
                        transactions: pd.DataFrame = None) -> pd.DataFrame:
    """各环节损失金额量化 — 流失会话去重 + 数据驱动客单价"""
    logger.info("=" * 60)
    logger.info("11. 损失金额量化")
    logger.info("=" * 60)

    # 使用 funnel_wide 中已转化用户的客单价
    purchased = funnel_wide[funnel_wide['step_purchase'] == 1]
    aov = purchased['total_revenue'].mean() if len(purchased) > 0 else 0
    if aov == 0 and transactions is not None:
        aov = transactions['gross_revenue'].abs().mean()
    logger.info("已转化用户客单价: Y%.2f", aov)

    stage_pairs = [
        ('首页 → 列表页', 'step1_home', 'step2_plp'),
        ('列表页 → 详情页', 'step2_plp', 'step3_pdp'),
        ('详情页 → 购物车', 'step3_pdp', 'step4_cart'),
        ('购物车 → 结算页', 'step4_cart', 'step5_checkout'),
    ]

    losses = []
    cumulative_lost_sessions = set()

    for label, stage_col, next_col in stage_pairs:
        # 到达该环节但未进入下一环节的会话，排除已在前序环节流失的
        reached = set(
            funnel_wide[funnel_wide[stage_col] == 1]['session_id'].unique()
        )
        continued = set(
            funnel_wide[funnel_wide[next_col] == 1]['session_id'].unique()
        )
        lost_sessions = (reached - continued) - cumulative_lost_sessions

        reached_count = len(reached - cumulative_lost_sessions)
        lost_count = len(lost_sessions)
        cumulative_lost_sessions |= lost_sessions

        loss_rate = round(lost_count / reached_count * 100, 2) if reached_count > 0 else 0
        loss_amount = lost_count * aov

        losses.append({
            '漏斗环节': label,
            '流失会话数': lost_count,
            '入环节会话数': reached_count,
            '环节流失率(%)': loss_rate,
            '客单价': round(aov, 2),
            '估算损失金额': round(loss_amount, 2),
        })

    loss_df = pd.DataFrame(losses)
    total_loss = loss_df['估算损失金额'].sum()

    for _, row in loss_df.iterrows():
        logger.info("  %s: 流失 %s (%.2f%%), 损失 Y%s",
                    row['漏斗环节'], f"{int(row['流失会话数']):,}",
                    row['环节流失率(%)'], f"{row['估算损失金额']:,.0f}")

    logger.info("估算总损失: Y%s (去重后)", f"{total_loss:,.0f}")
    logger.info("注: 此损失为估算值，采用已转化用户客单价 × 流失会话数，未包含权重调整")

    return loss_df
```

---

### 5.5 MySQL 导出修复

**文件**：[python/import_to_mysql.py](../python/import_to_mysql.py) — `step5_export_powerbi` 函数

改为从 Python 端直接用 pandas 从 funnel_wide CSV 导出，绕过 MySQL 查询：

```python
def step5_export_powerbi() -> None:
    print("\n[5/5] Export Power BI data files...")
    POWERBI_DIR.mkdir(parents=True, exist_ok=True)

    funnel_wide = pd.read_csv(OUTPUT_DIR / 'funnel_wide.csv')

    # funnel_overview
    cols = ['session_id', 'customer_id', 'traffic_source', 'device_type',
            'experiment_group', 'step1_home', 'step2_plp', 'step3_pdp',
            'step4_cart', 'step5_checkout', 'step_purchase',
            'country', 'loyalty_tier', 'acquisition_channel']
    overview = funnel_wide[[c for c in cols if c in funnel_wide.columns]].head(10000)
    overview.to_csv(POWERBI_DIR / 'funnel_overview.csv', index=False, encoding='utf-8-sig')
    print(f"  funnel_overview.csv: {len(overview)} rows")

    # channel_analysis
    ch = funnel_wide.groupby('traffic_source').agg(
        sessions=('session_id', 'nunique'),
        purchases=('step_purchase', 'sum'),
    )
    ch['conversion_rate'] = (ch['purchases'] / ch['sessions'] * 100).round(2)
    ch.reset_index().to_csv(POWERBI_DIR / 'channel_analysis.csv', index=False, encoding='utf-8-sig')
    print(f"  channel_analysis.csv: {len(ch)} rows")

    # device_analysis
    dev = funnel_wide.groupby('device_type').agg(
        sessions=('session_id', 'nunique'),
        purchases=('step_purchase', 'sum'),
    )
    dev['conversion_rate'] = (dev['purchases'] / dev['sessions'] * 100).round(2)
    dev.reset_index().to_csv(POWERBI_DIR / 'device_analysis.csv', index=False, encoding='utf-8-sig')
    print(f"  device_analysis.csv: {len(dev)} rows")

    # country_analysis
    ctry = funnel_wide.groupby('country').agg(
        sessions=('session_id', 'nunique'),
        purchases=('step_purchase', 'sum'),
    )
    ctry['conversion_rate'] = (ctry['purchases'] / ctry['sessions'] * 100).round(2)
    ctry.reset_index().to_csv(POWERBI_DIR / 'country_analysis.csv', index=False, encoding='utf-8-sig')
    print(f"  country_analysis.csv: {len(ctry)} rows")

    print(f"\nPower BI data exported to: {POWERBI_DIR}")
```

---

### 5.6 其他小修复

**`total_revenue.abs()` 替换** — [python/data_cleaning.py](../python/data_cleaning.py#L145)：

```python
# 删除 funnel_wide['total_revenue'] = funnel_wide['total_revenue'].abs()
# 替换为：
negative_mask = funnel_wide['total_revenue'] < 0
if negative_mask.any():
    logger.warning("发现 %d 条负收入记录 (customer_id: %s), 已保留原值",
                   negative_mask.sum(),
                   funnel_wide.loc[negative_mask, 'customer_id'].unique().tolist())
```

**文档中删除 GA4 引用** — [docs/03-methodology.md](../docs/03-methodology.md#L57)：

```
- 参考：Google Analytics 4 Engagement Time、Amplitude Behavioral Cohorts。
+ 参考：电商行业行为分桶最佳实践、Amplitude Behavioral Cohorts。
```

---

## 六、修复优先级

| 优先级 | 问题 | 影响 |
|:---:|:---|:---|
| **P0** | 测试全部失效 | 面试中运行 pytest 直接暴露 |
| **P0** | 转化率口径矛盾 | 最基础的 KPI 都说不清 |
| **P0** | 流失会话 704K > 总会话 633K | 数据基本逻辑错误 |
| **P1** | 页面漏斗 131.77% | 数学不可能 |
| **P1** | 品类漏斗计数错误 | 品类分析结论不可信 |
| **P1** | 损失权重无依据 | 核心业务价值主张不严谨 |
| **P1** | MySQL 导出失败 | 数据管道不完整 |
| **P2** | total_revenue.abs() | 隐藏数据质量问题 |
| **P2** | 文档引用不准确 | 面试中可能被追问 |
| **P3** | 缺失留存/Sankey/RFM | 锦上添花，不影响基本可用性 |

---

## 附录：快速验证命令

```bash
# 1. 运行全部分析
cd d:/D30360/Documents/ecommerce_funnel_analysis
python python/main.py

# 2. 运行测试（修复后）
pytest tests/ -v

# 3. 验证核心指标一致性
python -c "
import json
with open('output/baseline_snapshot.json') as f:
    snap = json.load(f)
total = snap['total_sessions']
purch = snap['purchase_sessions']
print(f'Session CR: {purch/total*100:.2f}%')
print(f'Total revenue: Y{snap[\"total_revenue\"]:,.0f}')
"

# 4. 检查页面漏斗转化率是否 >100%
python -c "
import pandas as pd
fw = pd.read_csv('output/funnel_wide.csv')
home = fw['step1_home'].sum()
both = ((fw['step1_home']==1) & (fw['step2_plp']==1)).sum()
rate = both / home * 100
print(f'Home→PLP: both={both}, home={home}, rate={rate:.2f}%')
assert rate <= 100, f'ERROR: rate {rate:.2f}% > 100%'
print('OK')
"
```
