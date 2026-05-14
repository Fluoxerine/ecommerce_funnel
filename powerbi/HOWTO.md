# Power BI 操作指南：逐页拖拽字段说明书

> 前提：已将 `powerbi/data/` 目录下全部 5 个 CSV 导入 Power BI Desktop

---

## 数据导入（如果尚未导入）

1. 打开 Power BI Desktop
2. 「获取数据」→「文本/CSV」→ 选择 `powerbi/data/` 目录
3. 依次加载以下 5 个文件：
   - `funnel_wide_export.csv`（主表，5,000 行）
   - `funnel_overview.csv`（漏斗步骤）
   - `channel_analysis.csv`（渠道汇总，4 行）
   - `device_analysis.csv`（设备汇总，3 行）
   - `country_analysis.csv`（国家汇总，7 行）
4. 点击「加载」

---

## 页面一：漏斗健康度（Funnel Health）

此页有 3 张 KPI 卡片 + 1 个柱状图。

### 卡片 1：总流量（kpi_traffic）

| 步骤 | 操作 |
|------|------|
| 点击选中左上角第一个卡片 | |
| 字段拖入 | `funnel_overview` → `step1_home` |
| 聚合方式 | 求和（默认） |
| 预期显示 | **5,000** |

### 卡片 2：总转化率（kpi_conversion）

| 步骤 | 操作 |
|------|------|
| 点击选中中间卡片 | |
| 新建度量值 | 右键 `funnel_overview` → 新建度量值 |
| 输入公式 | `转化率 = DIVIDE(SUM(funnel_overview[step5_confirm]), SUM(funnel_overview[step1_home]))` |
| 格式 | 设置为百分比，保留两位小数 |
| 预期显示 | **20.20%** |

### 卡片 3：总损失金额（kpi_loss）

| 步骤 | 操作 |
|------|------|
| 点击选中右上角卡片 | |
| 新建度量值 | `损失金额 = (SUM(funnel_overview[step1_home])-SUM(funnel_overview[step5_confirm])) * 100` |
| 格式 | 设置为货币 |
| 预期显示 | **¥399,000**（或按你的客单价调整） |

### 柱状图：漏斗各阶段会话数（funnel_bar）

| 步骤 | 操作 |
|------|------|
| 点击选中下方柱状图 | |
| X 轴 | 手动输入：首页、商品页、购物车、结账页、确认页（或用「输入数据」创建新表） |
| Y 轴 | 分别拖入 `step1_home`, `step2_product`, `step3_cart`, `step4_checkout`, `step5_confirm` 的「求和」 |
| 替代方案 | 在 Power BI 中创建新表：「输入数据」→ 手动输入 5 行漏斗数据 → 用该表的列作图 |

---

## 页面二：流量来源质量（Traffic Quality）

此页有 2 个柱状图 + 1 个透视表。

### 柱状图 1：渠道转化率（channel_bar）

| 步骤 | 操作 |
|------|------|
| 点击选中左上柱状图 | |
| Y 轴 | `channel_analysis` → `ReferralSource` |
| X 轴 | `channel_analysis` → `conversion_rate` |
| 预期 | Google 21.64%, Email 20.06%, Direct 19.82%, Social Media 19.23% |

### 柱状图 2：设备转化率（device_bar）

| 步骤 | 操作 |
|------|------|
| 点击选中右上柱状图 | |
| Y 轴 | `device_analysis` → `DeviceType` |
| X 轴 | `device_analysis` → `conversion_rate` |
| 预期 | Desktop 20.35%, Mobile 20.17%, Tablet 20.08% |

### 透视表：渠道 × 设备交叉（channel_device_matrix）

| 步骤 | 操作 |
|------|------|
| 点击选中下方透视表 | |
| 行 | `funnel_wide_export` → `ReferralSource` |
| 列 | `funnel_wide_export` → `DeviceType` |
| 值 | `funnel_wide_export` → `is_purchased`（聚合：平均值，格式：百分比） |

---

## 页面三：流失诊断（Churn Diagnostics）

此页有 2 个柱状图 + 1 个表。

### 柱状图 1：各环节损失（loss_bar）

此处需要手动创建一个损失数据表。在 Power BI 中：

1. 「输入数据」→ 创建以下表格：

| 流失环节 | 流失会话数 | 损失金额 |
|----------|:------:|:------:|
| 首页→商品页 | 1013 | 50650 |
| 商品页→购物车 | 2388 | 119400 |
| 购物车→结账页 | 476 | 47600 |
| 结账页→确认页 | 113 | 13560 |

2. 将该表的「流失环节」拖入 Y 轴，「损失金额」拖入 X 轴

### 柱状图 2：按渠道流失（churn_by_dim）

| 步骤 | 操作 |
|------|------|
| 新建度量值 | `浏览加购流失率 = CALCULATE(COUNTROWS(funnel_wide_export), funnel_wide_export[step2_product]=1, funnel_wide_export[step3_cart]=0) / CALCULATE(COUNTROWS(funnel_wide_export), funnel_wide_export[step2_product]=1)` |
| Y 轴 | `funnel_wide_export` → `ReferralSource` |
| X 轴 | 上述度量值 |


### 表：流失用户明细（churn_table）

| 步骤 | 操作 |
|------|------|
| 列 1 | `funnel_wide_export` → `SessionID` |
| 列 2 | `funnel_wide_export` → `ReferralSource` |
| 列 3 | `funnel_wide_export` → `DeviceType` |

添加筛选器：`step3_cart = 1` 且 `step4_checkout = 0`（只显示加购但未下单的用户）

---

## 页面四：优化优先级（Priority Matrix）

此页有 1 个表 + 1 个柱状图。

### 表：PIE 优先级（pie_table）

在 Power BI 中「输入数据」→ 创建以下表格：

| 瓶颈环节 | Potential | Importance | Ease | PIE得分 | 损失金额 |
|----------|:------:|:--------:|:----:|:------:|:------:|
| 浏览→加购 | 5.2 | 8.0 | 6.0 | 250 | 119400 |
| 首页→浏览 | 2.2 | 10.0 | 7.0 | 154 | 50650 |
| 加购→下单 | 2.1 | 3.2 | 5.0 | 34 | 47600 |
| 下单→支付 | 1.0 | 2.2 | 8.0 | 18 | 13560 |

将所有列拖入表。

### 柱状图：PIE 得分排名（pie_bar）

| 步骤 | 操作 |
|------|------|
| Y 轴 | 上表的「瓶颈环节」 |
| X 轴 | 上表的「PIE得分」 |

---

## 快速验证

打开报告后，检查以下关键数字是否与实际数据一致：

| 位置 | 指标 | 预期值 |
|------|------|:------:|
| 漏斗健康度 → KPI 卡片 | 总流量 | 5,000 |
| 漏斗健康度 → KPI 卡片 | 总转化率 | 20.20% |
| 流量质量 → 渠道柱状图 | Google 转化率 | 21.64% |
| 流失诊断 → 损失柱状图 | 最高损失环节 | 商品页→购物车 ¥119,400 |
| 优化优先级 → PIE 表 | PIE 最高 | 浏览→加购 (250) |

---

## 另见

- 数据字典：`docs/02-data-dictionary.md`
- 分析结果详情：`docs/04-results.md`
- CRO 策略：`operations/cro_strategy.md`
