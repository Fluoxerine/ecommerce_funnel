# E-Commerce Funnel Analysis & CRO

> 基于 220 万条用户行为数据的端到端转化率优化分析 —— 从数据探查到策略闭环，完整展示数据分析师的核心能力链。

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![SciPy](https://img.shields.io/badge/SciPy-Statistical_Tests-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-23_Charts-11557C?logo=python&logoColor=white)](https://matplotlib.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Wrangling-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-PBIR_Report-F2C811?logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)

---

## Executive Summary

本项目是一份**完整的数据分析作品集**，模拟真实电商场景下的转化率优化（CRO）全流程。选型决策、分析方法论、业务洞察和策略建议均有据可查，适合作为数据分析岗位的面试展示项目。

**一句话总结**：发现了电商漏斗的核心瓶颈（详情页→购物车转化率仅 25.81%），量化年损失 933 万元，并给出了分优先级的、附带 ROI 估算的可执行优化方案。

---

## 关键成果速览

| 维度 | 发现 |
| :--- | :--- |
| **核心瓶颈** | 详情页 → 购物车，交叉到达率仅 **25.81%**（行业基准 ~10-15%，但本数据为模拟数据，不可直接对标） |
| **年度趋势** | 整体转化率从 2021 年的 16.97% 降至 2023 年的 7.98%，**三年降幅 53%** |
| **年损失估算** | **¥9,328,840**（流失会话 × 预期转化率 × 客单价 ¥90.36） |
| **深链流量占比** | 54.9% 的 PLP 流量绕过了首页——传统线性漏斗无法刻画真实用户路径 |
| **严格路径转化** | 仅 **0.02%**（73/300,782）用户按 Home→PLP→PDP→Cart→Checkout 顺序走完全程 |
| **P0 优化方向** | 详情页改版（固定加购按钮 + 社会证明 + 个性化推荐），预期 ROI 1.5-3:1 |

---

## 分析框架

### 为什么选择"双漏斗"模型？

真实电商中，大量用户通过广告、搜索、社媒直达商品详情页（深链），而非按首页→列表页→详情页的线性路径浏览。单一的严格路径漏斗会将 95.8% 的 PDP 流量标记为"未进入漏斗"，严重低估流量价值。

本项目同时采用两套互补模型：

| 模型 | 用途 | 关键指标 |
| :--- | :--- | :--- |
| **页面覆盖分析**（宽松漏斗） | 评估各页面独立触达能力，发现深链流量分布 | 交叉到达率 |
| **严格路径漏斗** | 评估理想路径的端到端留存，发现流程断裂点 | 顺序转化率 |

> 这种"双漏斗对照"的方法论是本项目区别于简单漏斗分析的差异化点之一。

### 六阶段分析闭环

```
数据探查 → 漏斗建模 → 多维诊断 → 流失根因 → 损失量化 → 策略闭环
```

| 阶段 | 核心工作 | 产出 |
| :--- | :--- | :--- |
| **1. 数据探查** | 五表加载、字段标准化、关联完整性校验、数据质量报告 | 数据概览与质量评估 |
| **2. 数据清洗** | 会话时长异常值处理、漏斗宽表构建（633,450 行） | `funnel_wide.csv` |
| **3. 漏斗建模** | 页面漏斗 ×2 + 行为漏斗 + 5 渠道专属漏斗 + 品类漏斗 | 9 种漏斗视图 |
| **4. 多维诊断** | 渠道/设备/国家/品类/忠诚度/获客渠道 × 时段/趋势/交叉 | 20+ 维度分析 |
| **5. 流失根因** | 独立样本 t 检验 + Cohen's d + Bonferroni 校正 + 流失矩阵 | 统计显著性报告 |
| **6. 损失量化** | PIE 优先级矩阵 + 退款损失 + 广告 ROAS + What-If 模拟 | 策略摘要 + 基准快照 |

---

## 统计学方法

分析方法的选择均有明确理由，避免"为用而用"：

| 方法 | 应用场景 | 为什么用它 |
| :--- | :--- | :--- |
| **独立样本 t 检验** | 流失 vs 转化用户行为差异 | 二分类结果变量的均值比较 |
| **Cohen's d** | 效应量评估 | 大样本下 p 值几乎总是显著，需要效应量判断实际差异大小 |
| **Bonferroni 校正** | 多维度同时检验 | 控制 Family-Wise Error Rate，避免多重比较带来的假阳性 |
| **卡方检验** | 渠道×转化关联性 | 检验分类变量间独立性 |
| **PIE 矩阵** | 优化优先级排序 | Impact × Ease 双维度评估，确保资源投向回报最高的方向 |

---

## 技术架构

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  data/       │    │  python/      │    │  output/      │
│  5 CSV (2.2M)│───▶│  ETL + 分析   │───▶│  宽表 + 23 图  │
└──────────────┘    └──────┬───────┘    └──────────────┘
                           │
                    ┌──────▼───────┐    ┌──────────────┐
                    │  sql/        │    │  powerbi/     │
                    │  8 分析脚本   │    │  PBIR 报表     │
                    └──────────────┘    └──────────────┘
```

- **Python**：全流程自动化（数据加载 → 清洗 → 分析 → 可视化），约 4 分钟完成
- **SQL**：8 个独立分析脚本，可直接导入 MySQL 运行，覆盖漏斗概览到运营导出
- **Power BI**：PBIR 格式交互式报表，4 个页面（漏斗健康、流量质量、流失诊断、优先级矩阵）
- **统计检验**：SciPy 驱动的 t 检验 + Cohen's d + Bonferroni 校正

---

## 代表性可视化

<details>
<summary><b>点击展开图表预览</b></summary>

### 页面漏斗 & 流失瀑布

![页面漏斗](output/charts/01_page_funnel.png)

### 渠道漏斗对比

![渠道漏斗](output/charts/03_channel_funnels.png)

### 月度转化率趋势（2021-2023）

![月度趋势](output/charts/07_monthly_trend.png)

### PIE 优先级矩阵

![PIE矩阵](output/charts/10_pie_matrix.png)

### 新老用户漏斗对比

![新老用户](output/charts/14_new_vs_returning.png)

### 同期群留存热力图

![同期群](output/charts/16_cohort_heatmap.png)

</details>

---

## 项目结构

```
ecommerce_funnel_analysis/
├── data/                     # 原始数据 (未上传，需自行生成)
├── python/                   # 分析引擎
│   ├── config.py             # 全局配置 + CRO 行业基准 + 统计参数
│   ├── data_loader.py        # 五表加载 + 探查 + 质量报告
│   ├── data_cleaning.py      # 会话异常值清洗 + 漏斗宽表
│   ├── funnel_analysis.py    # 20+ 分析函数 (双漏斗/多维诊断/统计检验/损失量化)
│   ├── visualization.py      # 23 张图表 (matplotlib + plotly)
│   └── main.py               # 主入口 (支持 --skip-viz / --output)
├── sql/                      # 8 个独立 SQL 脚本 (MySQL 8.4)
├── powerbi/                  # Power BI PBIR 报表 (4 页交互式)
├── docs/                     # 分析文档 + 同行评审记录
├── operations/               # CRO 策略详情 (含实施成本 + ROI 估算)
├── output/charts/            # 23 张图表输出
└── tests/                    # pytest 单元测试 + 集成测试
```

---

## 快速运行

```bash
pip install -r requirements.txt
python python/main.py
```

**运行环境**：Python 3.13+ | 内存 ≥ 4GB | 运行时间约 3-4 分钟

**输出**：漏斗宽表（633,450 行）、基准快照 JSON、23 张可视化图表

---

## 数据说明

本项目使用**算法生成的模拟电商数据**（非真实用户日志），涵盖 2021-2023 三年数据：

| 表 | 行数 | 说明 |
| :--- | ---: | :--- |
| `events.csv` | 2,000,000 | 用户行为事件流（浏览/点击/加购/购买） |
| `transactions.csv` | 103,127 | 交易订单（含退款） |
| `customers.csv` | 100,000 | 用户画像（忠诚度/获客渠道） |
| `products.csv` | 2,000 | 商品信息 |
| `campaigns.csv` | 50 | 广告活动 |

> **局限说明**：模拟数据中各渠道/国家/品类的转化率差异较小（~1-2pp），真实电商中差异通常更显著。分析结论用于方法论演示，不可直接作为商业决策依据。这一说明体现了对数据局限性的清醒认知——也是面试中常被考察的能力点。

---

## 技能展示清单

| 能力维度 | 本项目体现 |
| :--- | :--- |
| **业务理解** | 将模糊的"提升转化率"拆解为可度量的漏斗环节和 PIE 优先级 |
| **数据清洗** | 会话时长异常值处理、traffic_source 标准化、多表关联去重 |
| **分析框架设计** | 六阶段闭环 + 双漏斗模型 + 多维度下钻体系 |
| **统计学基础** | t 检验、Cohen's d、Bonferroni 校正、卡方检验，且知其所以然 |
| **SQL 能力** | 8 个独立脚本，从建表到运营导出，含窗口函数和 CTE |
| **Python 工程** | 模块化设计、CLI 参数化、日志系统、单元测试 |
| **数据可视化** | matplotlib 静态图表 + plotly 交互式图表 + Power BI 报表 |
| **商业敏感度** | 损失金额量化、ROI 估算、P0/P1/P2 优先级排序 |
| **局限性意识** | 明确标注模拟数据、指标口径差异、不做虚假承诺 |

---

## 许可证

MIT
