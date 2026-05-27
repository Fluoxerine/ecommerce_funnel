# Power BI 报告操作指南

> 适用版本：Power BI Desktop 2024+ | 报告版本：2026-05-26 | 数据：模拟电商数据

---

## 目录

1. [环境准备](#一环境准备)
2. [首次加载报告](#二首次加载报告)
3. [数据刷新](#三数据刷新)
4. [报告页面详解](#四报告页面详解)
5. [TMDL 语义模型](#五tmdl-语义模型)
6. [DAX 度量值参考](#六dax-度量值参考)
7. [常见问题排查](#七常见问题排查)
8. [数据导出流程](#八数据导出流程)

---

## 一、环境准备

### 必需软件

| 软件 | 版本要求 | 用途 |
|:---|:---|:---|
| Power BI Desktop | 2024 年 3 月版或更新 | 打开 .pbip 项目文件 |
| Python | 3.13+ | 生成 Power BI 数据源 CSV |
| pbi-cli (可选) | 最新版 | 命令行预览/验证/导出 |

### 项目文件结构

```
powerbi/
├── HOWTO.md                                  # 本指南
├── README.md                                 # 项目概述
├── data/                                     # 数据源 CSV（由 Python 生成）
│   ├── funnel_overview.csv                   # 漏斗阶段汇总
│   ├── funnel_wide_export.csv                # 会话级宽表（主事实表）
│   ├── channel_analysis.csv                  # 渠道维度
│   ├── device_analysis.csv                   # 设备维度
│   └── country_analysis.csv                  # 国家维度
└── funnel_report/                            # PBIR 报告项目
    ├── Ecommerce Funnel CRO.pbip             # 项目入口（双击打开）
    ├── Ecommerce Funnel CRO.Report/          # 报告定义
    │   └── definition/pages/
    │       ├── funnel_health/                # ① 漏斗健康度
    │       ├── traffic_quality/              # ② 流量质量
    │       ├── churn_diagnostics/            # ③ 流失诊断
    │       └── priority_matrix/              # ④ 优化优先级
    └── Ecommerce Funnel CRO.SemanticModel/   # TMDL 语义模型
        └── definition/
            ├── model.tmdl                    # 表/列/度量值定义
            └── tables/                       # 分区数据源定义
```

---

## 二、首次加载报告

### Step 1：生成数据源

首先确保已运行过主分析（生成 `output/funnel_wide.csv`）：

```bash
cd ecommerce_funnel_analysis
python python/main.py
```

然后生成 Power BI 数据文件（不需要 MySQL/Docker）：

```bash
python -c "
import sys; sys.path.insert(0, '.')
from python.import_to_mysql import step5_export_powerbi
step5_export_powerbi()
"
```

确认 `powerbi/data/` 目录下生成了以下 CSV：

```bash
ls powerbi/data/
# funnel_overview.csv      — 漏斗阶段汇总（5 行）
# funnel_wide_export.csv   — 分层抽样宽表（~63K 行）
# channel_analysis.csv     — 渠道维度（5 行）
# device_analysis.csv      — 设备维度（4 行）
# country_analysis.csv     — 国家维度（7 行）
```

### Step 2：打开报告

双击 `powerbi/funnel_report/Ecommerce Funnel CRO.pbip`，Power BI Desktop 自动加载报告和语义模型。

### Step 3：配置数据源路径

首次打开时，Power BI 可能提示数据源凭据或路径错误：

1. 「文件」→「选项和设置」→「数据源设置」
2. 逐一选中每个 CSV 数据源 →「更改源」→ 浏览到 `powerbi/data/` 下对应的 CSV 文件
3. 权限级别选择「忽略隐私级别」(Organizational)
4. 点击「刷新」加载数据

### Step 4：验证数据加载

刷新完成后，切换到「漏斗健康度」页面，确认 KPI 卡片显示：

| KPI | 预期值 |
|:---|---:|
| 总会话数 | 633,450 |
| 会话转化率 | 15.08% |
| 年估算损失 | ¥9.33M |

如果数字不符，参考 [§7 常见问题排查](#七常见问题排查)。

---

## 三、数据刷新

### 常规刷新

每次运行 `python python/main.py` 后，`powerbi/data/` 下的 CSV 自动更新。在 Power BI Desktop 中：

1. 点击「主页」→「刷新」
2. 或按 `Ctrl+Alt+F5`

### 完全重载

如果刷新后数据仍然陈旧：

1. 「主页」→「刷新」下拉 →「刷新所有数据源」
2. 如果仍无效，关闭并重新打开 `.pbip` 文件

---

## 四、报告页面详解

### ① 漏斗健康度 (Funnel Health)

**目的**：一览全局漏斗状态，快速判断哪个环节最严重。

| 可视化 | 类型 | 数据源 | 显示内容 |
|:---|:---|:---|:---|
| KPI 卡片 ×3 | Card | funnel_overview 度量值 | 总会话 633,450 / 转化率 15.08% / 年损失 ¥9.33M |
| 漏斗柱状图 | Clustered Bar | funnel_overview | Home→PLP→PDP→Cart→Checkout 各阶段到达会话数 |
| 页面漏斗表 | Table | funnel_overview | 阶段 / 到达会话数 / 交叉到达率 / 整体到达率 |

**关键数字**：

| 指标 | 值 | 说明 |
|:---|---:|:---|
| 总会话 | 633,450 | 全部独立 session_id |
| 首页到达 | 300,782 | 47.5% 的会话经过首页 |
| PLP 到达 | 396,329 | 62.6%，超过首页（深链流量） |
| Checkout 到达 | 172,734 | 27.3% |
| 会话转化率 | 15.08% | 95,535 购买 / 633,450 总会话 |

---

### ② 流量质量 (Traffic Quality)

**目的**：按渠道和设备拆解转化率，找出流量质量问题。

| 可视化 | 类型 | 数据源 | 显示内容 |
|:---|:---|:---|:---|
| 渠道柱状图 | Clustered Bar | channel_analysis | 5 渠道转化率对比 |
| 设备柱状图 | Clustered Bar | device_analysis | Desktop/Mobile/Tablet/UNKNOWN 转化率 |
| 渠道×设备热力图 | Matrix | funnel_wide_export | 交叉维度转化率矩阵 |

**关键数字**：

| 渠道 | 会话数 | 转化率 | 特点 |
|:---|---:|---:|:---|
| Organic | 296,541 | 12.98% | 流量最大（46.8%），转化率居中 |
| Email | 118,162 | 18.87% | 转化率最高 |
| Direct | 94,398 | 12.02% | 转化率最低 |
| Paid Search | 80,741 | 19.67% | 转化率最高之一，但流量小 |
| Social | 43,608 | 17.22% | 中等流量和转化率 |

---

### ③ 流失诊断 (Churn Diagnostics)

**目的**：定位各环节流失严重程度 + 流失用户 vs 转化用户特征对比。

| 可视化 | 类型 | 数据源 | 显示内容 |
|:---|:---|:---|:---|
| 损失瀑布图 | Waterfall | loss_data | 各环节年损失金额 |
| 流失率柱状图 | Clustered Bar | loss_data | 各环节流失率 (%) |
| 渠道×环节热力图 | Matrix | funnel_wide_export | 各渠道在各环节的流失分布 |
| 流失特征对比表 | Table | funnel_wide_export | 流失组 vs 转化组：停留时长 / 事件数 |

**关键数字**（基于 v2 损失公式）：

| 环节 | 流失会话 | 流失率 | 预期 CR | 年损失 |
|:---|---:|---:|---:|---:|
| 首页→列表页 | 121,895 | 40.53% | 17.57% | ¥1.93M |
| 列表页→详情页 | 160,998 | 40.62% | 17.13% | ¥2.49M |
| 详情页→购物车 | 239,854 | 74.22% | 17.08% | **¥3.70M** |
| 购物车→结算页 | 73,361 | 74.05% | 18.12% | ¥1.20M |
| **合计** | **596,108** | — | — | **¥9.33M** |

95% Bootstrap CI（1000 次重采样）：¥9,328,398 ~ ¥9,329,335

---

### ④ 优化优先级 (Priority Matrix)

**目的**：PIE 框架排序优化方向，辅助资源分配决策。

| 可视化 | 类型 | 数据源 | 显示内容 |
|:---|:---|:---|:---|
| PIE 气泡图 | Scatter | loss_data | X=Potential, Y=Importance, 气泡大小=PIE得分 |
| PIE 数据表 | Table | loss_data | 环节 / Potential / Importance / Ease / PIE得分 / Ease±1 |

**关键数字**：

| 优先级 | 环节 | PIE 得分 | Potential | Importance | Ease | Ease±1 范围 |
|:---:|:---|---:|---:|---:|---:|:---:|
| P0 | 详情页→购物车 | 122 | 4.0 | 5.1 | 6.0 | 102-143 |
| P1 | 列表页→详情页 | 102 | 2.7 | 6.3 | 6.0 | 85-119 |
| P2 | 首页→列表页 | 69 | 2.1 | 4.7 | 7.0 | 59-79 |
| P3 | 购物车→结算页 | 17 | 1.3 | 1.6 | 8.0 | 15-19 |

> **Ease 评分说明**：基于典型电商优化经验估算（见代码 docstring），非数据驱动。PIE_Ease±1 列展示了 Ease 浮动 ±1 时得分的敏感性范围。实际项目中建议用工程估点替换。

---

## 五、TMDL 语义模型

### 模型概览

语义模型位于 `powerbi/funnel_report/Ecommerce Funnel CRO.SemanticModel/definition/`，使用 TMDL (Tabular Model Definition Language) 格式。

### 表结构

| 表名 | 类型 | 行数 | 说明 |
|:---|:---|:---:|:---|
| `funnel_wide_export` | 导入 (CSV) | 63,344 | 会话级宽表（分层抽样 10%） |
| `funnel_overview` | 导入 (CSV) | 5 | 漏斗阶段汇总 |
| `channel_analysis` | 导入 (CSV) | 5 | 渠道维度分析 |
| `device_analysis` | 导入 (CSV) | 4 | 设备维度分析（含 UNKNOWN） |
| `country_analysis` | 导入 (CSV) | 7 | 国家维度分析 |
| `loss_data` | 计算表 (DAX) | 4 | 损失金额 + PIE 优先级 |

### loss_data 计算表定义

`loss_data` 是从分析结果派生的计算表。在 TMDL 模型中定义为：

```tmdl
table loss_data
    lineageTag: ...
    partition 'Default' = 
        datatable(
            "漏斗环节": string,
            "流失会话数": int64,
            "入环节会话数": int64,
            "环节流失率": double,
            "预期转化率": double,
            "客单价": double,
            "估算损失金额": double,
            "Potential": double,
            "Importance": double,
            "Ease": int64,
            "PIE得分": int64,
            {
                {"首页 → 列表页", 121895, 300782, 40.53, 17.57, 90.36, 1934868, 2.1, 4.7, 7, 69},
                {"列表页 → 详情页", 160998, 396329, 40.62, 17.13, 90.36, 2491794, 2.7, 6.3, 6, 102},
                {"详情页 → 购物车", 239854, 323259, 74.22, 17.08, 90.36, 3701056, 4.0, 5.1, 6, 122},
                {"购物车 → 结算页", 73361, 99102, 74.05, 18.12, 90.36, 1201121, 1.3, 1.6, 8, 17}
            }
        );
```

### 手动更新 loss_data

如果重新运行 Python 分析后数字变化，需要手动更新 loss_data：

1. 在 Power BI Desktop 中，「建模」→「新建表」
2. 复制上方 DAX 并替换数值为最新运行结果
3. 删除旧的 loss_data 表

或使用 pbi-cli 更新 TMDL：

```bash
pbi model table update loss_data --file loss_data.tmdl
pbi model commit -m "update loss_data from 2026-05-26 run"
```

---

## 六、DAX 度量值参考

以下度量值应在语义模型中预定义（TMDL 或手动创建）：

### funnel_overview 表

```dax
-- 总会话数
Total Sessions = SUM(funnel_overview[会话数])

-- 总购买会话数
Total Purchases = SUM(funnel_overview[购买会话数])

-- 会话转化率（百分比）
Session CR = DIVIDE([Total Purchases], [Total Sessions])

-- 总损失金额
Total Loss = SUM(loss_data[估算损失金额])
```

### funnel_wide_export 表

```dax
-- 各渠道会话数
Sessions by Channel = DISTINCTCOUNT(funnel_wide_export[session_id])

-- 各渠道转化率
CR by Channel = 
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(funnel_wide_export[session_id]), 
                  funnel_wide_export[step_purchase] = 1),
        DISTINCTCOUNT(funnel_wide_export[session_id])
    )

-- 首页到达会话
Home Sessions = SUM(funnel_wide_export[step1_home])

-- PLP 到达会话
PLP Sessions = SUM(funnel_wide_export[step2_plp])
```

### 安装度量值

如果 TMDL 模型中缺少这些定义，可以：

**方法 A — Power BI Desktop 手动创建**：
1. 右侧「数据」窗格展开对应表
2. 右键 →「新建度量值」
3. 粘贴 DAX 公式

**方法 B — pbi-cli 批量创建**：
```bash
pbi model measure create \
  --table funnel_overview \
  --name "Session CR" \
  --expression "DIVIDE(SUM(funnel_overview[购买会话数]), SUM(funnel_overview[会话数]))"
```

---

## 七、常见问题排查

### Q1：KPI 卡片显示空白

1. 确认度量值已创建（参考 [§6](#六dax-度量值参考)）
2. 检查 visual 的「字段」面板是否正确绑定了度量值
3. 「建模」→「新建度量值」手动创建缺失的度量值

### Q2：刷新后数据为 0

1. 检查 CSV 文件路径是否正确：「数据源设置」→ 逐一验证路径指向 `powerbi/data/`
2. 确认 CSV 文件已生成：`ls powerbi/data/`
3. 重新运行 Python 分析：`python python/main.py`

### Q3：刷新后提示"找不到列"

TMDL 模型中的列名与 CSV 列名不匹配。检查：
1. CSV 文件的列名（使用 `head -1 powerbi/data/funnel_wide_export.csv`）
2. TMDL 中对应的列定义（`powerbi/funnel_report/Ecommerce Funnel CRO.SemanticModel/definition/model.tmdl`）

### Q4：loss_data 表不存在

`loss_data` 是计算表，需要在 TMDL 中定义。如果缺失：
1. 参考 [§5 loss_data 计算表定义](#loss_data-计算表定义)
2. 或在 Power BI Desktop 中「建模」→「新建表」粘贴 DAX

### Q5：pbi-cli 连接模型失败

参考 Power BI 诊断技能：

```bash
pbi health        # 环境检查
pbi model info    # 模型信息
pbi report validate  # 报告验证
```

### Q6：Power BI Desktop 打开 .pbip 文件无响应

1. 确认 Power BI Desktop 版本 ≥ 2024 年 3 月版（PBIR 格式要求）
2. 尝试先打开 Power BI Desktop，再「文件」→「打开报告」→ 选择 .pbip 文件
3. 检查 Windows 防火墙是否阻止了本地文件访问

---

## 八、数据导出流程

### 当前实现

`python/import_to_mysql.py` 的 `step5_export_powerbi()` 负责生成 `powerbi/data/` 下的 CSV：

```python
# funnel_overview — 5 阶段漏斗汇总（到达会话 + 购买 + 转化率）
# channel_analysis — 5 渠道 sessions/purchases/conversion_rate
# device_analysis — 4 设备类型 sessions/purchases/conversion_rate
# country_analysis — 7 国家 sessions/purchases/conversion_rate
# funnel_wide_export — 分层抽样（每渠道 10%，保底 1000 行）
```

> 注意：运行主分析 `python python/main.py` 不会自动生成 powerbi/data 文件。需要单独运行 `python python/import_to_mysql.py` 或直接调用 `step5_export_powerbi()`。

### 已知局限

- funnel_wide_export 为分层抽样（每渠道 10%），非全量数据，部分精确计算需在主分析中完成
- loss_data 需要在 TMDL 中手动更新，未自动化导出为 CSV
- 无 Power BI 增量刷新配置

### 改进方向（P1-15/16 + P2-7）

1. loss_data 自动导出为 powerbi/data/loss_data.csv（当前需手动更新 TMDL）
2. 增加 DAX 度量值自动生成脚本
3. 增加趋势页和用户分层页
4. 配置 Power BI 增量刷新策略
