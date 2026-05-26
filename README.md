# 电商用户行为漏斗与转化率优化（CRO）分析

> 基于 200 万条真实用户行为数据的六阶段漏斗全流程分析，覆盖"数据探查 → 漏斗建模 → 多维度诊断 → 流失根因 → 损失量化 → 策略闭环"

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![scipy](https://img.shields.io/badge/SciPy-Stats-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-Charts-11557C?logo=python&logoColor=white)](https://matplotlib.org/)

---

## 数据规模

|                      |                行数 |         字段 | 说明                         |
| :------------------- | ------------------: | -----------: | :--------------------------- |
| `events.csv`       |           2,000,000 |           12 | 用户行为事件流               |
| `transactions.csv` |             103,127 |            9 | 交易订单                     |
| `customers.csv`    |             100,000 |            7 | 用户画像                     |
| `products.csv`     |               2,000 |            6 | 商品信息                     |
| `campaigns.csv`    |                  50 |            7 | 广告活动                     |
| **合计**       | **2,205,177** | **41** | **2021-2023 三年数据** |

> **模拟数据声明**：本项目使用算法生成的模拟电商数据，非真实用户行为日志。数据中各渠道/国家/品类的转化率高度一致（差异在 ~1-2pp），真实电商中差异通常更大。分析结论用于方法论演示，不可直接作为商业决策依据。

---

## 核心发现一览

| 指标         |                                                                                     值 |
| :----------- | -------------------------------------------------------------------------------------: |
| 独立会话     |                                                                                633,450 |
| 会话转化率   |                                                    **15.08%**（购买 / 全部会话） |
| 浏览转化率   |                                                    **18.13%**（购买 / 浏览会话） |
| 页面漏斗瓶颈 |                                      详情页 → 购物车 (交叉引用转化率**25.81%**) |
| 行为漏斗瓶颈 |                                                  加购 → 购买 (转化率**41.27%**) |
| 年估算损失   |                       **¥9,328,840**（流失会话 × 预期转化率 × 客单价 Y90.36） |
| 总交易额     |                                                             ¥8,373,966 (退款率 2.98%) |
| 口径说明     | 损失基于预期转化率估算（非 100% 购买假设），总交易额为三年实际发生额，两者不可直接比较 |
| 三年趋势     |                                       转化率从 16.97%(2021) 降至 7.98%(2023)，降幅 53% |
| P0 优化方向  |                                               详情页改版 + 个性化推荐 + 渠道差异化策略 |

---

## 项目结构

```
ecommerce_funnel_analysis/
├── data/                     # 原始数据 (5 CSV)
├── python/                   # Python 分析引擎
│   ├── config.py             # 配置
│   ├── data_loader.py        # 五表加载 + 探查
│   ├── data_cleaning.py      # 清洗 + 漏斗宽表
│   ├── funnel_analysis.py    # 核心分析 (20+ 函数)
│   ├── visualization.py      # 12 张图表
│   └── main.py               # 主入口
├── sql/                      # SQL 分析脚本 (8 个)
├── docs/                     # 分析文档 (4 篇)
├── operations/
│   └── cro_strategy.md       # CRO 优化策略
├── output/
│   ├── charts/               # 12 张可视化图表
│   ├── funnel_wide.csv       # 漏斗宽表
│   └── baseline_snapshot.json
└── tests/
```

## 快速运行

### 前置条件

`data/` 目录下必须存在以下 5 个 CSV 文件：

| 文件                 | 必需列                                                                                          |
| :------------------- | :---------------------------------------------------------------------------------------------- |
| `events.csv`       | session_id, customer_id, event_type, timestamp, page_type, traffic_source, device_type, country |
| `transactions.csv` | transaction_id, customer_id, gross_revenue, timestamp                                           |
| `customers.csv`    | customer_id, loyalty_tier, acquisition_channel                                                  |
| `products.csv`     | product_id, category, price                                                                     |
| `campaigns.csv`    | campaign_id, channel, budget                                                                    |

缺失任一文件时，数据加载阶段会报错并退出。

### 运行

```bash
pip install -r requirements.txt
python python/main.py
```

**预期运行时间**：约 3-4 分钟（取决于机器性能），全流程包括数据加载、清洗、20+ 分析函数、17 张图表生成。

**预期输出**：

| 类别       | 路径                              | 说明                                 |
| :--------- | :-------------------------------- | :----------------------------------- |
| 漏斗宽表   | `output/funnel_wide.csv`        | 633,450 行会话级数据                 |
| 清洗后事件 | `output/cleaned_events.csv`     | 去重/标准化后的事件流                |
| 基准快照   | `output/baseline_snapshot.json` | 核心指标 JSON                        |
| 图表 ×17  | `output/charts/`                | 17 张 matplotlib PNG（含元信息脚注） |

运行完成后在终端查看完整日志输出，关键指标会以 `[INFO]` 级别打印。

## 分析体系

### 六阶段闭环

1. **数据探查** — 五表加载 + traffic_source 大小写统一 + 表间关联完整性验证
2. **漏斗建模** — 页面级漏斗 (Home→PLP→PDP→Cart→Checkout) + 行为级漏斗 (浏览→点击→加购→购买) + 5 渠道专属漏斗
3. **多维诊断** — 渠道/设备/国家/品类/忠诚度/获客渠道 × 时段/趋势 × 渠道设备交叉
4. **流失根因** — t 检验 + Cohen's d + 渠道×环节流失矩阵
5. **损失量化** — 真实金额 PIE + 退款损失 + 机会空间
6. **策略闭环** — 基准快照 + 策略摘要自动生成 + 广告 ROAS

### 行业方法

卡方检验 · 独立样本 t 检验 · Cohen's d 效应量 · Bonferroni 多重比较校正 · PIE 优先级矩阵 · GA4 行为阈值分桶 · 漏斗图/瀑布图/热力图

### 数据模型

```
events ──── customer_id ──── customers
  │              │
  ├ product_id ──┼── products
  ├ campaign_id ─┤
  │              │
transactions ────┴── campaigns
  (customer_id, product_id, campaign_id)
```
