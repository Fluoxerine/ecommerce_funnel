# Power BI 操作指南

> 报告已预配置 12 个可视化组件并绑定数据字段，打开 pbip 文件即可看到图表。如果刷新后图表为空，按页面下方说明操作。

---

## 快速开始

1. 双击打开 `powerbi/funnel_report/Ecommerce Funnel CRO.pbip`
2. 首次打开可能提示"数据源凭据"→ 选择"Windows 或 匿名"即可
3. 点击"刷新"按钮

**注意**：如果刷新后提示文件路径错误（因为 CSV 路径是你的本地路径），需要按如下操作重新指定数据源：
1. 「文件」→「选项和设置」→「数据源设置」
2. 选中每个 CSV 文件 →「更改源」→ 重新选择 `powerbi/data/` 下对应的 CSV
3. 点击「刷新」

数据源路径已在 TMDL 模型中硬编码为你的本地路径，首次打开 Desktop 会自动识别。若移动了项目文件夹，按上述步骤重新指定即可。

---

## 报告内容速览

| 页面 | 可视化 | 关联数据 | 显示内容 |
|------|--------|----------|----------|
| ① 漏斗健康度 | 3 KPI 卡片 | funnel_overview 度量值 | 总流量 5,000 / 转化率 20.20% / 损失金额 |
| | 漏斗柱状图 | 漏斗步骤 + funnel_overview 度量值 | 首页→商品页→购物车→结账页→确认页 各阶段会话数 |
| ② 流量质量 | 渠道柱状图 | channel_analysis | Google/Email/Direct/Social Media 转化率 |
| | 设备柱状图 | device_analysis | Desktop/Mobile/Tablet 转化率 |
| | 透视表 | funnel_wide_export | ReferralSource × DeviceType 交叉 |
| ③ 流失诊断 | 损失柱状图 | loss_data | 各环节损失金额：最高 ¥119,400（商品→加购） |
| | 渠道流失图 | funnel_wide_export | 按渠道的转化率对比 |
| | 明细表 | funnel_wide_export | SessionID/渠道/设备/国家/漏斗步骤 |
| ④ 优化优先级 | PIE 数据表 | loss_data | Potential/Importance/Ease/PIE得分 全维度 |
| | PIE 排名图 | loss_data | PIE得分排名：浏览→加购(250) 远高于其他 |

---

## 如果刷新后某张图表无数据

### 漏斗健康度 → KPI 卡片无数据

检查度量值是否存在：在右侧「数据」窗格展开 `funnel_overview` 表，确认有以下度量值：

```
首页会话 = SUM(funnel_wide_export[step1_home])
转化率 = DIVIDE(SUM(...step5_confirm), SUM(...step1_home))
损失金额 = (SUM(...step1_home)-SUM(...step5_confirm)) * 100
```

如果不存在，在「建模」→「新建度量值」手动创建。

### 流失诊断 → 损失柱状图无数据

`loss_data` 是预先写入 TMDL 的计算表。如果刷新后不存在：
1. 「建模」→「新建表」→ 输入以下 DAX：

```dax
loss_data = DATATABLE(
    "流失环节", STRING,
    "流失会话数", INTEGER,
    "损失金额", INTEGER,
    "Potential", DOUBLE,
    "Importance", DOUBLE,
    "Ease", INTEGER,
    "PIE得分", INTEGER,
    {
        {"首页→商品页", 1013, 50650, 2.2, 10.0, 7, 154},
        {"商品页→购物车", 2388, 119400, 5.2, 8.0, 6, 250},
        {"购物车→结账页", 476, 47600, 2.1, 3.2, 5, 34},
        {"结账页→确认页", 113, 13560, 1.0, 2.2, 8, 18}
    }
)
```

2. 然后将 loss_data 表的字段重新拖入对应 visual

---

## 关键数字对照

| 位置 | 指标 | 预期值 |
|------|------|:------:|
| 漏斗健康度 KPI1 | 总流量 | 5,000 |
| 漏斗健康度 KPI2 | 总转化率 | 20.20% |
| 漏斗健康度 漏斗图 | 商品页 | 3,987 |
| 流量质量 渠道图 | Google 转化率 | 21.64% |
| 流失诊断 损失图 | 最高损失 | ¥119,400 |
| PIE 表 | PIE 最高 | 250 |
