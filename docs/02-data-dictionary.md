# 数据字典

> 代码版本：2026-05-26 | 数据集：模拟数据 | 5 表, 41 字段, 2.2M+ 条记录

---

## 表 1: events（用户行为事件）

| 字段 | 类型 | 说明 | 示例值 |
|:---|:---|:---|:---|
| `event_id` | INT | 事件唯一 ID | 1-2000000 |
| `timestamp` | DATETIME | 事件时间 | 2021-01-01 ~ 2023-12-31 |
| `customer_id` | INT | 用户 ID (关联 customers) | 1-100000 |
| `session_id` | INT | 会话 ID | 1-633462 |
| `event_type` | STRING | 事件类型 | view / click / add_to_cart / bounce / purchase |
| `product_id` | INT | 商品 ID (关联 products, 可为空) | 1-2000 |
| `device_type` | STRING | 设备类型 | mobile / desktop / tablet |
| `traffic_source` | STRING | 流量来源 | Organic / Paid Search / Social / Email / Direct |
| `campaign_id` | INT | 广告活动 ID (关联 campaigns) | 1-50 |
| `page_category` | STRING | 页面类型 | Home / PLP / PDP / Cart / Checkout |
| `session_duration_sec` | FLOAT | 会话时长(秒) | 0.1-7533.8 |

**事件分布**: view(1,043,573) > click(379,008) > add_to_cart(284,370) > bounce(189,922) > purchase(103,127)

---

## 表 2: transactions（交易订单）

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `transaction_id` | INT | 交易 ID |
| `timestamp` | DATETIME | 交易时间 |
| `customer_id` | INT | 用户 ID |
| `product_id` | INT | 商品 ID |
| `quantity` | INT | 购买数量 |
| `discount_applied` | FLOAT | 折扣金额 |
| `gross_revenue` | FLOAT | 交易毛收入 (均值 ¥90.36, 中位数 ¥68.00) |
| `campaign_id` | INT | 关联广告活动 |
| `refund_flag` | INT | 退款标记 (0/1, 退款率 3.1%) |

---

## 表 3: customers（用户画像）

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `customer_id` | INT | 用户 ID |
| `signup_date` | DATE | 注册日期 |
| `country` | STRING | 国家 (US/IN/UK/BR/CA/DE/AU) |
| `age` | INT | 年龄 (18-70) |
| `gender` | STRING | 性别 (Male/Female/Other) |
| `loyalty_tier` | STRING | 忠诚度等级 (Bronze/Silver/Gold/Platinum) |
| `acquisition_channel` | STRING | 获客渠道 (Organic/Paid Search/Social/Email/Referral) |

---

## 表 4: products（商品信息）

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `product_id` | INT | 商品 ID |
| `category` | STRING | 品类 (Electronics/Fashion/Home/Grocery/Sports/Beauty) |
| `brand` | STRING | 品牌 (100 个品牌) |
| `base_price` | FLOAT | 基础价格 (¥5.11-464.58) |
| `launch_date` | DATE | 上市日期 |
| `is_premium` | INT | 是否高端商品 (0/1, 各 50%) |

---

## 表 5: campaigns（广告活动）

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `campaign_id` | INT | 广告活动 ID |
| `channel` | STRING | 投放渠道 (Paid Search/Email/Social/Display/Affiliate) |
| `objective` | STRING | 目标 (Acquisition/Retention/Reactivation/Cross-sell) |
| `start_date` | DATE | 开始日期 |
| `end_date` | DATE | 结束日期 |
| `target_segment` | STRING | 目标人群 (New Customers/High Value/Churn Risk/Deal Seekers/All) |
| `expected_uplift` | FLOAT | 预期提升率 (2.3%-14.4%) |
