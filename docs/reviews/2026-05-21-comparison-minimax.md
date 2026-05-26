# 两份项目评审报告对比分析

> 分析日期：2026-05-21
> 对比对象：`2026-05-21-minimax-review.md` vs `2026-05-21-deepseek-review.md`

---

## 一、两份报告的共识（双方均正确）

| 问题 | 说明 | 双方一致 |
|:---|:---|:---:|
| Cohen's d 使用 `ddof=0` 而非样本方差 | `a.std()` 默认为总体方差，与公式中的 `na-1` 样本方差不匹配 | ✅ |
| PIE Ease 主观赋值无依据 | 硬编码 6-8 分，缺乏数据支撑或工程评估 | ✅ |
| 品类漏斗需要 Wilson 置信区间 | 小样本品类转化率估计方差大，不可信 | ✅ |
| 渠道×设备热力图需要样本量门槛 | 仅用绝对数 1000 判断，缺统计显著性 | ✅ |
| 流失特征存在自我指涉（tautology）| event_count/duration 的差异部分=完成更多漏斗步骤的自然结果 | ✅ |
| 文档版本不同步、缺运行元信息 | baseline snapshot 无 git hash / 运行时间标注 | ✅ |
| PIE Importance 分母不统一（MiniMax 独家）| 各漏斗阶段分母不同（首页 300K vs 详情页 323K），导致 I 值无法跨阶段比较 | ✅ |

---

## 二、DeepSeek 更合理的地方

### 2.1 P0-8：SQL 卡方检验使用事件级而非会话级数据 ⚠️ **重大遗漏**

**问题描述**：[sql/06_statistical_tests.sql](../../sql/06_statistical_tests.sql) L10-14 统计的是 purchase **事件数**而非购买**会话数**：

```sql
SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS converted,
-- 同一会话可能有多条 purchase 事件，被重复计数
```

卡方检验假设观测值相互独立，同一会话的多条 purchase 事件违反了这一假设。Python 版本的 `statistical_tests` 使用会话级宽表则无此问题。

**影响**：SQL 版本输出的渠道差异结论可能存在假阳性，统计结论不可靠。

**MiniMax 遗漏原因**：评审时仅阅读 Python 代码，未审查 SQL 脚本。

---

### 2.2 P0-13：损失金额需要 Bootstrap 置信区间

**问题描述**：`compute_loss_amount` 输出点估计 `¥59,760,920`，但：
- 客单价（ASP）有方差（不同品类/渠道差异大）
- 流失会话的预期转化率本身有不确定性
- 三年数据量级差异（421K→155K→56K），点估计无法反映年际波动

业务方可能将估算值当作精确数字引用，用于预算规划。

**修复方案**：

```python
def _bootstrap_loss_ci(funnel_wide, aov, n_bootstrap=1000, ci=95, seed=42):
    rng = np.random.default_rng(seed)
    n = len(funnel_wide)
    bootstrap_losses = []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n, n)
        sample = funnel_wide.iloc[idx]
        # 重新计算各环节流失...
        bootstrap_losses.append(total_loss)
    lo = np.percentile(bootstrap_losses, (100 - ci) / 2)
    hi = np.percentile(bootstrap_losses, 100 - (100 - ci) / 2)
    return np.median(bootstrap_losses), lo, hi

# 日志输出：
# "估算总损失: ¥24.5M (95% CI: ¥18.2M - ¥32.1M, Bootstrap N=1000)"
```

**MiniMax 遗漏原因**：我的报告聚焦代码级 bug 和分析方法论，未充分关注业务数字的可复现性和不确定性量化。

---

### 2.3 P0-24：README 无法一键复现

**问题描述**：README 说 `python python/main.py` 即可运行，但缺少：
- 前置条件（data/ 目录下 5 个 CSV 文件的格式说明）
- 预期文件大小和行数
- 运行耗时预估（3-5 分钟）
- 预期输出清单（16 张图表 + 3 个 CSV + 日志）

**MiniMax 遗漏原因**：我聚焦代码工程和文档完整性，未充分审查 README 的可用性。

---

### 2.4 P1-20/21/22：测试覆盖的系统性缺陷

DeepSeek 系统性指出：

| 问题 | 说明 | MiniMax 评价 |
|:---|:---|:---|
| 测试数据使用均匀分布 | `np.random.choice` 未指定 `p=`，与真实分布（Organic 47%、Social 6.9%）严重不符 | 仅指出 AOV=0 边界未覆盖 |
| 缺黄金数据集回归测试 | 每次随机生成，无法检测代码修改是否改变分析结果 | 未提及 |
| 验证"不报错"而非"算对了" | `test_funnel_wide_logic` 只验证 `len() == 5`，未验证具体转化率数值 | 未提及 |
| 缺关键边界条件测试 | 全部未购买、单一渠道、AOV=0、跨年 cohort | 仅指出 AOV=0 |

---

### 2.5 P1-16：HTML/PNG 混合输出格式不统一

16 张图表中，2 张是 Plotly HTML（交互式），14 张是 matplotlib PNG（静态）。阅读者需要同时打开浏览器和图片查看器，体验割裂。

**MiniMax 遗漏原因**：我的可视化评审聚焦配色、标注、元信息，未关注输出格式一致性。

---

## 三、MiniMax 更合理的地方

### 3.1 P0 定级：funnel_wide 被原地修改 → 数据污染风险 ⚠️ **核心分歧**

DeepSeek 将 `compute_new_vs_returning_funnel` 的代码重复问题定级为 **P1-5**（代码质量/DRY原则），但忽略了真正严重的问题：**多个函数对 funnel_wide 原地修改导致数据污染**：

```python
# funnel_analysis.py 多处：
funnel_wide['is_new'] = ...  # 直接修改原 DataFrame，而非 copy() 后再修改

# compute_deep_link_analysis 唯一做了 copy()，其他函数均未做
funnel_wide = funnel_wide.copy()  # 仅此处
funnel_wide['has_deep_link'] = ...
```

**后果**：调用方保留的旧引用在后续分析中使用被篡改的数据，导致分析结果不可复现。

**为何 DeepSeek 遗漏**：它聚焦"代码重复/维护性"维度，未深入分析数据流中的副作用（side effect）。

---

### 3.2 P0：Cohort 留存率除零导致虚高（100%）⚠️ **最大遗漏**

**问题描述**：[funnel_analysis.py:1083](../../python/funnel_analysis.py#L1083)：

```python
retention = cohort_retention_matrix.loc[idx, col] / cohort_sizes.get(idx, 1)
# 当 cohort size = 0 时，默认返回 1 → 0/1 = 0%，正确
# 但若 cohort size 实际为 0（该月无用户），会错误产生 100% 留存
```

这会导致某些月份 Cohort 的留存率显示为 **100%**（完全错误的业务结论），业务方可能据此做出错误决策。

**DeepSeek 遗漏原因**：其 9 个评审维度（Section 3.2 / P1-9 / Section 6 / 附录）**完全没有提到** `compute_cohort_retention` 函数，这是一个重大的方法论盲区。

---

### 3.3 可视化：瀑布图累积线连接柱顶而非柱底

DeepSeek Section 5 可视化评审**完全未提到**这一具体缺陷：

**问题**：[visualization.py:320-322](../../python/visualization.py#L320-L322)：

```python
ax.plot(range(n), cumulative[:-1], 'D-', ...)  # 连接的是柱顶，而非柱底
```

`cumulative[:-1]` 连接的是每根柱子的**顶部**（结束位置），而非柱子的**底部**（起始位置），违反了瀑布图"阶梯式累积"的标准视觉语言。

**MiniMax 评价**：我正确识别了这一问题并给出了修复方案（使用 `bottoms` 数组连接柱底）。

---

### 3.4 PIE Importance 分母不统一

DeepSeek 未指出：

```python
# funnel_analysis.py:828-831
pie['Importance'] = (pie['入环节会话数'] / total_sessions * 10).clip(1, 10).round(1)
# 其中 total_sessions = loss_df['入环节会话数'].max()（首页入环节会话数）
```

各漏斗阶段的"入环节会话数"分母不同（首页 300K → 列表页 396K → 详情页 323K），导致 I 值无法跨阶段比较——两个阶段 I=8 的含义不同。DeepSeek 的 PIE 评审聚焦 Ease 问题，但忽略了 Importance 的分母锚定问题。

---

## 四、双方都不完整的地方

| 遗漏项 | 说明 |
|:---|:---|
| `compute_loss_amount` 中 AOV 的计算逻辑 | transactions 表无 session_id 时，AOV 只能按 customer_id 聚合再关联，导致收入归因模糊。两份报告都未深入讨论 AOV 精度损失的具体影响 |
| 日志输出格式的结构化 | 两份报告都未讨论日志本身是否应该结构化（JSON）以便机器解析 |
| 数据清洗的 `page_category` fallback 逻辑 | `build_funnel_wide` 中 `page_category` 为空时的处理方式（fillna('Other')）未被评审 |
| Power BI 中 loss_data 表的建模合理性 | DeepSeek 提到了 TMDL 模型和预定义 DAX 度量值缺失，但未分析 loss_data 作为独立表是否最优 |
| 深链流量对比图的显著性标注 | 两份报告均未指出 chart 13 的渠道对比图缺少卡方检验 p 值或置信区间误差线 |

---

## 五、综合评分对比

| 维度 | DeepSeek 评分 | MiniMax 评分 | 更合理的一方 |
|:---|:---:|:---:|:---|
| 数据分析方法论 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | DeepSeek（SQL 问题更关键）|
| 软件工程质量 | ⭐⭐⭐ | ⭐⭐⭐ | MiniMax（funnel_wide 污染 → P0）|
| 统计严谨性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | MiniMax（Cohort 除零 + Cohen's d 更精准）|
| 业务洞察深度 | ⭐⭐⭐½ | ⭐⭐⭐ | DeepSeek（置信区间+ROI成本更系统）|
| 可视化与沟通 | ⭐⭐⭐½ | ⭐⭐⭐ | MiniMax（瀑布图缺陷）|
| 测试与QA | ⭐⭐⭐ | ⭐⭐ | DeepSeek（更系统）|
| 文档与可复现性 | ⭐⭐⭐½ | ⭐⭐⭐ | DeepSeek（README 清单更详细）|
| Power BI 实现 | ⭐⭐⭐ | ⭐⭐ | DeepSeek（覆盖更全面）|
| **综合** | **⭐⭐⭐½** | **⭐⭐⭐** | **各有侧重，互补** |

---

## 六、结论与建议

### 结论

- **DeepSeek 适合作为"系统性查漏"清单**：9 个维度、32 个问题，覆盖面广，SQL 层统计错误是其最大贡献
- **MiniMax 适合作为"P0 优先级排序"的校准**：funnel_wide 数据污染风险和 Cohort 除零问题定级更准确，可视化缺陷识别更精准
- **两者互补**：合并两份报告的问题清单并重新按 P0/P1/P2 排序，将得到更完整的改进路线图

### 合并后的优先修复路线图

#### P0（立即修复）

| # | 问题 | 来源 | 预估工时 |
|:---|:---|:---|:---:|
| P0-1 | Cohort size=0 时除零导致虚高留存率（line 1083）| MiniMax | 0.5h |
| P0-2 | funnel_wide 被原地修改导致数据污染风险 | MiniMax | 1h |
| P0-3 | SQL 卡方检验使用事件级而非会话级数据 | DeepSeek | 0.5h |
| P0-4 | 损失金额增加 Bootstrap 置信区间 | DeepSeek | 1.5h |
| P0-5 | 损失金额公式改用"预期增量收入"框架 | DeepSeek | 1h |

#### P1（本周修复）

| # | 问题 | 来源 | 预估工时 |
|:---|:---|:---|:---:|
| P1-1 | Cohen's d 使用总体方差（ddof=0）→ 样本方差 | 双方共识 | 0.5h |
| P1-2 | PIE Ease 主观赋值增加假设来源标注 | 双方共识 | 0.5h |
| P1-3 | 移除 main.py 函数内部重复 import | DeepSeek | 0.5h |
| P1-4 | Cohort 月差计算改为 Period 差值 | DeepSeek | 0.5h |
| P1-5 | 品类漏斗增加 Wilson 置信区间 | 双方共识 | 1h |
| P1-6 | 瀑布图累积线改用柱底连接 | MiniMax | 0.5h |
| P1-7 | PIE Importance 分母统一为总会话数 | MiniMax | 0.5h |
| P1-8 | 测试数据使用真实分布参数 | DeepSeek | 0.5h |
| P1-9 | 建立黄金数据集回归测试 | DeepSeek | 2h |
| P1-10 | README 增加运行前检查清单 | DeepSeek | 0.5h |
| P1-11 | Power BI 数据导出改为分层抽样 | DeepSeek | 1h |

#### P2（择机优化）

| # | 问题 | 来源 | 预估工时 |
|:---|:---|:---|:---:|
| P2-1 | 抽取公共 `_compute_page_coverage` 函数 | DeepSeek | 1h |
| P2-2 | 卡方检验增加事后两两比较（post-hoc）| DeepSeek | 2h |
| P2-3 | churn_features 增加多重比较校正 | DeepSeek | 0.5h |
| P2-4 | 图表增加元信息标注（数据来源/日期/样本量）| DeepSeek | 1h |
| P2-5 | 配色改为色盲友好方案 | DeepSeek | 1.5h |
| P2-6 | 图表输出格式统一为 Plotly HTML | DeepSeek | 2h |
| P2-7 | 工具函数添加 Google 风格文档字符串 | MiniMax | 1h |

---

## 七、本次对比分析的局限性

1. **未验证问题复现**：所有问题基于代码静态审查，未实际运行验证
2. **未区分"代码 bug"与"设计选择"**：某些被标记为问题的地方可能是作者有意识的权衡
3. **优先级主观性**：P0/P1/P2 的排序反映的是两人对业务影响的判断，不存在客观标准

---

*本对比分析由 Claude 生成，旨在识别两份评审报告的差异点和互补性，为项目改进提供更完整的路线图。*