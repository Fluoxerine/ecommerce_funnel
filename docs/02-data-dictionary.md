# 数据字典

## 原始数据表：user_behavior / customer_journey.csv

| 字段 | 类型 | 说明 | 取值范围 |
|------|------|------|----------|
| SessionID | 字符串 | 会话唯一标识 | session_0 ~ session_4999（共 5,000 个会话） |
| UserID | 字符串 | 用户唯一标识 | user_1001 ~ user_2999（共 1,872 个用户） |
| Timestamp（CSV）/ EventTime（MySQL） | 日期时间 | 页面访问时间戳 | 2025-01-01 ~ 2025-12-31 |
| PageType | 字符串 | 页面类型 | home（首页）、product_page（商品页）、cart（购物车）、checkout（结账页）、confirmation（确认页） |
| DeviceType | 字符串 | 设备类型 | Desktop（桌面）、Mobile（移动）、Tablet（平板） |
| Country | 字符串 | 用户所在国家 | USA、UK、Germany、France、Canada、India、Australia |
| ReferralSource | 字符串 | 流量来源渠道 | Direct（直接）、Email（邮件）、Google（搜索）、Social Media（社交媒体） |
| TimeOnPage_seconds | 整数 | 该页面停留时长（秒） | 15 ~ 180 |
| ItemsInCart | 整数 | 当前购物车商品数 | 0 ~ 5 |
| Purchased | 整数 | 是否最终购买（会话级标记） | 0=未购买, 1=已购买 |

> **注意**：CSV 文件中列名为 `Timestamp`，导入 MySQL 后列名变为 `EventTime`，两者指代相同字段，仅命名不同。导入时按列的位置顺序映射，无需手动修改列名。

## 原始数据概况

| 指标 | 数值 |
|------|------|
| 总记录数 | 12,719 |
| 总会话数 | 5,000 |
| 总用户数 | 1,872 |
| 各页面记录数 | home: 5,000 / product_page: 3,987 / cart: 1,599 / checkout: 1,123 / confirmation: 1,010 |
| Purchased=1 记录数 | 5,050（同一会话内多个页面均标记为 1） |
| Purchased=0 记录数 | 7,669 |

## 清洗后宽表：funnel_wide

| 字段 | 类型 | 说明 |
|------|------|------|
| SessionID | 字符串 | 会话 ID（主键） |
| UserID | 字符串 | 用户 ID |
| DeviceType | 字符串 | 该会话主要使用的设备（取众数） |
| Country | 字符串 | 该会话主要所在国家（取众数） |
| ReferralSource | 字符串 | 该会话主要流量来源（取众数） |
| step1_home | 0/1 | 是否访问了首页 |
| step2_product | 0/1 | 是否访问了商品页 |
| step3_cart | 0/1 | 是否访问了购物车 |
| step4_checkout | 0/1 | 是否访问了结账页 |
| step5_confirm | 0/1 | 是否访问了支付确认页 |
| is_purchased | 0/1 | 该会话是否最终购买（= step5_confirm） |

## Python 衍生字段

| 字段 | 来源 | 说明 |
|------|------|------|
| hour | Timestamp | 访问时段（0-23） |
| weekday | Timestamp | 星期几（0=周一, 6=周日） |
| stage | PageType 映射 | 漏斗阶段中文标签（如"3.加入购物车"） |
| session_is_converted | Purchased 聚合 | 会话级转化标记（0/1） |

## 数据质量

经过以下清洗步骤后，数据质量检查结果：

| 清洗步骤 | 丢弃记录数 | 说明 |
|----------|-----------|------|
| 去重（SessionID+UserID+Timestamp+PageType） | 0 | 原始数据无重复 |
| 核心字段非空过滤 | 0 | 所有核心字段均无缺失 |
| 未来时间过滤 | 0 | 无非未来时间数据 |
| 数值异常过滤 | 0 | TimeOnPage 均在 15-180 秒，ItemsInCart 均在 0-5 |
| Purchased 值域过滤 | 0 | 仅含 0/1 |
| 会话总停留 < 5s 过滤 | 0 | 所有会话总停留均 ≥ 15s |
| **最终保留** | **12,719 条（100%）** | **5,000 个会话** |
