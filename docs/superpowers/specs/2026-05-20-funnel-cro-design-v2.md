# 电商漏斗 CRO 分析项目 — 设计文档 (v2.0)

> 2026-05-20 | v2.0 — 更新以反映实际实现的 5 表架构和 6 阶段流水线

## 1. 项目定位

| 维度 | RFM 项目 | 漏斗 CRO 项目 |
|------|----------|---------------|
| 核心问题 | 谁是高价值用户 | 哪个环节在漏钱 |
| 分析对象 | 用户（人） | 会话 + 页面行为 |
| 输出导向 | 客群 × 触达策略 | 瓶颈 × 修复方案 |
| ROI 逻辑 | 触达用户 → 增加回购 | 修复瓶颈 → 减少流失 |

---

## 2. 实际项目结构（已验证）

```
ecommerce_funnel_analysis/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   ├── events.csv          # 2,000,000 行 — 行为事件（主表）
│   ├── transactions.csv    # 103,127 行 — 交易记录
│   ├── customers.csv       # 100,000 行 — 用户画像
│   ├── products.csv        # 2,000 行 — 商品信息
│   └── campaigns.csv       # 50 行 — 广告活动
├── output/
│   ├── cleaned_events.csv  # 清洗后事件（1,999,754 行）
│   ├── funnel_wide.csv     # 漏斗宽表（633,450 会话 × 38 列）
│   ├── baseline_snapshot.json
│   ├── analysis.log
│   └── charts/             # 18 张图表（17 PNG + 1 plotly HTML）
├── python/
│   ├── __init__.py
│   ├── config.py           # 路径、MySQL、颜色、日志
│   ├── data_loader.py     # 5 表加载 + 探查 + 校验
│   ├── data_cleaning.py    # 事件清洗 + 会话属性 + 漏斗宽表
│   ├── funnel_analysis.py  # 核心漏斗 + 多维度拆解 + 统计检验 + PIE
│   ├── visualization.py    # 17 张 matplotlib/plotly 图表
│   ├── import_to_mysql.py
│   └── main.py             # 6 阶段流水线入口
├── sql/
│   ├── 01_setup_database.sql
│   ├── 02_load_data.sql
│   ├── 03_funnel_wide.sql
│   ├── 04_funnel_overview.sql
│   ├── 05_multi_dimension.sql
│   ├── 06_churn_diagnostics.sql
│   ├── 07_statistical_comparison.sql
│   └── 08_operational_export.sql
├── docs/
│   ├── 01-background.md
│   ├── 02-data-dictionary.md
│   ├── 03-methodology.md
│   └── 04-results.md
├── powerbi/
│   ├── data/
│   └── funnel_report/
└── tests/
    ├── __init__.py
    ├── test_data_cleaning.py
    └── test_funnel_analysis.py
```

---

## 3. 数据模型（已验证）

### events.csv — 行为事件表（主表）

| 列名 | 类型 | 说明 |
|------|------|------|
| event_id | VARCHAR | 事件唯一ID |
| customer_id | VARCHAR | 客户ID |
| session_id | VARCHAR | 会话ID |
| timestamp | DATETIME | 事件时间 |
| page_category | VARCHAR | 页面类型：Home / PLP / PDP / Cart / Checkout |
| event_type | VARCHAR | 事件类型：view / click / add_to_cart / bounce / purchase |
| traffic_source | VARCHAR | 流量来源：Organic / Paid Search / Social / Email / Direct |
| device_type | VARCHAR | 设备类型：mobile / desktop / tablet |
| session_duration_sec | INT | 会话总时长（秒） |
| experiment_group | VARCHAR | A/B 实验分组：Control / Variant_A / Variant_B |
| campaign_id | INT | 广告活动ID |
| product_id | INT | 商品ID（view/click/add_to_cart 事件有值） |

### transactions.csv — 交易表

| 列名 | 类型 | 说明 |
|------|------|------|
| transaction_id | VARCHAR | 交易ID |
| customer_id | VARCHAR | 客户ID |
| timestamp | DATETIME | 交易时间 |
| gross_revenue | FLOAT | 收入（含退款则为负） |
| discount_applied | FLOAT | 折扣金额 |
| refund_flag | INT | 退款标记：0/1 |
| product_id | INT | 商品ID |
| campaign_id | INT | 广告活动ID |

### customers.csv — 用户画像表

customer_id, country, age, gender, loyalty_tier, acquisition_channel, signup_date

### products.csv — 商品表

product_id, category, brand, base_price, launch_date, stock_level

### campaigns.csv — 广告活动表

campaign_id, channel, objective, start_date, end_date, budget, expected_uplift

---

## 4. 漏斗架构（已验证）

### 页面覆盖漏斗（宽松 — 独立统计，允许深链）

```
1.首页        → 300,782 会话
2.商品列表页   → 396,329 会话 (PLP > Home，因深链流量)
3.商品详情页   → 395,544 会话
4.购物车      → 172,491 会话 ← 最大断点（43.61% 交叉到达率）
5.结算页      → 172,734 会话
```

> **关键说明**：列表页（396,329）超过首页（300,782）是正常现象，因为大量用户通过广告/邮件/搜索直接落地到 PLP（深链），54.9% 的 PLP 流量是深链。交叉到达率 = 同时到达前后两页 / 到达前页，非严格顺序转化率。

### 严格路径漏斗（顺序 — 必须按时间顺序）

```
Home → PLP → PDP → Cart → Checkout
300,782 → 85,206 → 16,491 → 1,221 → 73
```

仅 73 个会话（0.02%）严格按顺序走完全流程。95.8% 的 PDP 流量通过非标准路径到达。

### 行为级漏斗

```
浏览(view) 526,869 → 点击(click) 289,028 (54.86%) → 加购(add_to_cart) 231,499 (80.10%) → 购买(purchase) 95,535 (41.27%)
```

### 漏斗步骤列名对照

| 页面漏斗列 | 阶段名 |
|------------|--------|
| step1_home | 1.首页 |
| step2_plp | 2.商品列表页 |
| step3_pdp | 3.商品详情页 |
| step4_cart | 4.购物车 |
| step5_checkout | 5.结算页 |

| 行为漏斗列 | 阶段名 |
|------------|--------|
| step_view | 浏览 |
| step_click | 点击 |
| step_add_cart | 加购 |
| step_purchase | 购买 |

---

## 5. 分析方法清单（已验证来源）

| # | 分析方法 | 来源 | 用途 |
|---|----------|------|------|
| 1 | 页面覆盖分析 | 页面独立到达统计（允许多入口） | 整体流量质量评估 |
| 2 | 严格路径漏斗 | 时间顺序过滤 | 真实有序转化率 |
| 3 | 行为级漏斗 | view→click→add_cart→purchase | 用户意图递进分析 |
| 4 | 深链流量分析 | 路径分类（深链直达 / 首页→PLP / 仅首页） | 落地页质量评估 |
| 5 | 渠道 × 设备热力图 | 交叉转化率矩阵 | 组合优化优先级 |
| 6 | 时段分析（hour × weekday） | 电商 BI 标准 | 运营排期依据 |
| 7 | 停留时长分桶（GA4 标准） | 行业基准（<60s/60-180s/180-420s/420s+） | 深度参与识别 |
| 8 | 品类漏斗 | 各品类浏览→加购→购买 | 品类差异诊断 |
| 9 | 渠道 × 流失环节矩阵 | 流失节点 × 渠道交叉 | 分渠道优化策略 |
| 10 | 卡方检验 + Bonferroni 校正 | 统计显著性（α=0.0125） | 维度差异显著性 |
| 11 | Cramér's V 效应量 | 效应强度（<0.1弱/0.1-0.3中/>0.3强） | 实际意义评估 |
| 12 | Cohen's d 效应量 | 流失组 vs 转化组对比 | 行为差异实际意义 |
| 13 | Shift-Share 归因分解 | 结构效应 + 质量效应 | 三年 CR 下降归因 |
| 14 | PIE 优先级矩阵 | PIE（Potential/Importance/Ease） | 优化排期决策 |
| 15 | 新用户 vs 老用户漏斗 | 未购买 vs 已购买分组 | 差异化运营策略 |
| 16 | 周末 vs 工作日对比 | 时段分组 | 运营策略差异 |
| 17 | Cohort 留存分析 | 首购月份 × 月差留存率 | 复购行为追踪 |

---

## 6. 关键口径说明

### 转化率双口径

| 指标 | 公式 | 数值 |
|------|------|------|
| 整体会话转化率 (Session CR) | 购买会话 / 全部会话 | 15.08% |
| 浏览到购买转化率 (View-to-Purchase CR) | 购买会话 / 浏览会话 | 18.13% |

两者分母不同，不可直接比较。统一口径使用整体会话转化率（15.08%）作为主指标。

### 漏斗逻辑校验警告

64,163 个购买会话无 checkout 记录——可能是跨会话转化（用户先加购，隔天购买）。这是数据层面的已知情况，代码已发出 WARNING 但不阻塞流程。

### 损失金额客单价来源

```python
# transactions 表单笔订单 gross_revenue 均值
aov = transactions['gross_revenue'].mean()  # Y90.36
```

总损失 = 各环节流失会话数 × 单笔订单客单价（环节间去重）。

---

## 7. 实施约束

- Python: base conda 环境
- MySQL: Docker mysql84 容器，ecommerce 数据库
- 数据: 2,000,000 条事件，633,450 会话，100,000 用户，103,127 交易
- 密码管理: .env 文件，不硬编码
- 路径管理: 全部相对于 PROJECT_ROOT，不写死绝对路径