# Power BI 仪表板

> 电商漏斗转化率优化（CRO）— 4 页交互式报告

## 数据文件

所有 CSV 数据文件位于 `powerbi/data/`（由 `python python/import_to_mysql.py` 自动生成）：

| 文件 | 内容 | 行数 | 用途 |
|------|------|:--:|------|
| `funnel_wide_export.csv` | 全部 5,000 个会话的漏斗步骤标记 | 5,000 | 主事实表 |
| `funnel_overview.csv` | 漏斗步骤标记 + 转化标签 | 5,000 | 漏斗图数据源 |
| `channel_analysis.csv` | 4 个渠道的会话数与转化率 | 4 | 渠道对比柱状图 |
| `device_analysis.csv` | 3 种设备的会话数与转化率 | 3 | 设备对比柱状图 |
| `country_analysis.csv` | 7 个国家的会话数与转化率 | 7 | 地理分布分析 |

## 报告页面

| 页面 | 英文名 | 说明 |
|------|--------|------|
| ① 漏斗健康度 | Funnel Health | KPI 卡片（总流量 / 总转化 / 总损失金额）+ 全链路漏斗图 |
| ② 流量来源质量 | Traffic Quality | 渠道 × 设备转化率热力图 + 各渠道漏斗叠加对比 + 时段分布 |
| ③ 流失诊断 | Churn Diagnostics | 各节点损失金额排名 + 流失 vs 转化用户特征对比 |
| ④ 优化优先级 | Priority Matrix | PIE 优先级矩阵气泡图 + 优化建议清单 |

## 快速开始

### 方式一：直接导入 CSV

1. 打开 Power BI Desktop
2. 「获取数据」→ 「文本/CSV」→ 选择 `powerbi/data/` 目录下的 CSV 文件
3. 加载全部 5 个文件
4. 按需求建立表关系（SessionID 连接各表）
5. 参照上方「报告页面」描述构建可视化

### 方式二：使用 PBIR 报告项目

```bash
# 预览 PBIR 报告
cd powerbi/funnel_report/"Ecommerce Funnel CRO.Report"
pbi report preview

# 验证报告结构
pbi report validate

# 在 Power BI Desktop 中打开
# 文件 → 打开 → 选择 powerbi/funnel_report/Ecommerce Funnel CRO.pbip
```

## PBIR 报告结构

```
funnel_report/
├── Ecommerce Funnel CRO.pbip              # PBIP 项目文件
├── Ecommerce Funnel CRO.Report/           # PBIR 报告
│   ├── definition.pbir                    # 数据集引用
│   └── definition/
│       ├── version.json                   # PBIR 版本
│       ├── report.json                    # 报告设置与主题
│       └── pages/
│           ├── pages.json                 # 页面顺序
│           ├── funnel_health/             # ① 漏斗健康度
│           ├── traffic_quality/           # ② 流量来源质量
│           ├── churn_diagnostics/         # ③ 流失诊断
│           └── priority_matrix/           # ④ 优化优先级
└── Ecommerce Funnel CRO.SemanticModel/    # 语义模型（TMDL）
```

## 数据刷新

每次运行 `python python/import_to_mysql.py` 后，`powerbi/data/` 目录下的 CSV 文件会自动更新。在 Power BI Desktop 中点击「刷新」即可获取最新数据。
