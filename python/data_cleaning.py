"""数据清洗模块：基础清洗 + 漏斗专属清洗 + 漏斗宽表生成"""
import pandas as pd
import numpy as np
from python.config import (
    MIN_SESSION_DURATION, MAX_SINGLE_PAGE_DURATION,
    FUNNEL_STAGES, CLEANED_CSV, FUNNEL_WIDE_CSV, logger,
)


def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """基础脏数据清洗"""
    logger.info("=" * 60)
    logger.info("2. 数据清洗")
    logger.info("=" * 60)
    total_original = len(df)

    # 1. 去重
    before = len(df)
    df = df.drop_duplicates(
        subset=["SessionID", "UserID", "Timestamp", "PageType"],
        keep="first",
    )
    logger.info("去重: %s -> %s (丢弃 %s)", f"{before:,}", f"{len(df):,}",
                f"{before - len(df):,}")

    # 2. 核心字段非空
    core_cols = ['SessionID', 'UserID', 'PageType', 'Timestamp', 'Purchased']
    before = len(df)
    df = df.dropna(subset=core_cols)
    logger.info("核心字段非空过滤: 丢弃 %s", f"{before - len(df):,}")

    # 3. 非核心字段填充
    df[["Country", "ReferralSource"]] = df[["Country", "ReferralSource"]].fillna("Unknown")
    df[["TimeOnPage_seconds", "ItemsInCart", "Purchased"]] = (
        df[["TimeOnPage_seconds", "ItemsInCart", "Purchased"]].fillna(0)
    )

    # 4. 时间类型转换 + 未来时间过滤
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    before = len(df)
    df = df[df['Timestamp'] < pd.Timestamp.now()]
    logger.info("未来时间过滤: 丢弃 %s", f"{before - len(df):,}")

    # 5. 数值异常过滤
    before = len(df)
    df = df[
        (df['TimeOnPage_seconds'] >= 0) &
        (df['TimeOnPage_seconds'] <= MAX_SINGLE_PAGE_DURATION) &
        (df['ItemsInCart'] >= 0)
    ]
    logger.info("数值异常过滤: 丢弃 %s", f"{before - len(df):,}")

    # 6. Purchased 仅允许 0/1
    before = len(df)
    df = df[df['Purchased'].isin([0, 1])]
    logger.info("Purchased值域过滤: 丢弃 %s", f"{before - len(df):,}")

    # 7. 格式统一
    df["PageType"] = df["PageType"].str.lower()
    df["DeviceType"] = df["DeviceType"].str.capitalize()

    pct = len(df) / total_original * 100
    logger.info("基础清洗完成: %s -> %s (保留 %.1f%%)",
                f"{total_original:,}", f"{len(df):,}", pct)
    return df.copy()


def funnel_specific_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """漏斗专属清洗：排序、会话内去重、无效会话过滤、特征衍生"""
    logger.info("=" * 60)
    logger.info("3. 漏斗专属清洗")
    logger.info("=" * 60)

    # 1. 按会话+时间排序
    df = df.sort_values(by=["SessionID", "Timestamp"]).reset_index(drop=True)

    # 2. 会话内页面去重（保留首次访问）
    before = len(df)
    df = df.drop_duplicates(subset=["SessionID", "PageType"], keep="first")
    logger.info("会话内去重: %s -> %s (丢弃 %s)", f"{before:,}", f"{len(df):,}",
                f"{before - len(df):,}")

    # 3. 无效会话过滤：总停留时长 < 阈值
    session_dur = df.groupby("SessionID")["TimeOnPage_seconds"].sum()
    valid = session_dur[session_dur >= MIN_SESSION_DURATION].index
    before = df['SessionID'].nunique()
    df = df[df["SessionID"].isin(valid)]
    after = df['SessionID'].nunique()
    logger.info("无效会话过滤(总停留<%ds): %s -> %s 会话",
                MIN_SESSION_DURATION, f"{before:,}", f"{after:,}")

    # 4. 衍生时间特征
    df['hour'] = df['Timestamp'].dt.hour
    df['weekday'] = df['Timestamp'].dt.weekday
    df['date'] = df['Timestamp'].dt.date

    # 5. 漏斗阶段标准化映射
    df['stage'] = df['PageType'].map(FUNNEL_STAGES)

    # 6. 会话级转化标签
    session_conversion = df.groupby('SessionID')['Purchased'].max().reset_index()
    session_conversion.columns = ['SessionID', 'session_is_converted']
    df = df.merge(session_conversion, on='SessionID', how='left')

    logger.info("漏斗清洗完成: %s 条, %s 会话",
                f"{len(df):,}", f"{df['SessionID'].nunique():,}")
    return df


def build_funnel_wide(df: pd.DataFrame) -> pd.DataFrame:
    """生成漏斗宽表：每个会话一行，含各漏斗步骤的 0/1 标记"""
    logger.info("=" * 60)
    logger.info("4. 生成漏斗宽表")
    logger.info("=" * 60)

    # 获取会话核心属性（取众数）
    attrib_cols = ['DeviceType', 'Country', 'ReferralSource']
    session_attribs = (
        df.groupby('SessionID')[attrib_cols]
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0])
    )

    # 生成漏斗步骤标记
    funnel_wide = df.groupby("SessionID").agg(
        UserID=("UserID", "first"),
        step1_home=("PageType", lambda x: int("home" in x.values)),
        step2_product=("PageType", lambda x: int("product_page" in x.values)),
        step3_cart=("PageType", lambda x: int("cart" in x.values)),
        step4_checkout=("PageType", lambda x: int("checkout" in x.values)),
        step5_confirm=("PageType", lambda x: int("confirmation" in x.values)),
        is_purchased=("Purchased", "max"),
    ).reset_index()

    # 合并会话属性
    funnel_wide = funnel_wide.merge(
        session_attribs, on='SessionID', how='left'
    )

    logger.info("漏斗宽表: %s 会话 x %s 列", f"{len(funnel_wide):,}",
                f"{len(funnel_wide.columns)}")

    steps = ['step1_home', 'step2_product', 'step3_cart',
             'step4_checkout', 'step5_confirm']
    for s in steps:
        logger.info("  %s: %s", s, f"{funnel_wide[s].sum():,}")

    # 漏斗逻辑校验
    confirm = funnel_wide[funnel_wide['step5_confirm'] == 1]
    assert (confirm['step4_checkout'] == 1).all(), "step5=1 但 step4=0"
    assert (funnel_wide['is_purchased'] == funnel_wide['step5_confirm']).all(), \
        "is_purchased 与 step5 不一致"
    logger.info("漏斗逻辑校验通过")

    return funnel_wide


def save_cleaned_data(df: pd.DataFrame, funnel_wide: pd.DataFrame) -> None:
    """保存清洗后数据和漏斗宽表"""
    df.to_csv(CLEANED_CSV, index=False, encoding='utf-8-sig')
    logger.info("已保存: %s (%s 条)", CLEANED_CSV, f"{len(df):,}")
    funnel_wide.to_csv(FUNNEL_WIDE_CSV, index=False, encoding='utf-8-sig')
    logger.info("已保存: %s (%s 条)", FUNNEL_WIDE_CSV, f"{len(funnel_wide):,}")
