# 电商用户行为漏斗与转化率优化（CRO）分析

> 基于 200 万条真实用户行为数据的六阶段漏斗全流程分析，覆盖"数据探查 → 漏斗建模 → 多维度诊断 → 流失根因 → 损失量化 → 策略闭环"

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![scipy](https://img.shields.io/badge/SciPy-Stats-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Charts-3F4F75?logo=plotly&logoColor=white)](https://plotly.com/)

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

---

## 核心发现一览

| 指标         |                                                值 |
| :----------- | ------------------------------------------------: |
| 独立会话     |                                           633,450 |
| 会话转化率   |               **15.08%**（购买 / 全部会话） |
| 浏览转化率   |               **18.13%**（购买 / 浏览会话） |
| 页面漏斗瓶颈 | 详情页 → 购物车 (交叉引用转化率**25.81%**) |
| 行为漏斗瓶颈 |             加购 → 购买 (转化率**41.27%**) |
| 年估算损失   |  **¥59,760,920**（基于实际客单价 Y100.25） |
| 总交易额     |                        ¥8,373,966 (退款率 2.98%) |
| 三年趋势     |  转化率从 16.97%(2021) 降至 7.98%(2023)，降幅 53% |
| P0 优化方向  |          详情页改版 + 个性化推荐 + 渠道差异化策略 |

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

```bash
pip install -r requirements.txt
python python/main.py
```

## 分析体系

### 六阶段闭环

1. **数据探查** — 五表加载 + traffic_source 大小写统一 + 表间关联完整性验证
2. **漏斗建模** — 页面级漏斗 (Home→PLP→PDP→Cart→Checkout) + 行为级漏斗 (浏览→点击→加购→购买) + 5 渠道专属漏斗
3. **多维诊断** — 渠道/设备/国家/品类/忠诚度/获客渠道 × 时段/趋势 × 渠道设备交叉
4. **流失根因** — t 检验 + Cohen's d + 渠道×环节流失矩阵
5. **损失量化** — 真实金额 PIE + 退款损失 + 机会空间
6. **策略闭环** — 基准快照 + 策略摘要自动生成 + A/B 实验效果 + 广告 ROAS

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
