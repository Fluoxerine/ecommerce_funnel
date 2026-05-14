"""数据加载模块：读取 CSV，基础概览，列名校验"""
import pandas as pd
from python.config import RAW_CSV, logger


def load_raw_data() -> pd.DataFrame:
    """读取原始 CSV 并执行基础校验"""
    logger.info("=" * 60)
    logger.info("1. 数据加载")
    logger.info("=" * 60)

    if not RAW_CSV.exists():
        logger.error("缺少数据文件: %s", RAW_CSV)
        raise FileNotFoundError(f"数据文件不存在: {RAW_CSV}")

    df = pd.read_csv(RAW_CSV)
    logger.info("原始数据: %s 条记录", f"{len(df):,}")

    expected_cols = ['SessionID', 'UserID', 'Timestamp', 'PageType',
                     'DeviceType', 'Country', 'ReferralSource',
                     'TimeOnPage_seconds', 'ItemsInCart', 'Purchased']
    actual_cols = df.columns.tolist()
    missing = set(expected_cols) - set(actual_cols)
    extra = set(actual_cols) - set(expected_cols)
    if missing:
        logger.warning("缺少预期列: %s", missing)
    if extra:
        logger.info("额外列: %s", extra)

    logger.info("列名: %s", actual_cols)
    return df


def print_data_overview(df: pd.DataFrame) -> None:
    """打印数据概览（用于日志和报告）"""
    logger.info("会话数: %s", f"{df['SessionID'].nunique():,}")
    logger.info("用户数: %s", f"{df['UserID'].nunique():,}")

    logger.info("页面类型分布:")
    for pt, cnt in df['PageType'].value_counts().items():
        logger.info("  %s: %s", pt, f"{cnt:,}")

    logger.info("Purchased 分布:")
    for v, cnt in df['Purchased'].value_counts().items():
        logger.info("  %d: %s", v, f"{cnt:,}")

    logger.info("设备分布:")
    for d, cnt in df['DeviceType'].value_counts().items():
        logger.info("  %s: %s", d, f"{cnt:,}")

    logger.info("渠道分布:")
    for r, cnt in df['ReferralSource'].value_counts().items():
        logger.info("  %s: %s", r, f"{cnt:,}")

    logger.info("国家分布:")
    for c, cnt in df['Country'].value_counts().items():
        logger.info("  %s: %s", c, f"{cnt:,}")


def validate_data_integrity(df: pd.DataFrame) -> dict:
    """校验数据完整性并返回问题清单"""
    issues = {}

    if not df['Purchased'].isin([0, 1]).all():
        issues['purchased_invalid'] = int((~df['Purchased'].isin([0, 1])).sum())

    neg_time = (df['TimeOnPage_seconds'] < 0).sum()
    if neg_time > 0:
        issues['negative_time'] = int(neg_time)

    neg_items = (df['ItemsInCart'] < 0).sum()
    if neg_items > 0:
        issues['negative_items'] = int(neg_items)

    if issues:
        logger.warning("数据完整性问题: %s", issues)
    else:
        logger.info("数据完整性检查通过")

    return issues
