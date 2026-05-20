"""数据加载与探查模块 — 五表加载 + 口径统一 + 完整性验证"""
import pandas as pd
from python.config import (
    EVENTS_CSV, TRANSACTIONS_CSV, CUSTOMERS_CSV,
    PRODUCTS_CSV, CAMPAIGNS_CSV, logger,
)


def load_all_tables() -> dict[str, pd.DataFrame]:
    """加载全部 5 张表，统一口径（traffic_source 大小写），返回 {表名: DataFrame}"""
    logger.info("=" * 60)
    logger.info("1. 数据加载")
    logger.info("=" * 60)

    events = pd.read_csv(EVENTS_CSV, parse_dates=['timestamp'])
    transactions = pd.read_csv(TRANSACTIONS_CSV, parse_dates=['timestamp'])
    customers = pd.read_csv(CUSTOMERS_CSV, parse_dates=['signup_date'])
    products = pd.read_csv(PRODUCTS_CSV, parse_dates=['launch_date'])
    campaigns = pd.read_csv(CAMPAIGNS_CSV, parse_dates=['start_date', 'end_date'])

    # 统一 traffic_source 大小写
    events['traffic_source'] = events['traffic_source'].str.title()

    logger.info("原始数据加载完成:")
    logger.info("  events:       %s 行, %s 列", f"{len(events):,}", len(events.columns))
    logger.info("  transactions: %s 行, %s 列", f"{len(transactions):,}", len(transactions.columns))
    logger.info("  customers:    %s 行, %s 列", f"{len(customers):,}", len(customers.columns))
    logger.info("  products:     %s 行, %s 列", f"{len(products):,}", len(products.columns))
    logger.info("  campaigns:    %s 行, %s 列", f"{len(campaigns):,}", len(campaigns.columns))

    return {
        'events': events, 'transactions': transactions,
        'customers': customers, 'products': products,
        'campaigns': campaigns,
    }


def print_data_overview(tables: dict[str, pd.DataFrame]) -> None:
    """打印各表关键统计信息"""
    events = tables['events']
    transactions = tables['transactions']
    customers = tables['customers']
    products = tables['products']

    logger.info("=" * 60)
    logger.info("2. 数据探查")
    logger.info("=" * 60)

    logger.info("--- events ---")
    logger.info("  事件类型: %s", events['event_type'].value_counts().to_dict())
    logger.info("  流量来源: %s", events['traffic_source'].value_counts().to_dict())
    logger.info("  设备:     %s", events['device_type'].value_counts().to_dict())
    logger.info("  实验分组: %s", events['experiment_group'].value_counts().to_dict())
    logger.info("  时间跨度: %s ~ %s",
                events['timestamp'].dt.strftime('%Y-%m-%d').min(),
                events['timestamp'].dt.strftime('%Y-%m-%d').max())
    n_sessions = events['session_id'].nunique()
    n_users = events['customer_id'].nunique()
    logger.info("  独立会话: %s, 独立用户: %s", f"{n_sessions:,}", f"{n_users:,}")

    logger.info("--- transactions ---")
    logger.info("  gross_revenue: mean=Y%.2f median=Y%.2f total=Y%s",
                transactions['gross_revenue'].mean(),
                transactions['gross_revenue'].median(),
                f"{transactions['gross_revenue'].sum():,.0f}")
    logger.info("  refund_flag: %s", transactions['refund_flag'].value_counts().to_dict())
    n_discount = (transactions['discount_applied'] > 0).sum()
    logger.info("  折扣订单: %s / %s", f"{n_discount:,}", f"{len(transactions):,}")

    logger.info("--- customers ---")
    logger.info("  国家: %s", customers['country'].value_counts().to_dict())
    logger.info("  忠诚度: %s", customers['loyalty_tier'].value_counts().to_dict())
    logger.info("  获客渠道: %s", customers['acquisition_channel'].value_counts().to_dict())
    logger.info("  年龄: %d-%d", customers['age'].min(), customers['age'].max())

    logger.info("--- products ---")
    logger.info("  品类: %s", products['category'].value_counts().to_dict())
    logger.info("  品牌数: %s", products['brand'].nunique())
    logger.info("  价格: Y%.2f - Y%.2f", products['base_price'].min(), products['base_price'].max())


def validate_data_integrity(tables: dict[str, pd.DataFrame]) -> list[str]:
    """验证 events↔transactions/customers/products/campaigns 表间关联完整性，返回问题列表"""
    events = tables['events']
    transactions = tables['transactions']
    customers = tables['customers']
    products = tables['products']
    campaigns = tables['campaigns']
    issues = []

    # purchase 事件 vs transactions 行数
    purchase_count = (events['event_type'] == 'purchase').sum()
    txn_count = len(transactions)
    if purchase_count == txn_count:
        logger.info("  purchase 事件 (%s) = transactions (%s) — 一致", f"{purchase_count:,}", f"{txn_count:,}")
    else:
        msg = f"purchase ({purchase_count}) != transactions ({txn_count})"
        issues.append(msg)

    # customer_id 覆盖
    e_users = set(events['customer_id'].unique())
    c_users = set(customers['customer_id'].unique())
    cov = len(e_users & c_users) / len(e_users) * 100
    logger.info("  events 用户在 customers 覆盖率: %.1f%%", cov)
    if cov < 100:
        issues.append(f"{len(e_users - c_users)} users in events not in customers")

    # product_id 覆盖
    e_prods = set(events[events['product_id'].notna()]['product_id'].astype(int).unique())
    p_ids = set(products['product_id'].unique())
    pcov = len(e_prods & p_ids) / len(e_prods) * 100
    logger.info("  events 商品在 products 覆盖率: %.1f%%", pcov)
    if pcov < 100:
        issues.append(f"{len(e_prods - p_ids)} products in events not in products")

    # campaign 覆盖
    e_camps = set(events[events['campaign_id'].notna()]['campaign_id'].astype(int).unique())
    c_ids = set(campaigns['campaign_id'].unique())
    ccov = len(e_camps & c_ids) / len(e_camps) * 100 if e_camps else 100
    logger.info("  events 活动在 campaigns 覆盖率: %.1f%%", ccov)

    if issues:
        logger.warning("数据完整性问题: %s", issues)
    else:
        logger.info("数据完整性检查通过")

    return issues
