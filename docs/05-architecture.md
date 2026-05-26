# 项目架构

> 代码版本：python/funnel_analysis.py | 生成日期：2026-05-26

## 一、模块依赖与数据流

```
                          main.py (编排层)
                              │
        ┌─────────────────────┼─────────────────────────┐
        │                     │                         │
   data_loader.py      data_cleaning.py         funnel_analysis.py
   (加载 + 探查)        (清洗 + 宽表)             (核心分析引擎)
        │                     │                         │
        │   load_all_tables() │  basic_cleaning_events()│ compute_page_funnel()
        │   validate_*()      │  build_session_attr()   │ compute_event_funnel()
        │                     │  build_funnel_wide()    │ compute_channel_funnels()
        │                     │                         │ compute_loss_amount()
        └─────────┬───────────┘                         │ compute_pie_priority()
                  │                                     │ compute_churn_features()
                  │                                     │ statistical_tests()
           visualization.py                             │ save_baseline()
           (11 张图表)                                   │
                  │                                     │
                  │                                     │
                  └──────────────┬──────────────────────┘
                                 │
                          import_to_mysql.py
                          (MySQL 导入 + Power BI 导出)
```

### 数据流转

```
data/                          python/                     output/
─────                          ──────                      ──────
events.csv           ──→  data_loader.load_all_tables()
transactions.csv     ──→  data_loader.validate_*()
customers.csv        ──→  data_cleaning.basic_cleaning_events()  ──→ cleaned_events.csv
products.csv         ──→  data_cleaning.build_session_attr()     ──→ funnel_wide.csv
campaigns.csv        ──→  data_cleaning.build_funnel_wide()     ──→ baseline_snapshot.json
                              │                                      charts/*.png
                              │                                      charts/*.html
                              ↓
                       funnel_analysis (计算层)
                       visualization  (图表层)
                              │
                              ↓
                       import_to_mysql  ──→  powerbi/data/*.csv
                       (Power BI 导出)
```

## 二、模块职责

### data_loader.py — 数据接入层
- 5 表加载 + 时间解析
- `traffic_source` 大小写统一
- 表间关联完整性验证 (events↔customers/transactions/products/campaigns)
- 关键分布探查 (event_type, device, traffic_source, experiment_group)

### data_cleaning.py — 数据清洗层
- event_id 去重
- 核心字段非空过滤
- session_duration 异常值过滤 (1s-7200s)
- event_type 白名单校验
- 会话级属性聚合 (customer_id, device, traffic_source, experiment_group)
- 漏斗宽表构建 (9 个 step 列 + 交易信息)
- 漏斗逻辑校验 (purchase→checkout)

### funnel_analysis.py — 分析引擎层 (~20 个函数)
按六阶段闭环组织：

| 阶段 | 函数 | 输出 |
|:---|:---|:---|
| 漏斗建模 | `compute_page_funnel` / `compute_event_funnel` / `compute_channel_funnels` | 各漏斗 DataFrame |
| 多维诊断 | `compute_*_analysis` (channel/device/country/loyalty/acquisition/category/duration/trend) | 按维度的转化率表 |
| 流失根因 | `compute_churn_features` / `compute_churn_matrix` | t 检验 + Cohen's d + 渠道×环节矩阵 |
| 损失量化 | `compute_loss_amount` / `compute_pie_priority` | 环节损失 + PIE 得分 |
| 统计检验 | `statistical_tests` | 卡方 + Bonferroni |
| 策略输出 | `save_baseline` / `generate_strategy_brief` | 基准快照 + 策略摘要 |

### visualization.py — 图表层 (11 张)

| # | 图表 | 类型 | 说明 |
|:---:|:---|:---|:---|
| 1 | 页面级漏斗 | Matplotlib Barh | 交叉引用转化率 |
| 2 | 行为级漏斗 | Matplotlib Barh | 浏览→点击→加购→购买 |
| 3 | 渠道漏斗对比 | Matplotlib Barh | Top 3 渠道 |
| 4 | 损失瀑布图 | Matplotlib Bar | 各环节年度损失 |
| 5 | 渠道×设备热力图 | Matplotlib Imshow | 转化率交叉矩阵 |
| 6 | 维度对比 | Matplotlib Barh | 渠道/设备/忠诚度 × 3 |
| 7 | 月度趋势 | Matplotlib Line | 2021-2023 三年 |
| 8 | 停留时长 vs 转化率 | Matplotlib Bar+Line | GA4 行为分桶 |
| 9 | 渠道流失率 | Matplotlib Barh | 渠道×环节矩阵 |
| 10 | PIE 矩阵 | Matplotlib Scatter | 气泡大小=PIE 得分 |
| 11 | 品类漏斗 | Matplotlib Grouped Bar | 浏览→加购→购买 |

### import_to_mysql.py — 数据导出层
- 5 步流程：(1) 建表 → (2) 导入 MySQL → (3) 执行 SQL 分析 → (4) 验证 → (5) 导出 Power BI CSV
- Step 5 可独立运行（从 funnel_wide.csv 直接用 pandas 导出）

## 三、SQL 分析体系

| 脚本 | 说明 | 依赖 |
|:---|:---|:---|
| 01_setup_database.sql | DDL 建表 (5 表 + 索引) | — |
| 02_load_data.sql | LOAD DATA INFILE 导入 | 01 |
| 03_funnel_overview.sql | 页面级 + 行为级漏斗 | 01 |
| 04_multi_dimension.sql | 渠道/设备/国家/忠诚度 | 01 |
| 05_churn_diagnostics.sql | 流失特征 + 渠道×环节交叉 | 01 |
| 06_statistical_tests.sql | 卡方检验底表 | 01 |
| 07_loss_quantification.sql | 退款损失 + ROAS + 品类 PIE | 01 |
| 08_operational_export.sql | 漏斗宽表导出 + 监控 KPI | 01 |

## 四、测试体系

| 测试文件 | 用例数 | 覆盖模块 |
|:---|---:|:---|
| test_data_cleaning.py | 12 | basic_cleaning_events, build_session_attributes, build_funnel_wide |
| test_funnel_analysis.py | 18 | compute_page_funnel, compute_event_funnel, compute_channel_analysis, compute_device_analysis, compute_loss_amount, compute_pie_priority, compute_duration_analysis, compute_churn_features |

## 五、关键设计决策

| 决策 | 理由 |
|:---|:---|
| 页面漏斗用交叉引用而非简单排序 | 处理多入口（深链）场景，PLP 会话 > Home 会话 |
| 损失计算用转化用户实际客单价 | 避免虚构权重（0.3/0.5/0.8/1.0），数据驱动 |
| 流失会话级联去重 | 防止同一会话在多个环节被重复计数 |
| 品类浏览加 event_type==view 过滤 | 之前浏览会话包含了 purchase/click，严重高估 |
| 双转化率口径 | 会话转化率(15.08%) 和浏览转化率(18.13%) 分母不同，分开标注 |
| 固定时长分桶（非等频） | 固定阈值可跨周期对比，等频分桶边界随时间漂移 |

## 六、运行方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行分析
python python/main.py

# 3. 运行测试
pytest tests/ -v

# 4. Power BI 导出 (需要 MySQL Docker)
python python/import_to_mysql.py
```
