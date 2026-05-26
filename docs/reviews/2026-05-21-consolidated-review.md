# 电商漏斗分析项目 — 综合评审汇总

> 汇总日期：2026-05-21
> 汇总范围：`docs/` 下全部审查评价文档（10 份），覆盖 2026-05-18 ~ 2026-05-21 的全部评审意见
>
> 审查文档清单（10 份）：
> 1. [2026-05-18-review-findings.md](2026-05-18-review-findings.md) — 项目全面审查报告 (2026-05-18)
> 2. [2026-05-20-funnel-critique.md](2026-05-20-funnel-critique.md) — 漏斗诊断与优化讨论 (2026-05-20)
> 3. [2026-05-20-dual-perspective-review.md](2026-05-20-dual-perspective-review.md) — 数据分析师×HR双视角评审 (2026-05-20)
> 4. [2026-05-20-overall-assessment.md](2026-05-20-overall-assessment.md) — 项目整体评估 (2026-05-20)
> 5. [2026-05-20-output-issues.md](2026-05-20-output-issues.md) — 输出文档和图表问题 (2026-05-20)
> 6. [2026-05-20-hr-perspective.md](2026-05-20-hr-perspective.md) — HR/面试官视角建议
> 7. [2026-05-21-deepseek-review.md](2026-05-21-deepseek-review.md) — DeepSeek 多角度评审 (2026-05-21)
> 8. [2026-05-21-minimax-review.md](2026-05-21-minimax-review.md) — Minimax 全面评审 (2026-05-21)
> 9. [2026-05-21-comparison-deepseek.md](2026-05-21-comparison-deepseek.md) — 两报告对比分析 DeepSeek版 (2026-05-21)
> 10. [2026-05-21-comparison-minimax.md](2026-05-21-comparison-minimax.md) — 两报告对比分析 Minimax原版 (2026-05-21)

---

## 目录

1. [已解决的问题](#一已解决的问题-21-项)
2. [未解决的问题](#二未解决的问题-47-项)
3. [合并优先修复路线图](#三合并优先修复路线图)
4. [两份对比报告的元分析发现](#四两份对比报告的元分析发现)
5. [各评审文档贡献总结](#五各评审文档贡献总结)

---

## 一、已解决的问题（21 项）

以下问题已在 2026-05-18 ~ 2026-05-20 期间通过代码修改解决，当前代码验证通过。

### 1.1 逻辑错误修复（5 项）

| # | 问题 | 来源 | 修复方式 | 验证位置 |
|:---|:---|:---|:---|:---|
| 1 | **流失会话数 704K > 总会话 633K** | 05-review-findings §1.3 | `compute_loss_amount` 增加 `cumulative_lost` set 级联去重 | [funnel_analysis.py:771-784](../../python/funnel_analysis.py#L771-L784) |
| 2 | **页面漏斗转化率 131.77%** | 05-review-findings §1.1 | 确认为文档数值手工计算错误，重跑后填入实际值 | [04-results.md](../04-results.md) |
| 3 | **核心指标转化率两套矛盾口径** | 05-review-findings §1.2 | `save_baseline` 双口径：`session_conversion_rate` + `view_to_purchase_rate` | [funnel_analysis.py:1130-1155](../../python/funnel_analysis.py#L1130-L1155) |
| 4 | **品类漏斗浏览会话计数错误** | 05-review-findings §2.4 | `compute_category_funnel` 增加 `event_type == 'view'` 过滤 | [funnel_analysis.py:524-526](../../python/funnel_analysis.py#L524-L526) |
| 5 | **损失金额 AOV 为客户级累计值** | 07-dual-perspective §1.2 P0 | 改用 transactions 表 `gross_revenue.mean()` 单笔均值 | [funnel_analysis.py:748-762](../../python/funnel_analysis.py#L748-L762) |

### 1.2 代码错误修复（3 项）

| # | 问题 | 来源 | 修复方式 | 验证位置 |
|:---|:---|:---|:---|:---|
| 6 | **测试代码全部失效** | 05-review-findings §2.1 | 重写 test_data_cleaning.py 和 test_funnel_analysis.py | [tests/test_data_cleaning.py](../../tests/test_data_cleaning.py) |
| 7 | **total_revenue 静默取绝对值** | 05-review-findings §2.3 | 改为 `negative_mask` 检测 + 日志警告，保留原值 | [data_cleaning.py:198-201](../../python/data_cleaning.py#L198-L201) |
| 8 | **MySQL 导出引用不存在的 CTE 表** | 05-review-findings §2.2 | `step5_export_powerbi` 改为从 funnel_wide.csv 直接 pandas 导出 | [import_to_mysql.py:132-181](../../python/import_to_mysql.py#L132-L181) |

### 1.3 新增分析模块（7 项）

| # | 功能 | 来源 | 实现位置 |
|:---|:---|:---|:---|
| 9 | **严格路径漏斗** | 06-funnel-critique §3.2 | [funnel_analysis.py:93-164](../../python/funnel_analysis.py#L93-L164) `compute_strict_page_funnel` |
| 10 | **深链流量分析** | 06-funnel-critique §4 | [funnel_analysis.py:167-254](../../python/funnel_analysis.py#L167-L254) `compute_deep_link_analysis` |
| 11 | **新用户 vs 老用户漏斗** | 06-funnel-critique §7 | [funnel_analysis.py:380-476](../../python/funnel_analysis.py#L380-L476) `compute_new_vs_returning_funnel` |
| 12 | **周末 vs 工作日对比** | 06-funnel-critique §7 | [funnel_analysis.py:479-508](../../python/funnel_analysis.py#L479-L508) `compute_weekend_analysis` |
| 13 | **Cohort 留存分析** | 07-dual-perspective §1.3 | [funnel_analysis.py:1035-1106](../../python/funnel_analysis.py#L1035-L1106) `compute_cohort_retention` |
| 14 | **Shift-Share 趋势归因** | 06-funnel-critique §7 | [funnel_analysis.py:893-990](../../python/funnel_analysis.py#L893-L990) `compute_trend_attribution` |
| 15 | **Cramér's V 效应量** | 07-dual-perspective §1.3 | [funnel_analysis.py:861-865](../../python/funnel_analysis.py#L861-L865) `cramers_v` 函数 |

### 1.4 方法与文档改进（6 项）

| # | 改进 | 来源 | 说明 |
|:---|:---|:---|:---|
| 16 | **漏斗命名规范化** | 06-funnel-critique §3.2 | 页面覆盖分析 vs 严格路径漏斗，概念明确区分 |
| 17 | **traffic_source 大小写统一** | 06-funnel-critique §6.1 | `basic_cleaning_events` 中 `.str.strip().str.title()` |
| 18 | **趋势分析增加会话量骤降警告** | 07-dual-perspective §1.2 P0 | 变化 >30% 时 logger.warning |
| 19 | **流失特征增加循环论证免责声明** | 07-dual-perspective §1.2 P1 | [funnel_analysis.py:663-667](../../python/funnel_analysis.py#L663-L667) 注释说明 tautology |
| 20 | **SQL 监控 KPI 移除 Bounce Rate** | 07-dual-perspective §1.2 P2 | [sql/08_operational_export.sql:49-53](../../sql/08_operational_export.sql#L49-L53) |
| 21 | **渠道瓶颈双指标**(转化率瓶颈+绝对流失瓶颈) | 07-dual-perspective §1.2 P1 | [funnel_analysis.py:310-330](../../python/funnel_analysis.py#L310-L330) |

---

## 二、未解决的问题（45 项）

### 2.1 P0 级 — 影响核心结论可信度（8 项）

> **2026-05-26 独立核查确认**：Top 3 最严重问题为 P0-1（损失公式高估 2-5x）、P0-3（卡方检验方法论错误）、P0-6（Cohort 留存率静默放大 100x）。P0-6 原排在靠后位置，经讨论确认其严重程度与 P0-1 同级——静默失败且放大倍数更高。
>
> **P0-2 已移除**：原"main.py 重复导入"经复查确认不是问题——`_run_stage*` 内部 import 是有意为之的惰性加载，Stage 3 有 15+ 个分析函数，全部顶部导入会拖慢启动速度，且违背 `_safe_plot` "单图失败不中断"的设计。属于过度解读。

| # | 问题 | 来源 | 当前状态 | 预估工时 |
|:---|:---|:---|:---|:---:|
| **P0-1** | **损失量化公式概念性缺陷**（✅ 已修复）：`lost_count × AOV` 假设流失会话 100% 购买 → 已改为 `lost_count × expected_CR × AOV`，实际缩小 5.8x（¥59.76M → ¥9.33M） | DeepSeek §1.2 P0-1 | [funnel_analysis.py:788](../../python/funnel_analysis.py#L788) | 1h |

> **P1 级别已知局限（2026-05-26 复核）**：v2 公式用"该阶段到达者中历史购买比例"作为 `expected_CR`，本质假设流失用户和留存用户有相同购买概率。实际业务中流失用户往往购买意愿更低，因此当前估计仍可能偏高。严重程度为 P1（不影响数量级，但 PIE 排序可能偏差），暂不阻塞。

| **P0-3** | ✅ **SQL 卡方检验改为会话级**：`SUM(CASE WHEN event_type...)` 统计事件 → `GROUP BY session_id` 后 `MAX(has_purchase)` 构建会话级列联表 | DeepSeek §3.2 P0-8 | [sql/06_statistical_tests.sql:11-12](../../sql/06_statistical_tests.sql#L11-L12) | 0.5h |
| **P0-4** | ✅ **CRO 策略已增加实施成本估算**：P0-P3 各策略均含人天/一次性成本/月维护/ROI 预估表 | DeepSeek §4.2 P0-12 | [cro_strategy.md](../../operations/cro_strategy.md) | 1h |
| **P0-5** | ✅ **Bootstrap 95% CI 已添加**：¥9,328,398 ~ ¥9,329,335（1000 次重采样，逐次计算防 OOM） | DeepSeek §4.2 P0-13 | `compute_loss_amount` | 1.5h |
| **P0-6** | ✅ **Cohort 默认值已修复**：`.get(idx, 1)` → `.get(idx, 0)`，size=0 时 warning + 留空，消除静默 100x 放大 | Minimax §7 | [funnel_analysis.py:1083](../../python/funnel_analysis.py#L1083) | 0.5h |
| **P0-7** | ✅ **README 已增加运行前检查**：前置条件表/预期运行时间 ~4min/预期输出文件清单 | DeepSeek §7.2 P0-24 | [README.md](../../README.md) | 0.5h |
| **P0-8** | ✅ **趋势分析已强化 disclaimer**：标注会话量降 86.5%、数据完整性风险、归因仅为工作假设 | 07-dual-perspective §1.2 P0 | [04-results.md](../04-results.md) | 0.5h |
| **P0-9** | ✅ **PIE Ease 已文档化**：docstring 说明各环节评分依据 + Ease±1 敏感性范围 | 05-review-findings + DeepSeek + Minimax 三方共识 | [funnel_analysis.py:833-838](../../python/funnel_analysis.py#L833-L838) | 1h |

### 2.2 P1 级 — 影响分析质量和工程规范（19 项）

| # | 问题 | 来源 | 当前状态 | 预估工时 |
|:---|:---|:---|:---|:---:|
| **P1-1** | **Cohen's d 使用 `np.std()`(ddof=0) 而非 `ddof=1`**：公式分子用 `na-1`（样本方差系数）但分母用总体方差，不匹配 | Minimax §2.2.2 | [funnel_analysis.py:677](../../python/funnel_analysis.py#L677) | 0.5h |
| **P1-2** | **compute_churn_features 8 个 t 检验未做多重比较校正**：假阳性风险约 34% | DeepSeek §3.2 P1-9 | [funnel_analysis.py:661-705](../../python/funnel_analysis.py#L661-L705) | 0.5h |
| **P1-3** | **PIE Importance 分母锚定不一致**：各阶段分母不同（首页300K vs PLP 396K），I 值不可跨阶段比较 | Minimax §5.2.3 | [funnel_analysis.py:828-831](../../python/funnel_analysis.py#L828-L831) | 0.5h |
| **P1-4** | **compute_new_vs_returning_funnel 复制了漏斗计算逻辑**：与 `compute_page_funnel` 的交叉到达率计算完全重复 | DeepSeek §2.2 P1-5 | [funnel_analysis.py:406-424](../../python/funnel_analysis.py#L406-L424) | 1h |
| **P1-5** | **Cohort 月差计算 `dt.days // 30` 有精度bug**：跨月场景（1月31日→3月1日=29天→0个月）产生错误 | DeepSeek §2.2 P1-6 | [funnel_analysis.py:1067-1070](../../python/funnel_analysis.py#L1067-L1070) | 0.5h |
| **P1-6** | **品类漏斗/热力图未控制样本量和置信区间**：小样本品类/渠道×设备组合的转化率估计方差极大 | 05-review-findings + 07-dual-perspective + Minimax 三方共识 | [funnel_analysis.py:511-549](../../python/funnel_analysis.py#L511-L549) + L650 | 1h |
| **P1-7** | **行业基准 CRO_BENCHMARKS 未被积极使用**：config.py 定义了 10 个基准值，但分析中未做对标 | DeepSeek §4.2 P1-14 | [config.py:85-97](../../python/config.py#L85-L97) | 1h |
| **P1-8** | **策略建议缺乏速赢矩阵**：PIE 给出优先级但没有区分"大项目"和"快迭代" | DeepSeek §4.2 P1-15 | [cro_strategy.md](../../operations/cro_strategy.md) | 1h |
| **P1-9** | **图表输出格式不统一**：16 张图中 2 张 Plotly HTML + 14 张 matplotlib PNG | DeepSeek §5.2 P1-16 | [visualization.py](../../python/visualization.py) | 2h |
| **P1-10** | **配色方案缺乏无障碍设计**：红绿色区分对 ~8% 男性色盲用户不可用 | DeepSeek §5.2 P1-17 | [visualization.py:50-67](../../python/visualization.py#L50-L67) | 1.5h |
| **P1-11** | **图表缺少元信息标注**：无数据来源、分析日期、样本量 | DeepSeek §5.2 P1-18 | 全部 16 个 plot 函数 | 1h |
| **P1-12** | **测试数据不反映真实分布**：使用均匀随机分布而非真实偏态分布 | DeepSeek §6.2 P1-20 | [tests/test_funnel_analysis.py](../../tests/test_funnel_analysis.py) `_make_wide_df` | 0.5h |
| **P1-13** | **缺少黄金测试数据集做回归测试**：随机数据无法检测代码修改是否改变分析结果 | DeepSeek §6.2 P1-22 | tests/ 目录 | 2h |
| **P1-14** | **文档版本不同步**：[04-results.md](../04-results.md) 数值未标注代码版本和运行时间 | DeepSeek §7.2 P1-25 | [04-results.md](../04-results.md) | 0.5h |
| **P1-15** | **Power BI 数据导出仅 1.6%-7.9% 且使用 head()**：非随机抽样，可能只看到早期数据 | DeepSeek §8.2 P1-27 | [import_to_mysql.py:148-181](../../python/import_to_mysql.py#L148-L181) | 1h |
| **P1-16** | **Power BI 语义模型缺预定义 DAX 度量值**：用户需自己写 DAX | DeepSeek §8.2 P1-28 | [powerbi/.../model.tmdl](powerbi/funnel_report/Ecommerce%20Funnel%20CRO.SemanticModel/definition/model.tmdl) | 2h |
| **P1-17** | **文档中 GA4 引用不准确**：config.py 时长分桶注释仍写"GA4 行业标准" | 05-review-findings §3.2c | [config.py:71](../../python/config.py#L71) | 0.5h |
| **P1-18** | **品类浏览系统性低估的文档标注缺失**：PLP 列表页浏览无法关联品类，浏览→加购转化率系统性偏高 | 07-dual-perspective §1.2 P2 | 文档中未标注 | 0.5h |
| **P1-19** | **年损失 vs 三年总收入口径矛盾**：v1 损失 ¥59.76M vs 收入 ¥8.37M 并列无说明。v2 已修正损失为 ¥9.33M + README 增加口径说明行 | 07-dual-perspective §2.2 Q3 | [README.md](../../README.md) + [04-results.md](../04-results.md) 已更新 | 0.5h |

### 2.3 P2 级 — 锦上添花的优化（18 项）

| # | 问题 | 来源 | 预估工时 |
|:---|:---|:---|:---:|
| **P2-1** | `build_funnel_wide` 中 SET 操作可向量化：events 被扫描 9 次 | DeepSeek §2.2 P2-7 | 2h |
| **P2-2** | `funnel_wide` 原地修改不一致：`compute_duration_analysis` 未 copy() | Minimax §5.2.1 | 0.5h |
| **P2-3** | baseline JSON 含中文自然语言 note：应拆分为结构化字段 + 文档链接 | Minimax §6.2.2 | 0.5h |
| **P2-4** | PIE 矩阵图信息密度过高：单图编码 4 个维度 | DeepSeek §5.2 P2-19 | 1h |
| **P2-5** | test_integration 验证"不报错"而非"算对了" | DeepSeek §6.2 P2-23 | 1h |
| **P2-6** | 多处文档存在重复内容：04/06/07 三篇独立维护相同数据表格 | DeepSeek §7.2 P2-26 | 1.5h |
| **P2-7** | Power BI 报告仅 4 页，缺少趋势页和用户分层页 | DeepSeek §8.2 P2-29 | 3h |
| **P2-8** | 各国转化率高度一致的模拟数据说明缺失 | 07-dual-perspective §1.2 P3 | 0.5h |
| **P2-9** | main.py 无命令行参数和错误处理 | 07-dual-perspective §2.3 | 2h |
| **P2-10** | 缺失 Executive Summary（面向 VP/CMO 的一页摘要） | 07-dual-perspective §2.3 | 2h |
| **P2-11** | `traffic_source` 聚合 mode() 可能抛异常：当会话内所有值都不同时 fallback 到 iloc[0] | 05-review-findings §2.5 | 0.5h |
| **P2-12** | 缺失数据质量独立报告（缺失率/异常值/关联完整性） | 05-review-findings §4.2 | 1.5h |
| **P2-13** | 缺失增量效果预估（what-if："PDP→Cart 提升 5% 则增量收入？"） | 05-review-findings §4.2 | 1h |
| **P2-14** | 缺失监控告警阈值定义（什么指标跌破什么值触发什么动作） | 05-review-findings §4.2 | 1h |
| **P2-15** | missing docstring/API 文档：`_dimension_analysis`、`_safe_plot`、`_stage_runner` 等工具函数 | 260520_总体问题 §5 + Minimax §6.2.1 | 1h |
| **P2-16** | `.env` 文件含数据库密码应加入 .gitignore | 260520_总体问题 §4 | 0.5h |
| **P2-17** | 输出大 CSV 文件直接存储于仓库：cleaned_events.csv (177MB) + funnel_wide.csv (122MB) | 260520_输出结果问题 §5 | 0.5h |
| **P2-18** | ~~RFM + Sankey + 提升度分析~~ — 已移除，用户有独立 RFM 项目 | 05-review-findings §3.3 | — |
| **P2-19** | main() 函数 237 行过于庞大，应拆分为更小的编排函数 | 260520_总体问题 §2 | 2h |

---

## 三、合并优先修复路线图

### 第一阶段：本周立即修复（P0，共 8 项，~6.0h）

```
周一-周二：
├── P0-1 损失量化公式修正 (1h) ← 核心结论，¥59.76M → ¥9.33M（缩小 5.8x）
├── P0-3 SQL 卡方检验改为会话级 (0.5h) ← 方法论根本性错误，面试必问
├── P0-6 Cohort size=0 默认值修复 (0.5h) ← 静默失败，留存率放大 100 倍，与 P0-1 同级

周三-周四：
├── P0-8 趋势分析文档 disclaimer (0.5h)
├── P0-7 README 运行前检查清单 (0.5h)
├── P0-9 PIE Ease 标注假设来源 (1h)

周五：
├── P0-4 CRO 策略增加成本估算 (1h)
├── P0-5 损失金额 Bootstrap CI (1.5h)
```

### 第二阶段：本月修复（P1，共 19 项，~18h）

```
第一周：
├── P1-1  Cohen's d → ddof=1 (0.5h)
├── P1-2  churn_features 多重比较校正 (0.5h)
├── P1-3  PIE Importance 分母统一 (0.5h)
├── P1-5  Cohort 月差 Period 差值 (0.5h)
├── P1-4  抽取公共 _compute_page_coverage (1h)
├── P1-19 损失vs收入口径矛盾文档说明 (0.5h)

第二周：
├── P1-6  品类漏斗/热力图 Wilson CI (1h)
├── P1-7  行业基准对标输出 (1h)
├── P1-8  速赢矩阵 (1h)
├── P1-12 测试数据使用真实分布 (0.5h)
├── P1-14 文档增加运行元信息 (0.5h)

第三周：
├── P1-9  统一图表输出格式 (2h)
├── P1-10 配色无障碍方案 (1.5h)
├── P1-11 图表元信息标注 (1h)
├── P1-17 GA4 引用修正 (0.5h)
├── P1-18 品类浏览低估文档标注 (0.5h)

第四周：
├── P1-13 黄金测试数据集 (2h)
├── P1-15 Power BI 分层抽样 (1h)
├── P1-16 Power BI DAX 度量值 (2h)
```

### 第三阶段：择机优化（P2，共 18 项，~21h）

```
├── P2-1  build_funnel_wide SET 向量化 (2h)
├── P2-2  funnel_wide 原地修改统一 copy() (0.5h)
├── P2-3  baseline JSON 结构化 (0.5h)
├── P2-4  PIE 矩阵图拆分 (1h)
├── P2-5  test_integration 验证具体数值 (1h)
├── P2-6  文档去重 _includes/ 机制 (1.5h)
├── P2-7  Power BI 增加趋势页+用户分层页 (3h)
├── P2-8  模拟数据说明 (0.5h)
├── P2-9  main.py CLI 参数+错误处理 (2h)
├── P2-10 Executive Summary (2h)
├── P2-11 traffic_source mode() 防御性提取 (0.5h)
├── P2-12 数据质量独立报告 (1.5h)
├── P2-13 增量效果预估 what-if 模拟 (1h)
├── P2-14 监控告警阈值定义 (1h)
├── P2-15 工具函数 docstring (1h)
├── P2-16 .env 加入 .gitignore (0.5h)
├── P2-17 大 CSV 移出版本控制 (0.5h)
├── P2-18 ~~RFM + Sankey~~ — 已移除（用户有独立 RFM 项目）
├── P2-19 main() 拆分编排函数 (2h)
```

---

## 四、两份对比报告的元分析发现

> 来源：[2026-05-21-comparison-deepseek.md](2026-05-21-comparison-deepseek.md)（DeepSeek 版）和 [2026-05-21-comparison-minimax.md](2026-05-21-comparison-minimax.md)（Minimax 原版）
>
> 这两份对比报告不是直接审查项目，而是对 DeepSeek 和 Minimax 两份评审报告进行交叉验证和元分析。

### 4.1 两份评审报告的共识（7 项，可信度最高）

以下问题 DeepSeek 和 Minimax 两份独立评审同时指出，应最优先处理：

| # | 共识问题 | DeepSeek 编号 | Minimax 编号 |
|:---|:---|:---|:---|
| 1 | Cohen's d 使用 `np.std()`(ddof=0) 而非样本方差 | — | §2.2.2 |
| 2 | PIE Ease 主观赋值无依据 | P0-2 | §3.2.1 |
| 3 | 品类漏斗需要 Wilson 置信区间 | P1-3 | §3.2.4 |
| 4 | 渠道×设备热力图需要统计显著性门槛 | P1-3 | §3.2.4 |
| 5 | 流失特征存在自我指涉（tautology） | P2-11 | §2.2.4 |
| 6 | 文档版本不同步、缺运行元信息 | P1-25 | — |
| 7 | PIE Importance 分母不统一 | — | §5.2.3 |

### 4.2 Minimax 报告的硬伤 — 不应采纳

| 发现 | 判断 | 详细原因 |
|:---|:---:|:---|
| 瀑布图累积线"连接柱顶而非柱底"（Minimax §4.2.1） | ❌ **错误** | `cumulative[:-1] = [0, v0, v0+v1, v0+v1+v2]` 依次经过每根柱子的底部（=上一根柱子的顶部），形成标准阶梯式累积——**这正是瀑布图累积线的正确画法**。Minimax 建议改为 `cumulative[:-1] - values` 会产生负值 |

### 4.3 Minimax 报告中过度要求/吹毛求疵的发现 — 不建议采纳

| 发现 | 判断 | 原因 |
|:---|:---:|:---|
| Welch's t 检验增加 Shapiro-Wilk 正态性验证（§2.2.1） | ⚠️ 过度工程化 | 各组数万样本，CLT 已提供充分保证。大样本下 Shapiro-Wilk 对微小偏离也显著（p<0.001），产生误导性警报 |
| Cramér's V 参数 `min_dim` 应改为 `min_cat`（§2.2.3） | ⚠️ 吹毛求疵 | 纯命名偏好，`min_dim` 在统计学文献中也常见 |
| 热力图文字对比度"过于简单"（§4.2.2） | ⚠️ 吹毛求疵 | 当前 `mid_val` 阈值判断在实际使用中效果可接受 |
| 中文文件名跨平台问题（§6.2.3） | ⚠️ 过度谨慎 | 现代文件系统完全支持 Unicode，日期前缀命名已解决排序 |
| 渠道 KeyError 风险（§5.2.2） | ⚠️ 夸大风险 | 代码已有 `if ch in base.index and ch in curr.index` 保护 |

### 4.4 双方评审都遗漏的问题（5 项）

两份对比报告在交叉验证中发现的共同盲区：

| # | 遗漏项 | 说明 |
|:---|:---|:---|
| 1 | **AOV 计算精度损失** | transactions 无 session_id 时 AOV 只能按 customer_id 聚合再关联，收入归因模糊。两份底层报告都提了此限制，但均未量化其影响 |
| 2 | **日志输出格式** | 两份报告都未讨论日志是否应结构化（JSON）以便机器解析 |
| 3 | **page_category fallback 逻辑** | `build_funnel_wide` 中 page_category 为空时的处理方式未被任何评审覆盖 |
| 4 | **Power BI loss_data 表建模合理性** | DeepSeek 提到 TMDL 模型和度量值缺失，但未分析 loss_data 作为独立表是否为最优设计 |
| 5 | **深链流量对比图缺显著性标注** | chart 13 的渠道对比图标注了"↑+7.1pp"等差异，但未标注这些差异是否统计显著 |

### 4.5 两份底层评审报告的优劣对比

| 维度 | DeepSeek | Minimax | 综合判断 |
|:---|:---:|:---:|:---|
| 概念性/方法论深度 | ⭐⭐⭐⭐ | ⭐⭐ | DeepSeek 更深入（损失公式概念缺陷、多重比较不完整） |
| 代码细节精度 | ⭐⭐⭐ | ⭐⭐⭐⭐ | Minimax 更细致（ddof、PIE分母、Cohort size） |
| 统计严谨性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 持平。DeepSeek 指出 SQL 事件级混淆；Minimax 指出 ddof |
| 业务洞察 | ⭐⭐⭐½ | ⭐⭐ | DeepSeek 明显更优（成本估算、CI、速赢矩阵） |
| 可视化 | ⭐⭐⭐½ | ⭐⭐⭐ | DeepSeek 更全；Minimax 瀑布图判断有硬伤 |
| 测试QA | ⭐⭐⭐½ | ⭐⭐ | DeepSeek 更系统（真实分布、黄金数据集） |
| 文档可复现 | ⭐⭐⭐½ | ⭐⭐ | DeepSeek 更系统（一键复现、版本同步） |
| Power BI | ⭐⭐⭐ | 未覆盖 | DeepSeek 独有 |
| **硬伤数** | **0** | **1** | Minimax 瀑布图判断错误 |
| **问题总数** | **29** | **~21** | |
| **综合** | **⭐⭐⭐½** | **⭐⭐⭐** | DeepSeek 更全面准确 |

### 4.6 合并建议

- **以 DeepSeek 报告的 29 个发现为主线**（覆盖面广、无硬伤、业务相关性强）
- **额外采纳 Minimax 报告中 5 个细节发现**（Cohen's d ddof、PIE Importance 分母、Cohort size 默认值、funnel_wide 原位复制、baseline JSON 结构化）
- **否决 Minimax 报告中 6 个发现**（1 个硬伤 + 5 个过度要求）
- **补充双方都遗漏的 5 个盲区**

---

## 五、各评审文档贡献总结

| 文档 | 日期 | 发现问题数 | 已解决 | 未解决 | 主要贡献 |
|:---|:---|:---:|:---:|:---:|:---|
| [2026-05-18-review-findings.md](2026-05-18-review-findings.md) | 05-18 | 10 | 9 | 1 | 发现核心逻辑错误（流失去重、测试失效、MySQL 导出），提供了完整的修复代码 |
| [2026-05-20-funnel-critique.md](2026-05-20-funnel-critique.md) | 05-20 | 10 | 10 | 0 | 漏斗方法论的深度讨论（覆盖vs严格、深链分析、Bounce数据质量），驱动了最大的功能迭代 |
| [2026-05-20-dual-perspective-review.md](2026-05-20-dual-perspective-review.md) | 05-20 | 10 | 6 | 4 | 识别出 AOV 基准错误和趋势归因不严谨，提供了 HR/面试视角的高价值模拟问答 |
| [2026-05-20-overall-assessment.md](2026-05-20-overall-assessment.md) | 05-20 | 6 | 0 | 6 | 工程化视角（代码质量、测试覆盖、CI/CD、性能）— 多为 P2 级长期改进 |
| [2026-05-20-output-issues.md](2026-05-20-output-issues.md) | 05-20 | 5 | 0 | 5 | 输出和文档质量（概念混淆、格式不统一、文件管理）— 部分与 05/06 重叠 |
| [2026-05-20-hr-perspective.md](2026-05-20-hr-perspective.md) | — | — | — | — | HR/面试官的方法论参考，非问题清单，但提供了评判标准框架 |
| [2026-05-21-deepseek-review.md](2026-05-21-deepseek-review.md) | 05-21 | 29 | 0 | 29 | 9 角度全覆盖（含 Power BI），识别出损失公式概念缺陷和 SQL 事件级混淆等深层次问题 |
| [2026-05-21-minimax-review.md](2026-05-21-minimax-review.md) | 05-21 | 21 | 0 | 21 | 代码细节精准（Cohen's d ddof、PIE Importance 分母、Cohort size=0），但瀑布图判断有误 |
| [2026-05-21-comparison-deepseek.md](2026-05-21-comparison-deepseek.md) (DeepSeek版) | 05-21 | — | — | — | 元分析：识别 Minimax 硬伤（瀑布图）+ 过度要求（正态性等）+ 两报告优劣对比 |
| [07-report-comparison-*-minimax原版.md](2026-05-21-comparison-minimax.md) (Minimax原版) | 05-21 | — | — | — | 元分析：7 项双方共识 + 5 项共同盲区 + 合并修复路线图 |

### 关键里程碑

```
2026-05-18  05-review-findings       → 发现 10 个问题，P0 级全部修复
2026-05-20  06-funnel-critique       → 驱动双漏斗+深链+新老用户+趋势归因等大量功能新增
2026-05-20  07-dual-perspective      → 发现 AOV + 趋势 + 瓶颈定义等深层问题，部分修复
2026-05-20  260520_总体/输出问题      → 工程化和文档层面建议，基本未处理
2026-05-21  DeepSeek 多角度评审       → 发现 29 个新问题（代码+统计+业务+Power BI+测试全面覆盖）
2026-05-21  Minimax 全面评审          → 补充 5 个 DeepSeek 遗漏的代码细节，但有 1 处硬伤
2026-05-21  两份对比报告（元分析）       → 交叉验证：确认 7 项双方共识、否决 Minimax 6 项发现、发现 5 项共同盲区
```

### 修复进度总览

```
总问题数（去重后）: 71
├── 原始已解决:     21  (30%)  ← 2026-05-18 ~ 05-20 修复
├── 本轮新增已解决: 40  (56%)  ← 2026-05-26 Claude Code 批量修复
│   ├── P0 已解决:  8/8  (100%)
│   ├── P1 已解决: 15/19 (79%)
│   └── P2 已解决: 17/18 (94%)
├── 剩余未解决:     10  (14%)
│   ├── P0 剩余:     0   ← ✅ 全部完成
│   ├── P1 剩余:     4   ← P1-13/15/16 + P1-14 部分（工具链/数据集依赖）
│   ├── P2 剩余:     1   ← P2-6 文档去重（低优先级）
│   └── P2 跳过:     1   ← P2-18 RFM（用户有独立项目）
└── 共同盲区:        5   (7%)  ← 两份底层报告都遗漏，暂无明确修复方案

其中 Minimax 特有发现中:
├── 应采纳:          5  (已合并入 P0/P1/P2)
└── 不应采纳:        6  (1 硬伤 + 5 过度要求)

其中源文档遗漏项（本次核查补充）:
├── P1 补充:         1  (P1-19 损失vs收入口径矛盾 — 已修复)
└── P2 补充:         9  (P2-11 ~ P2-19 — 已修复 8/9，P2-18 跳过)

预计总剩余工时: ~10h
├── P1-13 黄金测试集: 2.0h
├── P1-15/16 + P2-7 Power BI: 6.0h (需 pbi-cli)
└── P2-6 文档去重: 1.5h
```

---

> **总结**：经过 4 天 10 份评审文档的迭代（含 2 份元分析对比报告），项目已经从一个"有逻辑错误和工程问题的分析项目"演进为"方法论体系完整、大部分核心bug已修复的分析项目"。本次核查修正了 4 处数据矛盾（文档数量、已解决总数、子项计数、目录缺失），补充了 10 项源文档遗漏问题（含 1 项 P1 面试高危问题 + 9 项 P2 工程优化），总计 71 个去重问题（21 已解决 + 45 未解决 + 5 共同盲区，P2-18 RFM 已移除）。两份对比报告的交叉验证进一步明确了：7 项高置信度共识问题应优先处理；Minimax 报告的 6 项发现不应采纳（1 硬伤 + 5 过度要求）。

**Top 3 最优先修复（2026-05-26 复核确认）**：
1. **P0-1 损失量化公式** — `lost_count × AOV` 假设流失会话 100% 购买，高估 5.8 倍（¥59.76M → ¥9.33M，已修复）
2. **P0-3 SQL 卡方检验事件级** — 方法论根本性错误，违反独立性假设
3. **P0-6 Cohort size=0 默认值** — 静默失败，留存率放大 100 倍，原文档严重低估其影响（已从 P0 末位提升至 Top 3）

当前剩余工作主要为工具链依赖项（Power BI 3 项需 pbi-cli）和低优先级工程优化（P2-6 文档去重、P1-13 黄金测试集）。预计投入 ~10 工时可将剩余 5 项全部收尾，达到 100% 完成率。
