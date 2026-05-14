"""漏斗分析模块：核心漏斗构建 + 多维度拆解 + 损失金额量化 + PIE 优先级"""
import pandas as pd
import numpy as np
from scipy import stats
from python.config import (
    FUNNEL_ORDER, STEP_COLUMNS, FUNNEL_STAGES, logger,
)


def compute_funnel(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """计算全链路转化漏斗"""
    logger.info("=" * 60)
    logger.info("5. 漏斗核心分析")
    logger.info("=" * 60)

    step_names = FUNNEL_ORDER
    step_cols = STEP_COLUMNS
    counts = [int(funnel_wide[col].sum()) for col in step_cols]

    funnel_df = pd.DataFrame({
        '漏斗阶段': step_names,
        '独立会话数': counts,
    })

    funnel_df['上一阶段转化率(%)'] = (
        funnel_df['独立会话数'] / funnel_df['独立会话数'].shift(1)
    ).fillna(1.0) * 100
    funnel_df['整体转化率(%)'] = (
        funnel_df['独立会话数'] / funnel_df['独立会话数'].iloc[0]
    ) * 100

    funnel_df['上一阶段转化率(%)'] = funnel_df['上一阶段转化率(%)'].round(2)
    funnel_df['整体转化率(%)'] = funnel_df['整体转化率(%)'].round(2)

    for _, row in funnel_df.iterrows():
        logger.info("  %s: %s (上阶段 %.2f%% / 整体 %.2f%%)",
                    row['漏斗阶段'], f"{int(row['独立会话数']):,}",
                    row['上一阶段转化率(%)'], row['整体转化率(%)'])

    churn_idx = funnel_df[1:]['上一阶段转化率(%)'].idxmin()
    logger.info("最高流失环节: %s", funnel_df.loc[churn_idx, '漏斗阶段'])

    return funnel_df


def compute_channel_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """各渠道转化率分析"""
    logger.info("=" * 60)
    logger.info("6. 分渠道转化率分析")
    logger.info("=" * 60)

    total_sessions = funnel_wide['SessionID'].nunique()
    result = funnel_wide.groupby('ReferralSource').agg(
        总会话数=('SessionID', 'nunique'),
        转化会话数=('is_purchased', 'sum'),
    )
    result['整体转化率'] = (result['转化会话数'] / result['总会话数'] * 100).round(2)
    result['流量占比(%)'] = (result['总会话数'] / total_sessions * 100).round(2)
    result = result.sort_values('整体转化率', ascending=False)

    for ch, row in result.iterrows():
        logger.info("  %s: %s/%s (%.2f%%) 流量占比 %.2f%%",
                    ch, f"{int(row['转化会话数']):,}", f"{int(row['总会话数']):,}",
                    row['整体转化率'], row['流量占比(%)'])

    return result


def compute_device_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """各设备转化率分析"""
    logger.info("=" * 60)
    logger.info("7. 分设备转化率分析")
    logger.info("=" * 60)

    total_sessions = funnel_wide['SessionID'].nunique()
    result = funnel_wide.groupby('DeviceType').agg(
        总会话数=('SessionID', 'nunique'),
        转化会话数=('is_purchased', 'sum'),
    )
    result['整体转化率'] = (result['转化会话数'] / result['总会话数'] * 100).round(2)
    result['流量占比(%)'] = (result['总会话数'] / total_sessions * 100).round(2)
    result = result.sort_values('整体转化率', ascending=False)

    for dev, row in result.iterrows():
        logger.info("  %s: %s/%s (%.2f%%) 流量占比 %.2f%%",
                    dev, f"{int(row['转化会话数']):,}", f"{int(row['总会话数']):,}",
                    row['整体转化率'], row['流量占比(%)'])

    return result


def compute_duration_analysis(df_cleaned: pd.DataFrame) -> pd.DataFrame:
    """停留时长与转化率关系（等频分桶）"""
    logger.info("=" * 60)
    logger.info("8. 停留时长与转化率分析")
    logger.info("=" * 60)

    session_dur = df_cleaned.groupby('SessionID').agg(
        总停留时长=('TimeOnPage_seconds', 'sum'),
        是否转化=('session_is_converted', 'max'),
    )

    q25 = session_dur['总停留时长'].quantile(0.25)
    q50 = session_dur['总停留时长'].quantile(0.50)
    q75 = session_dur['总停留时长'].quantile(0.75)
    qmax = session_dur['总停留时长'].max()

    session_dur['时长分桶'] = pd.cut(
        session_dur['总停留时长'],
        bins=[0, q25, q50, q75, qmax],
        labels=[
            f'快速浏览 (0-{int(q25)}s)',
            f'浅层参与 ({int(q25)}-{int(q50)}s)',
            f'中度参与 ({int(q50)}-{int(q75)}s)',
            f'深度决策 ({int(q75)}-{int(qmax)}s)',
        ],
    )

    result = session_dur.groupby('时长分桶', observed=True).agg(
        会话数=('是否转化', 'count'),
        转化会话数=('是否转化', 'sum'),
    )
    result['转化率(%)'] = (result['转化会话数'] / result['会话数'] * 100).round(2)

    for bucket, row in result.iterrows():
        logger.info("  %s: %s 会话, 转化率 %.2f%%",
                    bucket, f"{int(row['会话数']):,}", row['转化率(%)'])

    return result


def compute_cart_item_analysis(df_cleaned: pd.DataFrame,
                                funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """购物车商品数与转化率关系"""
    logger.info("=" * 60)
    logger.info("9. 购物车商品数与转化率分析")
    logger.info("=" * 60)

    cart_info = df_cleaned[df_cleaned['PageType'] == 'cart'] \
        .groupby('SessionID')['ItemsInCart'].max().reset_index()
    cart_info = cart_info.merge(
        funnel_wide[['SessionID', 'is_purchased']], on='SessionID', how='inner',
    )

    bins = [-1, 0, 2, 5, 10, float('inf')]
    labels = ['0件', '1-2件', '3-5件', '6-10件', '10件+']
    cart_info['购物车分桶'] = pd.cut(cart_info['ItemsInCart'], bins=bins, labels=labels)

    result = cart_info.groupby('购物车分桶', observed=True).agg(
        会话数=('SessionID', 'nunique'),
        转化数=('is_purchased', 'sum'),
    )
    result['转化率(%)'] = (result['转化数'] / result['会话数'] * 100).round(2)

    for bucket, row in result.iterrows():
        logger.info("  %s: %s 会话, 转化率 %.2f%%",
                    bucket, f"{int(row['会话数']):,}", row['转化率(%)'])

    return result


def compute_loss_amount(funnel_wide: pd.DataFrame,
                         avg_cart_value: float = None) -> pd.DataFrame:
    """量化各环节损失金额"""
    logger.info("=" * 60)
    logger.info("10. 各环节损失金额量化")
    logger.info("=" * 60)

    if avg_cart_value is None:
        avg_cart_value = 100.0

    stage_pairs = [
        ('1.访问首页 → 2.浏览商品', 'step1_home', 'step2_product', 0.5),
        ('2.浏览商品 → 3.加入购物车', 'step2_product', 'step3_cart', 0.5),
        ('3.加入购物车 → 4.提交订单', 'step3_cart', 'step4_checkout', 1.0),
        ('4.提交订单 → 5.支付成功', 'step4_checkout', 'step5_confirm', 1.2),
    ]

    losses = []
    for label, stage_col, next_col, weight in stage_pairs:
        lost = funnel_wide[
            (funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 0)
        ]
        lost_count = len(lost)
        unit_value = avg_cart_value * weight
        loss_amount = lost_count * unit_value

        losses.append({
            '漏斗环节': label,
            '流失会话数': lost_count,
            '入环节会话数': int(funnel_wide[stage_col].sum()),
            '环节流失率(%)': round(lost_count / funnel_wide[stage_col].sum() * 100, 2),
            '估算单会话价值': round(unit_value, 2),
            '估算损失金额': round(loss_amount, 2),
        })

    loss_df = pd.DataFrame(losses)
    total_loss = loss_df['估算损失金额'].sum()

    for _, row in loss_df.iterrows():
        logger.info("  %s: 流失 %s 会话 (%.2f%%), 损失 Y%s",
                    row['漏斗环节'], f"{int(row['流失会话数']):,}",
                    row['环节流失率(%)'], f"{row['估算损失金额']:,.0f}")

    logger.info("估算总损失金额: Y%s", f"{total_loss:,.0f}")
    return loss_df


def compute_entry_path_analysis(df_cleaned: pd.DataFrame) -> pd.DataFrame:
    """进入路径分析：首次接触的页面类型对转化率的影响"""
    logger.info("=" * 60)
    logger.info("11. 进入路径分析")
    logger.info("=" * 60)

    entry_page = (
        df_cleaned.sort_values('Timestamp')
        .groupby('SessionID')
        .first()['PageType']
        .reset_index()
    )
    entry_page.columns = ['SessionID', 'entry_page']

    conversion = df_cleaned.groupby('SessionID')['session_is_converted'].max().reset_index()
    entry_page = entry_page.merge(conversion, on='SessionID')

    result = entry_page.groupby('entry_page').agg(
        会话数=('SessionID', 'nunique'),
        转化数=('session_is_converted', 'sum'),
    )
    result['转化率(%)'] = (result['转化数'] / result['会话数'] * 100).round(2)
    result['流量占比(%)'] = (result['会话数'] / result['会话数'].sum() * 100).round(2)
    result = result.sort_values('转化率(%)', ascending=False)

    for ep, row in result.iterrows():
        logger.info("  %s: %s 会话 (%.2f%%), 转化率 %.2f%%",
                    ep, f"{int(row['会话数']):,}", row['流量占比(%)'], row['转化率(%)'])

    return result


def compute_time_of_day_analysis(df_cleaned: pd.DataFrame):
    """时段分析：按小时和星期几的流量与转化率"""
    logger.info("=" * 60)
    logger.info("12. 时段分析 (hour x weekday)")
    logger.info("=" * 60)

    session_level = df_cleaned.drop_duplicates('SessionID')[
        ['SessionID', 'hour', 'weekday', 'session_is_converted']
    ]

    hourly = session_level.groupby('hour').agg(
        会话数=('SessionID', 'nunique'),
        转化率=('session_is_converted', 'mean'),
    ).round(4)
    hourly['转化率'] = (hourly['转化率'] * 100).round(2)

    weekday_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu',
                   4: 'Fri', 5: 'Sat', 6: 'Sun'}
    session_level['星期'] = session_level['weekday'].map(weekday_map)
    weekday_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dow = session_level.groupby('星期').agg(
        会话数=('SessionID', 'nunique'),
        转化率=('session_is_converted', 'mean'),
    ).round(4)
    dow['转化率'] = (dow['转化率'] * 100).round(2)
    dow = dow.reindex([d for d in weekday_order if d in dow.index])

    peak_hour = hourly['会话数'].idxmax()
    best_hour = hourly['转化率'].idxmax()
    logger.info("流量高峰: %s点, 转化率最高: %s点", peak_hour, best_hour)
    logger.info("高峰日: %s", dow['会话数'].idxmax())

    return hourly, dow


def channel_device_cross_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """渠道 x 设备交叉转化率矩阵"""
    logger.info("=" * 60)
    logger.info("13. 渠道x设备交叉分析")
    logger.info("=" * 60)

    cross = funnel_wide.groupby(['ReferralSource', 'DeviceType']).agg(
        会话数=('SessionID', 'nunique'),
        转化数=('is_purchased', 'sum'),
    )
    cross['转化率(%)'] = (cross['转化数'] / cross['会话数'] * 100).round(2)
    cross = cross.sort_values('会话数', ascending=False)

    worst = cross[cross['会话数'] >= 10].nsmallest(3, '转化率(%)')
    logger.info("转化率最低的组合:")
    for idx, row in worst.iterrows():
        logger.info("  %s x %s: %.2f%% (%s 会话)",
                    idx[0], idx[1], row['转化率(%)'], f"{int(row['会话数']):,}")

    return cross


def statistical_tests(funnel_wide: pd.DataFrame,
                       df_cleaned: pd.DataFrame = None) -> dict:
    """统计检验：渠道/设备与转化之间的显著性"""
    logger.info("=" * 60)
    logger.info("14. 统计检验")
    logger.info("=" * 60)

    results = {}

    # 卡方检验：渠道与转化
    contingency = pd.crosstab(funnel_wide['ReferralSource'], funnel_wide['is_purchased'])
    chi2, p_val, dof, _ = stats.chi2_contingency(contingency)
    sig = 'significant' if p_val < 0.05 else 'not significant'
    results['channel_chi2'] = {'chi2': chi2, 'p': p_val, 'sig': sig}
    logger.info("Channel x Conversion chi2: X2=%.2f, p=%.4f (%s)", chi2, p_val, sig)

    # 卡方检验：设备与转化
    contingency_dev = pd.crosstab(funnel_wide['DeviceType'], funnel_wide['is_purchased'])
    chi2_dev, p_dev, dof_dev, _ = stats.chi2_contingency(contingency_dev)
    sig_dev = 'significant' if p_dev < 0.05 else 'not significant'
    results['device_chi2'] = {'chi2': chi2_dev, 'p': p_dev, 'sig': sig_dev}
    logger.info("Device x Conversion chi2: X2=%.2f, p=%.4f (%s)", chi2_dev, p_dev, sig_dev)

    return results


def compute_pie_priority(loss_df: pd.DataFrame) -> pd.DataFrame:
    """PIE 优先级矩阵"""
    logger.info("=" * 60)
    logger.info("15. PIE 优先级计算")
    logger.info("=" * 60)

    total_loss = loss_df['估算损失金额'].sum()
    total_sessions = loss_df['入环节会话数'].max()

    pie = loss_df.copy()
    pie['Potential'] = (pie['估算损失金额'] / total_loss * 10).clip(1, 10).round(1)
    pie['Importance'] = (pie['入环节会话数'] / total_sessions * 10).clip(1, 10).round(1)

    ease_map = {
        '1.访问首页 → 2.浏览商品': 7,
        '2.浏览商品 → 3.加入购物车': 6,
        '3.加入购物车 → 4.提交订单': 5,
        '4.提交订单 → 5.支付成功': 8,
    }
    pie['Ease'] = pie['漏斗环节'].map(ease_map).fillna(5)

    pie['PIE得分'] = (pie['Potential'] * pie['Importance'] * pie['Ease']).round(0)
    pie = pie.sort_values('PIE得分', ascending=False)

    for _, row in pie.iterrows():
        logger.info("  %s: PIE=%.0f (P=%.1f I=%.1f E=%.1f) - Loss Y%s",
                    row['漏斗环节'], row['PIE得分'],
                    row['Potential'], row['Importance'], row['Ease'],
                    f"{row['估算损失金额']:,.0f}")

    return pie
