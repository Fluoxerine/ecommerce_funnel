# Power BI 仪表板

> 电商漏斗 CRO 分析 — 4 页交互式报告 | 2026-05-26

详细操作指南见 [HOWTO.md](HOWTO.md)。

## 报告页面

| 页面 | 内容 |
|:---|:---|
| ① 漏斗健康度 | KPI 卡片（633,450 会话 / 15.08% CR / ¥9.33M 损失）+ 漏斗柱状图 |
| ② 流量质量 | 渠道×设备转化率对比 + 交叉热力图 |
| ③ 流失诊断 | 损失瀑布图 + 流失率柱状图 + 流失特征对比 |
| ④ 优化优先级 | PIE 气泡图 + PIE 数据表（含 Ease±1 敏感性） |

## 快速开始

1. 运行 `python python/main.py` 生成数据源 CSV
2. 双击 `funnel_report/Ecommerce Funnel CRO.pbip`
3. 配置数据源路径（首次）→ 刷新

## 数据文件

| 文件 | 行数 | 用途 |
|:---|---:|:---|
| `funnel_wide_export.csv` | 633,450 | 主事实表（会话级宽表） |
| `funnel_overview.csv` | 5 | 漏斗阶段汇总 |
| `channel_analysis.csv` | 5 | 渠道维度 |
| `device_analysis.csv` | 3 | 设备维度 |
| `country_analysis.csv` | 7 | 国家维度 |
