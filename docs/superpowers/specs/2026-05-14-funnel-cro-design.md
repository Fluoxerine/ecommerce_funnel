# 电商漏斗转化率优化 (CRO) 分析项目 — 设计文档

> 2026-05-14 | 重构现有单体 notebook 为企业级模块化项目

## 1. 项目定位与 RFM 项目的区别

| 维度     | RFM 项目                | 漏斗 CRO 项目                        |
| -------- | ----------------------- | ------------------------------------ |
| 核心问题 | 谁是高价值用户          | 哪个环节在漏钱                       |
| 分析对象 | 用户（人）              | 会话 + 页面行为                      |
| 输出导向 | 客群 × 触达策略        | 瓶颈 × 修复方案                     |
| ROI 逻辑 | 触达用户 → 增加回购    | 修复瓶颈 → 减少流失                 |
| 方法论   | RFM 分群 + TGI 品类偏好 | 漏斗分析 + PIE 优先级 + 统计特征对比 |

---

## 2. 项目结构

```
ecommerce_funnel_analysis/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   └── customer_journey.csv                    # 原始数据（12719条 / 5000会话）
├── output/
│   ├── cleaned_customer_journey.csv
│   ├── funnel_wide.csv
│   ├── analysis.log
│   └── charts/                                 # 10 张可视化
├── python/
│   ├── config.py                               # 路径、MySQL配置(.env)、颜色、logger
│   ├── data_loader.py                          # 加载 + 数据概览 + 校验
│   ├── data_cleaning.py                        # 基础清洗 + 漏斗专属清洗 + 生成宽表
│   ├── funnel_analysis.py                      # 漏斗构建 + 损失金额 + 多维度拆解
│   ├── churn_diagnostics.py                    # 流失特征统计对比（卡方/t检验）
│   ├── visualization.py                        # matplotlib 8 张 + plotly 2 张
│   ├── import_to_mysql.py                      # CSV→容器→MySQL + Power BI 数据导出
│   └── main.py                                 # 主入口，串联全流程
├── sql/                                        # 8 个顺序脚本
│   ├── 01_setup_database.sql                   # 建库 + 建表（修正列名不一致）
│   ├── 02_load_data.sql                        # LOAD DATA INFILE
│   ├── 03_funnel_wide.sql                      # 清洗逻辑 + 漏斗宽表
│   ├── 04_funnel_overview.sql                  # 全链路漏斗 + 逐级转化率
│   ├── 05_multi_dimension.sql                  # 分渠道/设备/时段/国家交叉分析
│   ├── 06_churn_diagnostics.sql                # 流失金额量化
│   ├── 07_statistical_comparison.sql           # 流失 vs 转化特征对比
│   └── 08_operational_export.sql               # 运营清单导出 + PIE 排序
├── docs/
│   ├── 01-background.md                        # 业务背景与问题定义
│   ├── 02-data-dictionary.md                   # 数据字典
│   ├── 03-methodology.md                       # CRO 方法论说明
│   └── 04-results.md                           # 核心发现与业务洞察
├── operations/
│   └── cro_strategy.md                         # 转化率优化策略（按 PIE 排序）
├── powerbi/
│   ├── data/                                   # 从 MySQL 导出的 PBIR 数据文件
│   └── funnel_report/                          # PBIR 报告项目
├── tests/
│   ├── __init__.py
│   ├── test_data_cleaning.py
│   └── test_funnel_analysis.py
└── notebook/
    └── funnel_analysis.ipynb                   # 保留原 notebook 为探索记录
```

---

## 3. 分析方法清单（已自查来源）

| #  | 分析方法                    | 来源                                  | 用途                       |
| -- | --------------------------- | ------------------------------------- | -------------------------- |
| 1  | 全链路转化漏斗              | GA / Mixpanel 标准功能                | 基准：整体转化率           |
| 2  | 分渠道/设备转化率对比       | GA 默认报告维度                       | 找出高/低转化渠道          |
| 3  | 各环节损失金额量化          | CRO 标准（Monetate / Optimizely）     | 量化每个环节漏了多少钱     |
| 4  | 停留时长与转化率关系        | Amplitude 行为分析标准                | 识别参与度与转化关联       |
| 5  | 行为路径分析                | GA Behavior Flow / Mixpanel           | 发现异常路径 + 流失路径    |
| 6  | 进入路径分析                | GA Landing Page 标准报告              | 评估不同进入点的流量质量   |
| 7  | 时段分析（hour × weekday） | 电商 BI 标准维度                      | 运营排期 + 高峰期识别      |
| 8  | 购物车商品数 × 渠道交叉    | 电商 CRO 标准分析                     | 加购后流失精细拆解         |
| 9  | 统计特征对比（卡方/t检验）  | 统计学标准方法                        | 流失组 vs 转化组差异显著性 |
| 10 | 放弃购物车金额按维度拆分    | CRO / PIE 框架                        | 量化每个维度的潜在收益     |
| 11 | PIE 优先级矩阵              | PIE 框架（Potential/Importance/Ease） | 优化排期决策               |

---

## 4. 可视化清单（10 张）

| #  | 图表                                     | 库         | 说明                   |
| -- | ---------------------------------------- | ---------- | ---------------------- |
| 1  | 全链路转化漏斗（静态）                   | matplotlib | 彩色柱状图，标注转化率 |
| 2  | 全链路转化漏斗（交互）                   | plotly     | hover 显示明细         |
| 3  | 各环节损失金额瀑布图                     | matplotlib | 核心CRO图表            |
| 4  | 渠道 × 设备转化率热力图                 | matplotlib | 交叉诊断               |
| 5  | 时段(小时×周几)流量与转化率双轴         | matplotlib | 运营排期依据           |
| 6  | 各漏斗阶段停留时长箱线图（转化 vs 流失） | matplotlib | 行为差异可视化         |
| 7  | 进入路径转化率对比                       | matplotlib | 流量质量评估           |
| 8  | 购物车商品数 × 渠道转化率气泡图         | matplotlib | 三维交叉               |
| 9  | 行为路径桑基图（Top 8）                  | plotly     | 用户流转可视化         |
| 10 | PIE 优先级矩阵气泡图                     | matplotlib | 修复 ROI 决策矩阵      |

---

## 5. Power BI 仪表板（4 页）

| 页面            | 内容                                               |
| --------------- | -------------------------------------------------- |
| ① 漏斗健康度   | KPI 卡片（总流量/总转化/总损失金额）+ 漏斗图       |
| ② 流量来源质量 | 渠道 × 设备热力图 + 各渠道漏斗叠加对比 + 时段分布 |
| ③ 流失诊断     | 各节点损失金额排行 + 流失 vs 转化特征对比          |
| ④ 优化优先级   | PIE 矩阵 + 分维度优化建议（修复成本/预期收益/ROI） |

---

## 6. 统计检验计划

| 检验                             | 用途                                          | 预期结论方向             |
| -------------------------------- | --------------------------------------------- | ------------------------ |
| 卡方检验                         | 渠道/设备/国家与"是否在X节点流失"是否显著相关 | 找出有统计意义的差异维度 |
| 独立样本 t 检验                  | 流失组 vs 转化组的停留时长/商品数差异         | 量化行为差异             |
| Cohen's d                        | t 检验效应量                                  | 差异的实际意义           |
| 多组比较（ANOVA/Kruskal-Wallis） | 不同渠道/国家的转化率差异是否显著             | 判断"是否真的不同"       |

---

## 7. PIE 优先级框架（替代手工 ROI 公式）

```
PIE 总分 = Potential × Importance × Ease (每个维度 1-10)

Potential (挽回潜力): 修复该环节后能挽回的损失金额 / 总损失金额 × 10
Importance (影响面): 该环节覆盖的用户比例 × 10
Ease (实施难度): (11 - 实施难度评分 1-10)，即越容易实施得分越高

PIE 得分范围: 1-1000，排序得出优化优先级
```

每个瓶颈环节输出：

- 当期损失金额
- 涉及的会话/用户数
- 主要影响渠道/设备
- 建议修复方向
- PIE 三档得分
- 乐观/基准/保守三档挽回预估

---

## 8. 关键修正：SQL 已知问题

| 问题                                             | 当前状态                                    | 修正方案                                 |
| ------------------------------------------------ | ------------------------------------------- | ---------------------------------------- |
| SQL 第 5 节标题称 cart→checkout 为核心流失      | 错误，实际核心流失是 product→cart (40.11%) | 修正标题 + 补充 product→cart 分渠道分析 |
| CSV 列名 `Timestamp` vs SQL 列名 `EventTime` | 目前靠 LOAD DATA INFILE 位置映射            | 建表时统一为 `EventTime` + 文档说明    |
| SQL 缺少 product→cart 分渠道分析                | 缺失                                        | 新增完整的分渠道×各环节分析             |
| 清洗后的 CSV 编码不一致风险                      | 已用 utf-8-sig                              | 保持                                     |

---

## 9. 关键设计决策

| 决策          | 选择                                                                                              | 理由                                                                      |
| ------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| 列名统一      | SQL 用 EventTime，Python 用 Timestamp，config 中管理映射                                          | 不改原始 CSV 列名，保持上游兼容                                           |
| Python 模块化 | 7 分析模块 (config/loader/cleaning/funnel_analysis/churn_diagnostics/visualization/import) + main | 参照 RFM 项目，每个模块单一职责                                           |
| 流失分析方法  | 统计特征对比（非手工评分）                                                                        | 避免主观，用卡方/t检验给出有统计意义的结论                                |
| 优先级框架    | PIE（非手工 ROI 公式）                                                                            | PIE 是 CRO 领域标准框架，可操作性强                                       |
| K-Means 弃用  | 不引入聚类                                                                                        | 漏斗场景下用户分群用"流失节点"天然划分，不需要无监督学习                  |
| PIE vs ICE    | 选 PIE                                                                                            | ICE（Impact/Confidence/Ease）适合 Growth 实验场景；PIE 更适合瓶颈修复排期 |

---

## 10. 实施约束

- Python: base conda 环境（与 notebook 一致）
- MySQL: Docker mysql84 容器，ecommerce 数据库
- 数据: 12719 条行为记录，5000 个会话，1872 个用户
- 密码管理: .env 文件，不硬编码
- 路径管理: 全部相对于 PROJECT_ROOT，不写死绝对路径
