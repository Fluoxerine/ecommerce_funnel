# 电商用户行为漏斗与转化率优化（CRO）分析

> 量化各漏斗环节流失损失，定位转化瓶颈，输出 PIE 优先级优化策略

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Container-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![scipy](https://img.shields.io/badge/SciPy-Stats-8CAAE6?logo=scipy&logoColor=white)](https://scipy.org/)
[![Power BI](https://img.shields.io/badge/Power%20BI-Report-F2C811?logo=power-bi&logoColor=black)](https://powerbi.microsoft.com/)

## 核心发现

分析 5,000 个用户会话、1,872 个用户，全链路转化率为 **20.2%**。

**最高流失环节是「浏览商品 → 加入购物车」（上一阶段转化率仅 40.11%）**，2,388 个会话在此流失。

各环节预估损失：
| 流失环节 | 流失会话 | 流失率 | 预估损失 |
|----------|:------:|:-----:|:------:|
| 浏览→加购 | 2,388 | 59.89% | ¥119,400 |
| 首页→浏览 | 1,013 | 20.26% | ¥50,650 |
| 加购→下单 | 476 | 29.77% | ¥47,600 |
| 下单→支付 | 113 | 10.06% | ¥13,560 |

**PIE 优先级建议**：商品详情页优化（PIE=250） > 首页推荐改进（PIE=154） > 购物车召回（PIE=34） > 支付流程（PIE=18）。

## 项目结构

```
├── python/              分析引擎（8 模块）
│   ├── config.py          统一配置中心（路径、MySQL、颜色、日志）
│   ├── data_loader.py     数据加载与完整性校验
│   ├── data_cleaning.py   基础清洗 + 漏斗专属清洗 + 宽表生成
│   ├── funnel_analysis.py 漏斗构建 + 损失金额 + PIE 优先级 + 多维度拆解
│   ├── churn_diagnostics.py 流失特征统计对比（t 检验 / Cohen's d）
│   ├── visualization.py   matplotlib 8 张 + plotly 2 张
│   ├── import_to_mysql.py CSV → MySQL（pandas 直写） + Power BI 导出
│   └── main.py            主入口，串联全流程
├── sql/                 数据库脚本（8 个，按编号顺序执行）
├── docs/                项目文档（4 份，中文）
├── operations/          CRO 优化策略
├── powerbi/             Power BI PBIR 报告（4 页） + 数据文件
├── tests/               单元测试（24 个，pytest）
├── archive/             历史版本归档
└── notebook/            原始探索 notebook
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 MySQL 密码
cp .env.example .env
# 编辑 .env，填入 Docker MySQL 的密码和端口

# 3. 运行 Python 分析（清洗 + 漏斗 + 可视化）
python python/main.py

# 4. 导入 MySQL 并导出 Power BI 数据（可选）
python python/import_to_mysql.py

# 5. 运行测试
pytest tests/ -v
```

## 技术栈

| 领域 | 技能 |
|------|------|
| 数据清洗 | Pandas — 去重、缺失值处理、异常过滤、漏斗逻辑校验 |
| 漏斗分析 | 会话维度漏斗构建 + 渠道/设备/时段/国家多维度拆解 |
| 统计检验 | SciPy — 卡方独立性检验、独立样本 t 检验、Cohen's d 效应量 |
| 损失量化 | 购物车放弃金额（Cart Abandonment Value） × PIE 优先级框架 |
| 可视化 | Matplotlib（8 张静态）+ Plotly（2 张交互：漏斗图 + 桑基图） |
| 数据仓库 | MySQL 8.4（Docker）— 原始表 + 漏斗宽表 + 多维度查询 |
| 工程化 | Docker、pytest、python-dotenv 配置管理 |

## 分析方法清单

| 方法 | 来源 | 用途 |
|------|------|------|
| 全链路转化漏斗 | Google Analytics / Mixpanel 标准功能 | 基准：整体转化率 |
| 分渠道 / 分设备转化率对比 | GA 默认报告维度 | 找出高 / 低转化渠道 |
| 各环节损失金额量化 | CRO 标准（Monetate / Optimizely） | 量化每个环节漏了多少钱 |
| 停留时长与转化率关系 | Amplitude 行为分析标准 | 识别参与度与转化关联 |
| 进入路径分析 | GA Landing Page 标准报告 | 评估不同进入点的流量质量 |
| 时段分析（hour × weekday） | 电商 BI 标准维度 | 运营排期 + 高峰期识别 |
| 统计特征对比（卡方 / t 检验） | 统计学标准方法 | 流失组 vs 转化组差异显著性 |
| PIE 优先级矩阵 | PIE 框架（WiderFunnel） | 优化排期决策 |
