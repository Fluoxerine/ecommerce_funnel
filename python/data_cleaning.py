"""数据清洗模块：五表清洗 + 漏斗宽表构建"""
import pandas as pd
from python.config import (
    MIN_SESSION_DURATION, MAX_SESSION_DURATION,
    CLEANED_EVENTS_CSV, FUNNEL_WIDE_CSV, logger,
)


def basic_cleaning_events(events: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """events 表基础清洗：去重 → 核心字段非空 → 时长异常值过滤 → event_type 白名单
    返回 (清洗后 DataFrame, 各阶段保留行数)"""
    logger.info("=" * 60)
    logger.info("3. 数据清洗")
    logger.info("=" * 60)

    total = len(events)
    stats = {'原始数据': total}

    # 1. 去重
    before = len(events)
    events = events.drop_duplicates(subset=['event_id'], keep='first')
    stats['去重后'] = len(events)
    logger.info("去重: %s -> %s (丢弃 %s)", f"{before:,}", f"{len(events):,}", f"{before - len(events):,}")

    # 2. 核心字段非空
    for col in ['timestamp', 'customer_id', 'session_id', 'event_type']:
        before = len(events)
        events = events.dropna(subset=[col])
        if before != len(events):
            logger.info("  %s 非空过滤: 丢弃 %s", col, f"{before - len(events):,}")
    stats['核心字段非空'] = len(events)

    # 3. 时间类型确保
    events['timestamp'] = pd.to_datetime(events['timestamp'])

    # 4. session_duration_sec 异常值
    before = len(events)
    events = events[
        (events['session_duration_sec'] >= MIN_SESSION_DURATION) &
        (events['session_duration_sec'] <= MAX_SESSION_DURATION)
    ]
    stats['时长异常值过滤'] = len(events)
    logger.info("会话时长过滤: 丢弃 %s", f"{before - len(events):,}")

    # 5. event_type 标准化
    known_types = ['view', 'click', 'add_to_cart', 'bounce', 'purchase']
    before = len(events)
    events = events[events['event_type'].isin(known_types)]
    stats['事件类型白名单'] = len(events)
    logger.info("事件类型过滤: 丢弃 %s", f"{before - len(events):,}")

    # 6. traffic_source 大小写统一 (数据中存在 Organic/ORGANIC 等重复)
    if 'traffic_source' in events.columns:
        before_unique = events['traffic_source'].nunique()
        events['traffic_source'] = events['traffic_source'].str.strip().str.title()
        after_unique = events['traffic_source'].nunique()
        if before_unique != after_unique:
            logger.info("  traffic_source 标准化: %d -> %d 个唯一值 (大小写合并)",
                        before_unique, after_unique)

    # 7. device_type 缺失值填充 (数据集描述注明存在缺失, 共 40,300 条)
    if 'device_type' in events.columns:
        before_missing = events['device_type'].isna().sum()
        if before_missing > 0:
            events['device_type'] = events['device_type'].fillna('UNKNOWN')
            logger.info("  device_type 缺失值填充: %s 条 -> UNKNOWN", f"{before_missing:,}")

    pct = len(events) / total * 100
    logger.info("events 清洗完成: %s -> %s (保留 %.1f%%)", f"{total:,}", f"{len(events):,}", pct)
    return events.copy(), stats


def build_session_attributes(events: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """构建会话级属性表 — 聚合 events 到 session 粒度，合并 customers 画像，用户级实验分组"""
    logger.info("=" * 60)
    logger.info("4. 构建会话属性表")
    logger.info("=" * 60)

    # 会话级聚合
    session_attr = events.groupby('session_id').agg(
        customer_id=('customer_id', 'first'),
        traffic_source=('traffic_source', lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]),
        device_type=('device_type', lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]),
        experiment_group=('experiment_group', 'first'),
        campaign_id=('campaign_id', 'first'),
        total_duration_sec=('session_duration_sec', 'max'),
        event_count=('event_id', 'count'),
        session_start=('timestamp', 'min'),
        session_end=('timestamp', 'max'),
    ).reset_index()

    # 衍生时间特征
    session_attr['hour'] = session_attr['session_start'].dt.hour
    session_attr['weekday'] = session_attr['session_start'].dt.weekday
    session_attr['date'] = session_attr['session_start'].dt.date
    session_attr['year'] = session_attr['session_start'].dt.year
    session_attr['month'] = session_attr['session_start'].dt.month

    # 关联用户属性
    cust_cols = ['customer_id', 'country', 'age', 'gender', 'loyalty_tier',
                 'acquisition_channel', 'signup_date']
    session_attr = session_attr.merge(customers[cust_cols], on='customer_id', how='left')

    logger.info("会话属性表: %s 会话", f"{len(session_attr):,}")

    # 按用户级重新确定实验分组（原始数据中 experiment_group 为事件级，需用户级聚合）
    user_exp = events.groupby('customer_id')['experiment_group'].agg(
        lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]
    ).reset_index()
    user_exp.columns = ['customer_id', 'experiment_group_user']
    session_attr = session_attr.merge(user_exp, on='customer_id', how='left')
    session_attr['experiment_group'] = session_attr['experiment_group_user'].fillna(
        session_attr['experiment_group']
    )
    session_attr = session_attr.drop(columns=['experiment_group_user'])

    return session_attr


def build_funnel_wide(events: pd.DataFrame, session_attr: pd.DataFrame,
                      transactions: pd.DataFrame) -> pd.DataFrame:
    """构建漏斗宽表：每个会话一行，含页面漏斗 + 行为漏斗 + 交易信息"""
    logger.info("=" * 60)
    logger.info("5. 构建漏斗宽表")
    logger.info("=" * 60)

    # 构建宽表
    funnel_wide = session_attr.copy()

    # 页面漏斗 + 行为漏斗 + bounce 标记 — 2 次 crosstab 替代 10 次 set 扫描
    page_matrix = (
        pd.crosstab(events['session_id'], events['page_category'])
        .gt(0).astype(int)
        .rename(columns={
            'Home': 'step1_home', 'PLP': 'step2_plp', 'PDP': 'step3_pdp',
            'Cart': 'step4_cart', 'Checkout': 'step5_checkout',
        })
        .reset_index()
    )
    event_matrix = (
        pd.crosstab(events['session_id'], events['event_type'])
        .gt(0).astype(int)
        .rename(columns={
            'view': 'step_view', 'click': 'step_click',
            'add_to_cart': 'step_add_cart', 'purchase': 'step_purchase',
            'bounce': 'is_bounced',
        })
        .reset_index()
    )
    funnel_wide = funnel_wide.merge(page_matrix, on='session_id', how='left')
    funnel_wide = funnel_wide.merge(event_matrix, on='session_id', how='left')

    # 填充未匹配的 session_id（0 = 未到达该页面/未发生该事件）
    step_cols = ['step1_home', 'step2_plp', 'step3_pdp', 'step4_cart', 'step5_checkout',
                 'step_view', 'step_click', 'step_add_cart', 'step_purchase', 'is_bounced']
    for col in step_cols:
        if col not in funnel_wide.columns:
            funnel_wide[col] = 0
        else:
            funnel_wide[col] = funnel_wide[col].fillna(0).astype(int)

    # 关联交易数据 — 注意: transactions 无 session_id，只能聚合到 customer 级
    # 过滤缺失 product_id/gross_revenue 的交易（10,449条，占 10.1%）
    valid_txn = transactions[
        transactions['product_id'].notna() & transactions['gross_revenue'].notna()
    ].copy()
    dropped_txn = len(transactions) - len(valid_txn)
    if dropped_txn > 0:
        logger.info(
            "  过滤缺失 product_id/revenue 的交易: %s 条 (%.1f%%) — 仍计入购买计数",
            f"{dropped_txn:,}", dropped_txn / len(transactions) * 100,
        )

    # total_revenue/has_refund 等字段为客户级数据，不可在会话级做 sum()
    txn_agg = valid_txn.groupby('customer_id').agg(
        total_revenue=('gross_revenue', 'sum'),
        total_transactions=('transaction_id', 'nunique'),
        total_discount=('discount_applied', 'sum'),
        has_refund=('refund_flag', 'max'),
        refund_count=('refund_flag', 'sum'),
    ).reset_index()
    # 首次购买日期使用全量 transactions（含缺失 product_id 的，购买行为仍成立）
    first_txn = transactions.groupby('customer_id')['timestamp'].min().reset_index()
    first_txn.columns = ['customer_id', 'first_purchase_date']
    txn_agg = txn_agg.merge(first_txn, on='customer_id', how='left')

    # 对仅在"broken"交易中有购买记录的用户，补充 transaction 计数
    all_purchasers = transactions.groupby('customer_id')['transaction_id'].nunique().reset_index()
    all_purchasers.columns = ['customer_id', 'total_transactions_all']
    txn_agg = txn_agg.merge(all_purchasers, on='customer_id', how='outer')
    txn_agg['total_transactions'] = txn_agg['total_transactions'].fillna(0).astype(int)
    txn_agg['total_transactions'] = txn_agg[['total_transactions', 'total_transactions_all']].max(axis=1)
    txn_agg = txn_agg.drop(columns=['total_transactions_all'])

    funnel_wide = funnel_wide.merge(txn_agg, on='customer_id', how='left')
    for col in ['total_revenue', 'total_transactions', 'total_discount', 'has_refund', 'refund_count']:
        funnel_wide[col] = funnel_wide[col].fillna(0).astype(
            'float64' if col == 'total_revenue' else 'int64'
        )
    negative_mask = funnel_wide['total_revenue'] < 0
    if negative_mask.any():
        logger.warning("发现 %d 条负收入记录, 已保留原值 (customer_ids: %s)",
                       int(negative_mask.sum()),
                       funnel_wide.loc[negative_mask, 'customer_id'].unique().tolist())
    funnel_wide['is_purchased'] = (funnel_wide['total_transactions'] > 0).astype(int)

    logger.info("漏斗宽表: %s 会话 x %s 列", f"{len(funnel_wide):,}", len(funnel_wide.columns))

    # 打印各步骤分布
    page_steps = ['step1_home', 'step2_plp', 'step3_pdp', 'step4_cart', 'step5_checkout']
    for s in page_steps:
        logger.info("  %s: %s 会话", s, f"{funnel_wide[s].sum():,}")

    event_steps = ['step_view', 'step_click', 'step_add_cart', 'step_purchase']
    for s in event_steps:
        logger.info("  %s: %s 会话", s, f"{funnel_wide[s].sum():,}")

    # 漏斗逻辑校验：购买必须有 checkout
    purchasers = funnel_wide[funnel_wide['step_purchase'] == 1]
    checkout_missing = (purchasers['step5_checkout'] == 0).sum()
    if checkout_missing > 0:
        logger.warning("  %s 个购买会话无 checkout 记录（可能是跨会话转化）", checkout_missing)
    else:
        logger.info("漏斗逻辑校验通过")

    return funnel_wide


def save_cleaned_data(events_cleaned: pd.DataFrame, funnel_wide: pd.DataFrame) -> None:
    """保存清洗后 events 和漏斗宽表到 CSV"""
    events_cleaned.to_csv(CLEANED_EVENTS_CSV, index=False, encoding='utf-8-sig')
    logger.info("已保存: %s (%s 条)", CLEANED_EVENTS_CSV, f"{len(events_cleaned):,}")
    funnel_wide.to_csv(FUNNEL_WIDE_CSV, index=False, encoding='utf-8-sig')
    logger.info("已保存: %s (%s 条)", FUNNEL_WIDE_CSV, f"{len(funnel_wide):,}")
