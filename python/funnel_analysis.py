"""漏斗分析模块 — 六阶段全流程分析引擎"""
import json
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats

from python.config import (
    PAGE_FUNNEL_ORDER, PAGE_FUNNEL_COLS,
    EVENT_FUNNEL_ORDER, EVENT_FUNNEL_COLS,
    STRICT_PAGE_STAGES, STRICT_PAGE_ORDER,
    CHURN_STAGES, DURATION_BINS, DURATION_LABELS,
    BASELINE_JSON, logger,
)


def _compute_page_coverage(df, steps, labels):
    """页面覆盖分析 — 交叉到达率：同时到达前后两页 / 到达前页"""
    counts = [int(df[col].sum()) for col in steps]
    rates = [100.0]
    for i in range(1, len(steps)):
        prev = counts[i - 1]
        both = int(((df[steps[i - 1]] == 1) & (df[steps[i]] == 1)).sum())
        rates.append(round(both / prev * 100, 2) if prev > 0 else 0.0)
    funnel_df = pd.DataFrame({
        '漏斗阶段': labels,
        '到达会话数': counts,
        '交叉到达率(%)': rates,
    })
    funnel_df['整体到达率(%)'] = (funnel_df['到达会话数'] / len(df) * 100).round(2)
    return funnel_df


# ═══════════════════════════════════════════════════════════════
# 阶段 2: 漏斗建模拆解
# ═══════════════════════════════════════════════════════════════

def compute_page_funnel(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """页面覆盖分析 — 各页面独立到达统计 + 相邻页面交叉到达率

    重要: 这是**页面覆盖分析** (Page Coverage), 不是严格路径漏斗。
    - 每个页面的到达会话数是独立统计的 ("只要访问过该页面即计入")
    - 多入口/深链场景下, 下游页面会话数可能超过上游 (如 PLP > Home)
    - "交叉到达率" = 同时到达前后两页的会话 / 到达前页的会话
      这是重叠率 (Overlap Rate), 不是严格顺序转化率
    - 如需严格按时间顺序的漏斗, 请使用 compute_strict_page_funnel()
    """
    logger.info("=" * 60)
    logger.info("6. 页面覆盖分析 (Page Coverage)")
    logger.info("=" * 60)
    logger.info("注意: 这是页面覆盖统计, 非严格路径漏斗。下游页面可因深链流量超过上游。")

    funnel_df = _compute_page_coverage(funnel_wide, PAGE_FUNNEL_COLS, PAGE_FUNNEL_ORDER)

    # 检测倒挂现象并警示
    counts = funnel_df['到达会话数'].tolist()
    for i in range(1, len(counts)):
        if counts[i] > counts[i - 1]:
            logger.info(
                "  [深链警示] %s 到达 (%s) > %s 到达 (%s) — 存在直接落地该页面的深链流量",
                PAGE_FUNNEL_ORDER[i], f"{counts[i]:,}",
                PAGE_FUNNEL_ORDER[i - 1], f"{counts[i - 1]:,}",
            )

    for _, row in funnel_df.iterrows():
        logger.info("  %s: %s (交叉到达率 %.2f%% / 整体到达率 %.2f%%)",
                    row['漏斗阶段'], f"{int(row['到达会话数']):,}",
                    row['交叉到达率(%)'], row['整体到达率(%)'])

    churn_idx = funnel_df[1:]['交叉到达率(%)'].idxmin()
    logger.info("页面覆盖最大断点: %s (交叉到达率 %.2f%%)",
                funnel_df.loc[churn_idx, '漏斗阶段'],
                funnel_df.loc[churn_idx, '交叉到达率(%)'])
    return funnel_df


def compute_strict_page_funnel(funnel_wide: pd.DataFrame,
                               events: pd.DataFrame) -> pd.DataFrame:
    """严格路径漏斗 — 必须按 Home→PLP→PDP→Cart→Checkout 时间顺序访问

    与 compute_page_funnel（页面覆盖分析）的区别：
    - 覆盖分析：只要到达过该页面即计入，允许多入口/深链，人数可能倒挂
    - 严格路径：必须按顺序 A→B→C（前页首次访问时间 < 后页首次访问时间），人数必递减
    """
    logger.info("--- 严格路径漏斗 (时间顺序) ---")

    stages = STRICT_PAGE_STAGES

    # 每会话每页面的首次访问时间
    page_first = (
        events.groupby(['session_id', 'page_category'])['timestamp']
        .min()
        .reset_index()
    )
    pivot = page_first.pivot(
        index='session_id', columns='page_category', values='timestamp'
    )

    counts = []
    for i, stage in enumerate(stages):
        if i == 0:
            count = int(pivot[stage].notna().sum())
        else:
            mask = pivot[stages[i]].notna()
            for j in range(1, i + 1):
                mask = mask & (pivot[stages[j]] > pivot[stages[j - 1]])
            count = int(mask.sum())
        counts.append(count)

    # 与覆盖分析对比
    coverage_counts = [int(funnel_wide[col].sum()) for col in PAGE_FUNNEL_COLS]

    funnel_df = pd.DataFrame({
        '漏斗阶段': STRICT_PAGE_ORDER,
        '严格路径到达会话数': counts,
        '覆盖到达会话数': coverage_counts,
    })

    total_sessions = len(funnel_wide)
    funnel_df['顺序转化率(%)'] = [100.0] + [
        round(counts[i] / counts[i - 1] * 100, 2) if counts[i - 1] > 0 else 0
        for i in range(1, len(counts))
    ]
    funnel_df['整体留存率(%)'] = (
        funnel_df['严格路径到达会话数'] / total_sessions * 100
    ).round(2)
    funnel_df['覆盖-严格差异'] = [
        coverage_counts[i] - counts[i] for i in range(len(counts))
    ]

    for _, row in funnel_df.iterrows():
        logger.info(
            "  %s: 严格 %s (留存率 %.1f%%) | 覆盖 %s | 差异 %s",
            row['漏斗阶段'],
            f"{int(row['严格路径到达会话数']):,}",
            row['整体留存率(%)'],
            f"{int(row['覆盖到达会话数']):,}",
            f"{int(row['覆盖-严格差异']):,}",
        )

    loss = funnel_df.iloc[-1]
    logger.info(
        "严格漏斗 Home→Checkout 留存: %.2f%% (%s / %s)",
        loss['整体留存率(%)'],
        f"{int(loss['严格路径到达会话数']):,}",
        f"{int(funnel_df.iloc[0]['严格路径到达会话数']):,}",
    )
    return funnel_df


def compute_deep_link_analysis(
    funnel_wide: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """深链流量分析 — 直接落地 PLP 的会话 vs 经首页路径会话

    Returns:
        (path_summary, channel_comparison)
        - path_summary: 各路径类型转化率
        - channel_comparison: 分渠道 深链 vs 首页路径 转化率对比
    """
    logger.info("=" * 60)
    logger.info("深链流量分析")
    logger.info("=" * 60)

    # 路径分类
    has_home = funnel_wide['step1_home'] == 1
    has_plp = funnel_wide['step2_plp'] == 1
    conditions = [
        (has_plp & ~has_home),
        (has_home & has_plp),
        (has_home & ~has_plp),
    ]
    choices = ['深链直达PLP', '首页→PLP', '仅首页']
    funnel_wide = funnel_wide.copy()
    funnel_wide['path_type'] = np.select(conditions, choices, default='其他')

    # 整体对比
    path_summary = (
        funnel_wide.groupby('path_type', observed=True)
        .agg(
            会话数=('session_id', 'nunique'),
            购买会话数=('step_purchase', 'sum'),
        )
    )
    path_summary['转化率(%)'] = (
        path_summary['购买会话数'] / path_summary['会话数'] * 100
    ).round(2)
    path_summary['流量占比(%)'] = (
        path_summary['会话数'] / len(funnel_wide) * 100
    ).round(2)
    path_summary = path_summary.sort_values('会话数', ascending=False)

    for pt, row in path_summary.iterrows():
        logger.info(
            "  %s: %s 会话 (%.1f%%), 转化率 %.2f%%",
            pt,
            f"{int(row['会话数']):,}",
            row['流量占比(%)'],
            row['转化率(%)'],
        )

    # 分渠道深链 vs 首页路径对比
    deep_link = funnel_wide[funnel_wide['path_type'] == '深链直达PLP']
    home_path = funnel_wide[funnel_wide['path_type'] == '首页→PLP']

    deep_by_ch = (
        deep_link.groupby('traffic_source')
        .agg(深链会话=('session_id', 'nunique'), 深链购买=('step_purchase', 'sum'))
    )
    home_by_ch = (
        home_path.groupby('traffic_source')
        .agg(首页路径会话=('session_id', 'nunique'), 首页路径购买=('step_purchase', 'sum'))
    )

    comparison = deep_by_ch.join(home_by_ch, how='outer').fillna(0).astype(int)
    comparison['深链转化率(%)'] = (
        comparison['深链购买'] / comparison['深链会话'].replace(0, np.nan) * 100
    ).round(2)
    comparison['首页路径转化率(%)'] = (
        comparison['首页路径购买'] / comparison['首页路径会话'].replace(0, np.nan) * 100
    ).round(2)
    comparison['转化率差异(pp)'] = (
        comparison['首页路径转化率(%)'] - comparison['深链转化率(%)']
    ).round(2)
    comparison = comparison.sort_values('深链会话', ascending=False)

    for ch, row in comparison.iterrows():
        logger.info(
            "  %s: 深链 %.2f%% (%s) vs 首页路径 %.2f%% (%s) | 差异 %+.1fpp",
            ch,
            row['深链转化率(%)'],
            f"{int(row['深链会话']):,}",
            row['首页路径转化率(%)'],
            f"{int(row['首页路径会话']):,}",
            row['转化率差异(pp)'],
        )

    return path_summary, comparison


def compute_event_funnel(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """行为级漏斗 (view→click→add_to_cart→purchase) — 顺序递进"""
    logger.info("=" * 60)
    logger.info("7. 行为级漏斗分析")
    logger.info("=" * 60)

    counts = [int(funnel_wide[col].sum()) for col in EVENT_FUNNEL_COLS]
    funnel_df = pd.DataFrame({'漏斗阶段': EVENT_FUNNEL_ORDER, '会话数': counts})
    funnel_df['上一阶段转化率(%)'] = (
        funnel_df['会话数'] / funnel_df['会话数'].shift(1)
    ).fillna(1.0) * 100
    funnel_df['整体转化率(%)'] = (
        funnel_df['会话数'] / funnel_df['会话数'].iloc[0]
    ) * 100
    funnel_df['上一阶段转化率(%)'] = funnel_df['上一阶段转化率(%)'].round(2)
    funnel_df['整体转化率(%)'] = funnel_df['整体转化率(%)'].round(2)

    for _, row in funnel_df.iterrows():
        logger.info("  %s: %s (上阶段 %.2f%% / 整体 %.2f%%)",
                    row['漏斗阶段'], f"{int(row['会话数']):,}",
                    row['上一阶段转化率(%)'], row['整体转化率(%)'])

    churn_idx = funnel_df[1:]['上一阶段转化率(%)'].idxmin()
    logger.info("行为漏斗最高流失环节: %s", funnel_df.loc[churn_idx, '漏斗阶段'])
    return funnel_df


def compute_channel_funnels(funnel_wide: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """每个 traffic_source 独立页面覆盖漏斗 + 交叉到达率"""
    logger.info("=" * 60)
    logger.info("8. 各渠道页面覆盖漏斗")
    logger.info("=" * 60)

    steps = PAGE_FUNNEL_COLS
    channel_funnels = {}
    for channel in funnel_wide['traffic_source'].unique():
        ch_data = funnel_wide[funnel_wide['traffic_source'] == channel]
        counts = [int(ch_data[col].sum()) for col in steps]
        funnel_df = pd.DataFrame({'漏斗阶段': PAGE_FUNNEL_ORDER, '到达会话数': counts})

        rates = [100.0]
        for i in range(1, len(steps)):
            prev = counts[i - 1]
            both = int(((ch_data[steps[i - 1]] == 1) & (ch_data[steps[i]] == 1)).sum())
            rate = min(round(both / prev * 100, 2), 100.0) if prev > 0 else 0.0
            rates.append(rate)

        ch_total = len(ch_data)
        funnel_df['交叉到达率(%)'] = rates
        funnel_df['整体到达率(%)'] = (funnel_df['到达会话数'] / ch_total * 100).round(2) if ch_total > 0 else 0
        channel_funnels[channel] = funnel_df

        # 交叉到达率瓶颈 (最小交叉到达率)
        churn_idx = funnel_df[1:]['交叉到达率(%)'].idxmin()
        # 绝对流失瓶颈 (最大绝对流失 = 前阶段覆盖 - 交叉到达)
        overlap_counts = []
        for i in range(1, len(steps)):
            both_val = int(
                ((ch_data[steps[i - 1]] == 1) & (ch_data[steps[i]] == 1)).sum()
            )
            overlap_counts.append(both_val)
        absolute_losses = [
            counts[i - 1] - overlap_counts[i - 1] for i in range(1, len(counts))
        ]
        abs_churn_idx = absolute_losses.index(max(absolute_losses)) + 1  # +1 skip index 0

        logger.info(
            "  %s: 交叉到达率瓶颈=%s (%.2f%%), 绝对流失瓶颈=%s (%s 会话流失)",
            channel,
            funnel_df.loc[churn_idx, '漏斗阶段'],
            funnel_df.loc[churn_idx, '交叉到达率(%)'],
            funnel_df.loc[abs_churn_idx, '漏斗阶段'],
            f"{max(absolute_losses):,}",
        )

    return channel_funnels


# ═══════════════════════════════════════════════════════════════
# 阶段 3: 多维度拆解诊断
# ═══════════════════════════════════════════════════════════════

def _dimension_analysis(funnel_wide: pd.DataFrame, dim_col: str,
                        label: str = '') -> pd.DataFrame:
    """通用维度转化率分析"""
    logger.info("--- %s ---", label)

    total = funnel_wide['session_id'].nunique()
    result = funnel_wide.groupby(dim_col).agg(
        总会话数=('session_id', 'nunique'),
        购买会话数=('step_purchase', 'sum'),
    )
    result['转化率(%)'] = (result['购买会话数'] / result['总会话数'] * 100).round(2)
    result['流量占比(%)'] = (result['总会话数'] / total * 100).round(2)
    result = result.sort_values('转化率(%)', ascending=False)

    for v, row in result.iterrows():
        logger.info("  %s: %s/%s (%.2f%%) 流量占比 %.1f%%",
                    v, f"{int(row['购买会话数']):,}", f"{int(row['总会话数']):,}",
                    row['转化率(%)'], row['流量占比(%)'])
    return result


def compute_channel_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    return _dimension_analysis(funnel_wide, 'traffic_source', '渠道转化率分析')


def compute_device_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    return _dimension_analysis(funnel_wide, 'device_type', '设备转化率分析')


def compute_country_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    return _dimension_analysis(funnel_wide, 'country', '国家转化率分析')


def compute_loyalty_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    return _dimension_analysis(funnel_wide, 'loyalty_tier', '用户忠诚度转化率分析')


def compute_acquisition_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    return _dimension_analysis(funnel_wide, 'acquisition_channel', '获客渠道转化率分析')


def compute_new_vs_returning_funnel(
    funnel_wide: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """新用户 vs 老用户 漏斗对比 — CRO 最核心的分层维度

    新用户 (Prospect): is_purchased == 0，从未购买过，分析其首次转化障碍
    老用户 (Returning): is_purchased == 1，已有购买记录，分析其复购/留存漏斗

    分别构建页面漏斗和行为漏斗，对比两组的流失模式差异。
    """
    logger.info("=" * 60)
    logger.info("新用户 vs 老用户 漏斗分析")
    logger.info("=" * 60)

    new_users = funnel_wide[funnel_wide['is_purchased'] == 0]
    returning_users = funnel_wide[funnel_wide['is_purchased'] == 1]

    logger.info(
        "  新用户(未购买过): %s 会话 (%.1f%%) | 老用户(已购买): %s 会话 (%.1f%%)",
        f"{len(new_users):,}", len(new_users) / len(funnel_wide) * 100,
        f"{len(returning_users):,}", len(returning_users) / len(funnel_wide) * 100,
    )

    results = {}
    steps = PAGE_FUNNEL_COLS

    # 页面漏斗对比
    for label, subset in [('新用户(未购买)', new_users), ('老用户(已购买)', returning_users)]:
        funnel_df = _compute_page_coverage(subset, steps, PAGE_FUNNEL_ORDER)
        results[f'{label}_page'] = funnel_df

        churn_idx = funnel_df[1:]['交叉到达率(%)'].idxmin()
        logger.info(
            "  %s 页面漏斗: 瓶颈=%s (交叉到达率 %.2f%%) | Home→Checkout %.2f%%",
            label,
            funnel_df.loc[churn_idx, '漏斗阶段'],
            funnel_df.loc[churn_idx, '交叉到达率(%)'],
            funnel_df.iloc[-1]['整体到达率(%)'],
        )

    # 行为漏斗对比
    event_steps = EVENT_FUNNEL_COLS
    event_labels = EVENT_FUNNEL_ORDER
    for label, subset in [('新用户(未购买)', new_users), ('老用户(已购买)', returning_users)]:
        counts = [int(subset[col].sum()) for col in event_steps]
        rates = [100.0] + [
            round(counts[i] / counts[i - 1] * 100, 2) if counts[i - 1] > 0 else 0.0
            for i in range(1, len(counts))
        ]
        funnel_df = pd.DataFrame({
            '漏斗阶段': event_labels,
            '会话数': counts,
            '上一阶段转化率(%)': rates,
        })
        funnel_df['整体转化率(%)'] = (
            funnel_df['会话数'] / funnel_df['会话数'].iloc[0] * 100
        ).round(2)
        results[f'{label}_event'] = funnel_df

        logger.info(
            "  %s 行为漏斗: view→purchase = %.2f%%",
            label, funnel_df.iloc[-1]['整体转化率(%)'],
        )

    # 新用户在哪个环节与老用户差距最大
    new_page = results['新用户(未购买)_page']
    ret_page = results['老用户(已购买)_page']
    gaps = []
    for i, stage in enumerate(PAGE_FUNNEL_ORDER):
        if i > 0:
            gap = (
                ret_page.iloc[i]['交叉到达率(%)']
                - new_page.iloc[i]['交叉到达率(%)']
            )
            gaps.append((stage, gap))
    if gaps:
        max_gap_stage, max_gap = max(gaps, key=lambda x: x[1])
        logger.info(
            "  新老用户最大转化率差距: %s (%.1fpp)", max_gap_stage, max_gap,
        )

    return results


def compute_weekend_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """周末 vs 工作日 转化率 + 漏斗对比"""
    logger.info("--- 周末 vs 工作日分析 ---")

    funnel_wide = funnel_wide.copy()
    funnel_wide['is_weekend'] = funnel_wide['weekday'].isin([5, 6])

    result = funnel_wide.groupby('is_weekend').agg(
        会话数=('session_id', 'nunique'),
        购买会话数=('step_purchase', 'sum'),
        浏览会话数=('step_view', 'sum'),
        加购会话数=('step_add_cart', 'sum'),
        均时长=('total_duration_sec', 'mean'),
    )
    result['CR(%)'] = (result['购买会话数'] / result['会话数'] * 100).round(2)
    result['浏览→加购(%)'] = (result['加购会话数'] / result['浏览会话数'] * 100).round(2)
    result['加购→购买(%)'] = (
        result['购买会话数'] / result['加购会话数'] * 100
    ).round(2)
    result['均时长'] = result['均时长'].round(0).astype(int)
    result.index = ['工作日', '周末']

    for idx, row in result.iterrows():
        logger.info(
            "  %s: %s 会话, CR %.2f%%, 浏览→加购 %.1f%%, 加购→购买 %.1f%%",
            idx, f"{int(row['会话数']):,}",
            row['CR(%)'], row['浏览→加购(%)'], row['加购→购买(%)'],
        )

    return result


def compute_category_funnel(funnel_wide: pd.DataFrame,
                            events: pd.DataFrame,
                            products: pd.DataFrame) -> pd.DataFrame:
    """品类漏斗：各品类的浏览→购买转化"""
    logger.info("--- 品类漏斗分析 ---")

    # 关联 product_id → category
    prod_cat = products[['product_id', 'category']].copy()
    events_with_cat = events[events['product_id'].notna()].copy()
    events_with_cat['product_id'] = events_with_cat['product_id'].astype(int)
    events_with_cat = events_with_cat.merge(prod_cat, on='product_id', how='left')

    # 按品类聚合 — 先用 event_type 筛选再 groupby，避免 lambda 闭包
    add_cart_by_cat = (
        events_with_cat[events_with_cat['event_type'] == 'add_to_cart']
        .groupby('category')['session_id'].nunique().reset_index(name='加购会话')
    )
    purchase_by_cat = (
        events_with_cat[events_with_cat['event_type'] == 'purchase']
        .groupby('category')['session_id'].nunique().reset_index(name='购买会话')
    )
    view_by_cat = (
        events_with_cat[events_with_cat['event_type'] == 'view']
        .groupby('category')['session_id'].nunique().reset_index(name='浏览会话')
    )
    cat_stats = view_by_cat.merge(add_cart_by_cat, on='category', how='left')
    cat_stats = cat_stats.merge(purchase_by_cat, on='category', how='left')
    cat_stats[['加购会话', '购买会话']] = cat_stats[['加购会话', '购买会话']].fillna(0).astype(int)

    # Wilson 95% CI for proportions — handles small-N categories
    def _wilson_ci(success, n, z=1.96):
        if n == 0:
            return (0.0, 0.0)
        p = success / n
        denom = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denom
        margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
        return (round(max(0, center - margin) * 100, 2),
                round(min(1, center + margin) * 100, 2))

    cat_stats['浏览→加购(%)'] = (cat_stats['加购会话'] / cat_stats['浏览会话'] * 100).round(2)
    cat_stats['加购→购买(%)'] = (cat_stats['购买会话'] / cat_stats['加购会话'] * 100).round(2)
    cat_stats = cat_stats.sort_values('购买会话', ascending=False)

    # 为加购→购买转化率添加 Wilson CI（影响最大的指标）
    ci_data = [_wilson_ci(r['购买会话'], r['加购会话'])
               for _, r in cat_stats.iterrows()]
    cat_stats['购买CI_low'] = [c[0] for c in ci_data]
    cat_stats['购买CI_high'] = [c[1] for c in ci_data]

    for _, row in cat_stats.iterrows():
        logger.info("  %s: %s 浏览 → 加购 %.2f%% → 购买 %.2f%% [95%% CI: %.1f-%.1f%%]",
                    row['category'], f"{int(row['浏览会话']):,}",
                    row['浏览→加购(%)'], row['加购→购买(%)'],
                    row['购买CI_low'], row['购买CI_high'])

    return cat_stats


def compute_duration_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """停留时长与转化率（行为分析常用阈值分桶）"""
    logger.info("--- 停留时长分析 ---")

    funnel_wide = funnel_wide.copy()
    funnel_wide['时长分桶'] = pd.cut(
        funnel_wide['total_duration_sec'],
        bins=DURATION_BINS, labels=DURATION_LABELS,
    )

    result = funnel_wide.groupby('时长分桶', observed=True).agg(
        会话数=('session_id', 'nunique'),
        购买会话数=('step_purchase', 'sum'),
    )
    result['转化率(%)'] = (result['购买会话数'] / result['会话数'] * 100).round(2)

    for b, row in result.iterrows():
        logger.info("  %s: %s 会话, 转化率 %.2f%%",
                    b, f"{int(row['会话数']):,}", row['转化率(%)'])
    return result


def compute_time_of_day_analysis(funnel_wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """时段分析 — 返回 (小时转化率, 星期几转化率)"""
    logger.info("--- 时段分析 ---")

    funnel_wide = funnel_wide.copy()
    hourly = funnel_wide.groupby('hour').agg(
        会话数=('session_id', 'nunique'),
        转化率=('step_purchase', 'mean'),
    )
    hourly['转化率'] = (hourly['转化率'] * 100).round(2)

    wd_map = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
    funnel_wide['星期'] = funnel_wide['weekday'].map(wd_map)
    dow_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dow = funnel_wide.groupby('星期').agg(
        会话数=('session_id', 'nunique'),
        转化率=('step_purchase', 'mean'),
    )
    dow['转化率'] = (dow['转化率'] * 100).round(2)
    dow = dow.reindex([d for d in dow_order if d in dow.index])

    logger.info("流量高峰: %sh, 转化率高峰: %sh",
                hourly['会话数'].idxmax(), hourly['转化率'].idxmax())
    logger.info("流量最大日: %s", dow['会话数'].idxmax())
    return hourly, dow


def compute_trend_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """月度转化率趋势分析（3 年）"""
    logger.info("--- 月度趋势分析 ---")

    monthly = funnel_wide.groupby(['year', 'month']).agg(
        会话数=('session_id', 'nunique'),
        购买会话数=('step_purchase', 'sum'),
        总时长中位数=('total_duration_sec', 'median'),
    ).reset_index()

    monthly['日期'] = monthly.apply(
        lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1
    )
    monthly['转化率(%)'] = (monthly['购买会话数'] / monthly['会话数'] * 100).round(2)
    monthly = monthly.sort_values(['year', 'month'])

    # 年度汇总
    years = sorted(funnel_wide['year'].unique())
    yearly_sessions = {}
    for y in years:
        y_data = funnel_wide[funnel_wide['year'] == y]
        rate = y_data['step_purchase'].mean() * 100
        yearly_sessions[y] = len(y_data)
        logger.info("  %d 年: 转化率 %.2f%% (%s 会话)", int(y), rate, f"{len(y_data):,}")

    # 会话量变化率检查 — 数据完整性警示
    for i, y in enumerate(years[1:], start=1):
        prev = yearly_sessions[years[i - 1]]
        curr = yearly_sessions[y]
        change_pct = (curr - prev) / prev * 100
        if abs(change_pct) > 30:
            logger.warning(
                "  %d 年会话量较 %d 年变化 %+.1f%% (%s → %s) — 数据完整性存疑, 趋势结论需谨慎",
                int(y), int(years[i - 1]), change_pct,
                f"{prev:,}", f"{curr:,}",
            )

    return monthly


def channel_device_cross_analysis(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """渠道 × 设备交叉转化率矩阵"""
    logger.info("--- 渠道×设备交叉分析 ---")

    cross = funnel_wide.groupby(['traffic_source', 'device_type']).agg(
        会话数=('session_id', 'nunique'),
        购买会话数=('step_purchase', 'sum'),
    )
    cross['转化率(%)'] = (cross['购买会话数'] / cross['会话数'] * 100).round(2)
    cross = cross.sort_values('会话数', ascending=False)

    worst = cross[cross['会话数'] >= 1000].nsmallest(3, '转化率(%)')
    for idx, row in worst.iterrows():
        logger.info("  最低: %s x %s = %.2f%% (%s 会话)",
                    idx[0], idx[1], row['转化率(%)'], f"{int(row['会话数']):,}")
    return cross


# ═══════════════════════════════════════════════════════════════
# 阶段 4: 流失根因诊断
# ═══════════════════════════════════════════════════════════════

def compute_churn_features(funnel_wide: pd.DataFrame) -> list[dict[str, str | float]]:
    """流失组 vs 转化组 Welch's t 检验 + Cohen's d — 总停留时长 & 事件数

    注: event_count 和 total_duration_sec 的部分差异反映了"完成更多漏斗步骤"
    的自然结果 (tautology), 在当前数据字段限制下无法进一步区分
    "互动驱动转化"和"转化带来互动"。建议在埋点层面增加搜索使用、评价查看、
    比价行为等独立事件以提升诊断可操作性。
    """
    logger.info("=" * 60)
    logger.info("10. 流失特征对比 (t检验 + Cohen's d)")
    logger.info("=" * 60)

    def cohens_d(a, b):
        na, nb = len(a), len(b)
        if na < 2 or nb < 2:
            return np.nan
        pooled = np.sqrt(((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2) / (na + nb - 2))
        return (a.mean() - b.mean()) / pooled if pooled > 0 else np.nan

    features = ['total_duration_sec', 'event_count']
    results = []
    n_tests = len(CHURN_STAGES) * len(features)  # 4 stages × 2 features = 8
    bonferroni_alpha = 0.05 / n_tests  # Bonferroni 校正 α = 0.00625
    logger.info("  Bonferroni 校正 α = %.5f (%d 次独立检验)", bonferroni_alpha, n_tests)

    for label, stage_col, next_col in CHURN_STAGES:
        lost = funnel_wide[(funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 0)]
        conv = funnel_wide[(funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 1)]

        for feat in features:
            t_stat, p_val = stats.ttest_ind(lost[feat], conv[feat], equal_var=False)
            d_val = cohens_d(lost[feat], conv[feat])
            sig_raw = '***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'
            sig_corrected = '*' if p_val < bonferroni_alpha else 'ns'

            results.append({
                '流失环节': label,
                '特征': feat,
                '流失组均值': round(lost[feat].mean(), 2),
                '转化组均值': round(conv[feat].mean(), 2),
                'p值': round(p_val, 6),
                '显著性(未校正)': sig_raw,
                '显著性(Bonferroni)': sig_corrected,
                'Cohens_d': round(d_val, 2),
                '效应量': '大' if abs(d_val) > 0.8 else '中' if abs(d_val) > 0.5 else '小',
            })
            logger.info("  %s | %s: 流失 %.2f vs 转化 %.2f (d=%.2f %s | Bonferroni: %s)",
                        label, feat, lost[feat].mean(), conv[feat].mean(), d_val, sig_raw, sig_corrected)

    return results


def compute_churn_matrix(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """渠道 × 流失环节交叉矩阵"""
    logger.info("--- 渠道×流失环节矩阵 ---")

    rows = []
    for ch in funnel_wide['traffic_source'].unique():
        ch_data = funnel_wide[funnel_wide['traffic_source'] == ch]
        for label, stage_col, next_col in CHURN_STAGES:
            reached = ch_data[stage_col].sum()
            churned = ch_data[(ch_data[stage_col] == 1) & (ch_data[next_col] == 0)]
            rows.append({
                '渠道': ch,
                '流失环节': label,
                '到达会话数': int(reached),
                '流失会话数': len(churned),
                '流失率(%)': round(len(churned) / reached * 100, 2) if reached > 0 else 0,
            })

    result = pd.DataFrame(rows)
    # 找出每个渠道的最高流失环节
    for ch in result['渠道'].unique():
        ch_rows = result[result['渠道'] == ch]
        worst = ch_rows.loc[ch_rows['流失率(%)'].idxmax()]
        logger.info("  %s 最高流失: %s (%.2f%%)", ch, worst['流失环节'], worst['流失率(%)'])

    return result


# ═══════════════════════════════════════════════════════════════
# 阶段 5: 损失量化与优先级
# ═══════════════════════════════════════════════════════════════

def _build_session_losses(funnel_wide, stage_pairs, stage_crs, aov):
    """预计算每个流失会话的损失金额 → {session_id: loss_amount}，供 bootstrap 快速重采样"""
    session_loss = {}
    cumulative_lost = set()
    for _, stage_col, next_col in stage_pairs:
        reached = set(
            funnel_wide[funnel_wide[stage_col] == 1]['session_id'].unique()
        ) - cumulative_lost
        continued = set(
            funnel_wide[funnel_wide[next_col] == 1]['session_id'].unique()
        ) - cumulative_lost
        lost_sessions = reached - continued
        cumulative_lost |= lost_sessions
        cr = stage_crs.get(stage_col, 0.0)
        for sid in lost_sessions:
            session_loss[sid] = cr * aov
    return session_loss


def compute_loss_amount(funnel_wide: pd.DataFrame,
                        transactions: pd.DataFrame | None = None) -> pd.DataFrame:
    """各环节损失金额量化 — 流失会话级联去重，已转化用户客单价驱动"""
    logger.info("=" * 60)
    logger.info("11. 损失金额量化")
    logger.info("=" * 60)

    # 使用单笔订单级别的客单价，而非客户累计值
    # total_revenue 为客户级 sum，需除以 total_transactions 得到 per-transaction AOV
    if transactions is not None and len(transactions) > 0:
        valid_txn = transactions[transactions['gross_revenue'].notna()]
        aov = valid_txn['gross_revenue'].mean() if len(valid_txn) > 0 else 0
        aov_source = 'transactions表单笔均值'
    else:
        purchased = funnel_wide[funnel_wide['step_purchase'] == 1]
        purchased_cust = purchased[
            ['customer_id', 'total_revenue', 'total_transactions']
        ].drop_duplicates('customer_id')
        purchased_cust = purchased_cust[purchased_cust['total_transactions'] > 0]
        aov = (
            purchased_cust['total_revenue'] / purchased_cust['total_transactions']
        ).mean() if len(purchased_cust) > 0 else 0
        aov_source = 'funnel_wide per-transaction估算'
    logger.info("单笔订单客单价: Y%.2f (来源: %s)", aov, aov_source)

    stage_pairs = [
        ('首页 → 列表页', 'step1_home', 'step2_plp'),
        ('列表页 → 详情页', 'step2_plp', 'step3_pdp'),
        ('详情页 → 购物车', 'step3_pdp', 'step4_cart'),
        ('购物车 → 结算页', 'step4_cart', 'step5_checkout'),
    ]

    # Per-stage expected conversion rate: among sessions reaching each stage,
    # what proportion eventually purchased? Avoids the implausible assumption
    # that 100% of lost sessions would convert.
    all_purchasers = set(funnel_wide[funnel_wide['step_purchase'] == 1]['session_id'].unique())
    stage_crs = {}
    for _, stage_col, _ in stage_pairs:
        stage_sessions = set(funnel_wide[funnel_wide[stage_col] == 1]['session_id'].unique())
        purchasers = stage_sessions & all_purchasers
        stage_crs[stage_col] = len(purchasers) / len(stage_sessions) if stage_sessions else 0.0

    session_loss_map = {}  # session_id → loss_amount, 用于 bootstrap
    losses = []
    cumulative_lost = set()

    for label, stage_col, next_col in stage_pairs:
        reached = set(
            funnel_wide[funnel_wide[stage_col] == 1]['session_id'].unique()
        ) - cumulative_lost
        continued = set(
            funnel_wide[funnel_wide[next_col] == 1]['session_id'].unique()
        ) - cumulative_lost
        lost_sessions = reached - continued
        cumulative_lost |= lost_sessions

        reached_count = len(reached)
        lost_count = len(lost_sessions)
        loss_rate = round(lost_count / reached_count * 100, 2) if reached_count > 0 else 0
        expected_cr = stage_crs[stage_col]
        loss_amount = lost_count * expected_cr * aov

        # 记录每个流失会话的损失（用于 bootstrap）
        per_session = expected_cr * aov
        for sid in lost_sessions:
            session_loss_map[sid] = per_session

        losses.append({
            '漏斗环节': label,
            '流失会话数': lost_count,
            '入环节会话数': reached_count,
            '环节流失率(%)': loss_rate,
            '预期转化率(%)': round(expected_cr * 100, 2),
            '客单价': round(aov, 2),
            '估算损失金额': round(loss_amount, 2),
        })

    loss_df = pd.DataFrame(losses)
    total_loss = loss_df['估算损失金额'].sum()
    total_lost = loss_df['流失会话数'].sum()

    for _, row in loss_df.iterrows():
        logger.info("  %s: 流失 %s (%.2f%%), 预期CR %.2f%%, 损失 Y%s",
                    row['漏斗环节'], f"{int(row['流失会话数']):,}",
                    row['环节流失率(%)'], row['预期转化率(%)'],
                    f"{row['估算损失金额']:,.0f}")

    logger.info("估算总损失: Y%s (流失会话合计: %s, 总会话: %s)",
                f"{total_loss:,.0f}", f"{int(total_lost):,}", f"{len(funnel_wide):,}")

    # 退款损失 — 使用 customer_id 去重避免重复计算
    refund_customers = funnel_wide[funnel_wide['has_refund'] == 1][['customer_id', 'total_revenue']].drop_duplicates('customer_id')
    refund_count = int(funnel_wide[funnel_wide['has_refund'] == 1]['customer_id'].nunique())
    refund_revenue = refund_customers['total_revenue'].sum()
    logger.info("退款损失: %s 笔退款客户, 涉及金额 Y%s", f"{refund_count:,}", f"{refund_revenue:,.0f}")

    # Bootstrap 95% CI — 逐次采样避免大矩阵 OOM
    rng = np.random.default_rng(42)
    all_sids = np.array(list(session_loss_map.keys()))
    loss_values = np.array([session_loss_map[s] for s in all_sids], dtype=np.float64)
    n_lost = len(all_sids)
    boot_means = np.empty(1000, dtype=np.float64)
    for i in range(1000):
        boot_means[i] = rng.choice(loss_values, size=n_lost, replace=True).mean()
    boot_total_losses = boot_means * n_lost
    ci_low, ci_high = np.percentile(boot_total_losses, [2.5, 97.5])
    logger.info("总损失 95%% Bootstrap CI: Y%s ~ Y%s (1000次重采样)",
                f"{ci_low:,.0f}", f"{ci_high:,.0f}")

    return loss_df


def compute_pie_priority(loss_df: pd.DataFrame, total_sessions: int | None = None) -> pd.DataFrame:
    """PIE 优先级矩阵

    Ease 评分依据（基于典型电商优化经验，非数据驱动，仅供参考）：
    - 首页→列表页 (7): 导航/推荐算法优化，后端改动为主，1-2 sprint
    - 列表页→详情页 (6): 筛选/排序/缩略图改进，涉及前端+索引优化
    - 详情页→购物车 (6): CTA 按钮/信任信号/库存显示，需 A/B 测试验证
    - 购物车→结算页 (8): 移除表单字段/自动填充/优惠码优化，改动面小见效快

    实际 Ease 取决于团队能力和系统架构，建议在真实项目中用工程估点替换。"""
    logger.info("=" * 60)
    logger.info("12. PIE 优先级计算")
    logger.info("=" * 60)

    total_loss = loss_df['估算损失金额'].sum()
    if total_sessions is None:
        total_sessions = loss_df['入环节会话数'].max()

    pie = loss_df.copy()
    pie['Potential'] = (pie['估算损失金额'] / total_loss * 10).clip(1, 10).round(1)
    pie['Importance'] = (pie['入环节会话数'] / total_sessions * 10).clip(1, 10).round(1)

    ease_map = {
        '首页 → 列表页': 7,
        '列表页 → 详情页': 6,
        '详情页 → 购物车': 6,
        '购物车 → 结算页': 8,
    }
    pie['Ease'] = pie['漏斗环节'].map(ease_map).fillna(5)
    # 敏感性：Ease ±1 时的 PIE 得分范围
    pie['PIE_Ease+1'] = (pie['Potential'] * pie['Importance'] * (pie['Ease'] + 1)).round(0)
    pie['PIE_Ease-1'] = (pie['Potential'] * pie['Importance'] * (pie['Ease'] - 1)).round(0)
    pie['PIE得分'] = (pie['Potential'] * pie['Importance'] * pie['Ease']).round(0)
    pie = pie.sort_values('PIE得分', ascending=False)

    for _, row in pie.iterrows():
        logger.info("  %s: PIE=%.0f (P=%.1f I=%.1f E=%.1f) [Ease±1→%.0f-%.0f]",
                    row['漏斗环节'], row['PIE得分'],
                    row['Potential'], row['Importance'], row['Ease'],
                    row['PIE_Ease-1'], row['PIE_Ease+1'])

    return pie


# ═══════════════════════════════════════════════════════════════
# 统计检验
# ═══════════════════════════════════════════════════════════════

def statistical_tests(funnel_wide: pd.DataFrame) -> dict[str, dict[str, float | str]]:
    """卡方独立性检验 × 4 维度 + Bonferroni 多重比较校正 (α=0.0125) + Cramér's V 效应量"""
    logger.info("=" * 60)
    logger.info("13. 统计检验")
    logger.info("=" * 60)

    def cramers_v(chi2: float, n: int, min_dim: int) -> float:
        """Cramér's V 效应量: <0.1弱, 0.1-0.3中, >0.3强"""
        if min_dim <= 1 or n == 0:
            return 0.0
        return float(np.sqrt(chi2 / (n * (min_dim - 1))))

    results = {}
    dims = ['traffic_source', 'device_type', 'loyalty_tier', 'country']
    n_tests = len(dims)
    n_total = len(funnel_wide)
    alpha_corrected = 0.05 / n_tests  # Bonferroni

    for dim in dims:
        ct = pd.crosstab(funnel_wide[dim], funnel_wide['step_purchase'])
        chi2, p_val, dof, _ = stats.chi2_contingency(ct)
        sig = 'significant' if p_val < alpha_corrected else 'not significant'
        v = cramers_v(chi2, n_total, min(ct.shape))
        strength = '强' if v > 0.3 else '中' if v > 0.1 else '弱'
        results[dim] = {
            'chi2': round(chi2, 2), 'p': round(p_val, 4), 'sig': sig,
            'bonferroni_alpha': round(alpha_corrected, 4),
            'cramers_v': round(v, 4), 'effect_strength': strength,
        }
        logger.info(
            "  %s: X²=%.2f, p=%.4f (%s after Bonferroni, α=%.4f), "
            "Cramér's V=%.4f (%s)",
            dim, chi2, p_val, sig, alpha_corrected, v, strength,
        )

    return results


def compute_trend_attribution(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """三年转化率下降归因 — 渠道结构变化 vs 渠道内质量变化

    使用 shift-share 分解:
    - 结构效应: 各渠道流量占比变化导致的转化率变化
    - 质量效应: 各渠道自身转化率变化导致的转化率变化
    """
    logger.info("--- 三年趋势归因分析 ---")

    years = sorted(funnel_wide['year'].unique())
    channels = funnel_wide['traffic_source'].unique()

    yearly = []
    for y in years:
        y_data = funnel_wide[funnel_wide['year'] == y]
        for ch in channels:
            ch_data = y_data[y_data['traffic_source'] == ch]
            yearly.append({
                'year': int(y), 'channel': ch,
                'sessions': len(ch_data),
                'purchases': int(ch_data['step_purchase'].sum()),
            })

    attr_df = pd.DataFrame(yearly)
    attr_df['cr'] = (attr_df['purchases'] / attr_df['sessions'] * 100).round(2)
    attr_df['share'] = attr_df.groupby('year')['sessions'].transform(
        lambda x: (x / x.sum() * 100).round(1)
    )

    base_year = years[0]
    base = attr_df[attr_df['year'] == base_year].set_index('channel')
    decompositions = []

    for y in years[1:]:
        curr = attr_df[attr_df['year'] == y].set_index('channel')

        base_cr = attr_df[attr_df['year'] == base_year].assign(
            weighted=lambda df: df['cr'] * df['sessions'] / df['sessions'].sum()
        )['weighted'].sum()
        curr_cr = attr_df[attr_df['year'] == y].assign(
            weighted=lambda df: df['cr'] * df['sessions'] / df['sessions'].sum()
        )['weighted'].sum()

        struct_effect = 0
        quality_effect = 0
        for ch in channels:
            if ch in base.index and ch in curr.index:
                base_share = base.loc[ch, 'share'] / 100
                curr_share = curr.loc[ch, 'share'] / 100
                base_ch_cr = base.loc[ch, 'cr'] / 100
                curr_ch_cr = curr.loc[ch, 'cr'] / 100
                struct_effect += base_ch_cr * (curr_share - base_share)
                quality_effect += base_share * (curr_ch_cr - base_ch_cr)

        decompositions.append({
            '对比年份': f'{int(base_year)}→{int(y)}',
            '基准年CR(%)': round(base_cr, 2),
            '对比年CR(%)': round(curr_cr, 2),
            'CR变化(pp)': round(curr_cr - base_cr, 2),
            '结构效应(pp)': round(struct_effect * 100, 2),
            '质量效应(pp)': round(quality_effect * 100, 2),
        })

        logger.info(
            "  %s: CR %.2f%% → %.2f%% (Δ%.1fpp), 结构 %.1fpp / 质量 %.1fpp",
            f'{int(base_year)}→{int(y)}', base_cr, curr_cr, curr_cr - base_cr,
            struct_effect * 100, quality_effect * 100,
        )

    result = pd.DataFrame(decompositions)

    for ch in channels:
        ch_years = attr_df[attr_df['channel'] == ch].sort_values('year')
        logger.info(
            "  %s: %s",
            ch,
            ' → '.join([
                f"{int(r['year'])}年 CR {r['cr']:.1f}% (份额 {r['share']:.1f}%)"
                for _, r in ch_years.iterrows()
            ]),
        )

    # 数据完整性警示
    yearly_totals = attr_df.groupby('year')['sessions'].sum()
    for i, y in enumerate(years[1:], start=1):
        prev = yearly_totals[years[i - 1]]
        curr = yearly_totals[y]
        change_pct = (curr - prev) / prev * 100
        if abs(change_pct) > 30:
            logger.warning(
                "  %d→%d 会话量变化 %+.1f%% (%s → %s) — "
                "数据完整性存疑, Shift-Share 归因作为方法演示, "
                "在数据完整性验证前不应作为确定性业务结论",
                int(years[i - 1]), int(y), change_pct,
                f"{prev:,}", f"{curr:,}",
            )

    return result


# ═══════════════════════════════════════════════════════════════
# 广告 ROAS 分析
# ═══════════════════════════════════════════════════════════════

def compute_campaign_roas(funnel_wide: pd.DataFrame,
                          campaigns: pd.DataFrame) -> pd.DataFrame:
    """广告活动 ROAS 分析"""
    logger.info("--- 广告活动转化分析 ---")

    camp_conv = funnel_wide[funnel_wide['campaign_id'].notna()].groupby('campaign_id').agg(
        会话数=('session_id', 'nunique'),
        购买会话数=('step_purchase', 'sum'),
    ).reset_index()
    # 客户级收入按 campaign_id 去重求和
    camp_revenue = funnel_wide[funnel_wide['campaign_id'].notna()].groupby('campaign_id').apply(
        lambda g: g[['customer_id', 'total_revenue']].drop_duplicates('customer_id')['total_revenue'].sum(),
        include_groups=False,
    ).reset_index(name='总收入')
    camp_conv['campaign_id'] = camp_conv['campaign_id'].astype(int)
    camp_conv['转化率(%)'] = (camp_conv['购买会话数'] / camp_conv['会话数'] * 100).round(2)

    # 合并客户级收入
    camp_revenue['campaign_id'] = camp_revenue['campaign_id'].astype(int)
    camp_conv = camp_conv.merge(camp_revenue, on='campaign_id', how='left')

    camp_conv = camp_conv.merge(campaigns, on='campaign_id', how='left')
    camp_conv = camp_conv.sort_values('购买会话数', ascending=False)

    top5 = camp_conv.head(5)
    for _, row in top5.iterrows():
        logger.info("  #%d %s/%s: %s 转化, %.2f%%, 预期提升 %.1f%%",
                    int(row['campaign_id']), row['channel'], row['objective'],
                    f"{int(row['购买会话数']):,}", row['转化率(%)'],
                    row['expected_uplift'] * 100)

    return camp_conv


# ═══════════════════════════════════════════════════════════════
# Cohort 留存分析
# ═══════════════════════════════════════════════════════════════

def compute_cohort_retention(funnel_wide: pd.DataFrame) -> pd.DataFrame:
    """按首次购买月份分组的留存 Cohort 分析

    以用户首次购买的月份为 cohort，追踪后续月份的回购行为。
    返回留存矩阵 (cohort_month × period_index)，值为留存率(%)。
    """
    logger.info("--- Cohort 留存分析 ---")

    fw = funnel_wide.copy()
    fw['session_date'] = pd.to_datetime(fw['session_start'])

    # 确定每个用户的首次购买月份
    purchased = fw[fw['step_purchase'] == 1]
    if len(purchased) == 0:
        logger.info("  无购买用户, 跳过留存分析")
        return pd.DataFrame()

    first_purchase = (
        purchased.groupby('customer_id')['session_date']
        .min()
        .reset_index()
    )
    first_purchase.columns = ['customer_id', 'first_purchase_date']
    first_purchase['cohort_month'] = first_purchase['first_purchase_date'].dt.to_period('M')

    # 所有购买行为关联首次购买月份
    purchases = purchased[['customer_id', 'session_date']].copy()
    purchases['purchase_month'] = purchases['session_date'].dt.to_period('M')
    purchases = purchases.merge(first_purchase[['customer_id', 'cohort_month']],
                                on='customer_id', how='inner')

    # cohort_index = 购买月份与首次购买月份的月差 (Period ordinal)
    purchases['cohort_index'] = (
        purchases['purchase_month'].apply(lambda x: x.ordinal)
        - purchases['cohort_month'].apply(lambda x: x.ordinal)
    )

    # 构建留存矩阵
    cohort_sizes = first_purchase.groupby('cohort_month')['customer_id'].nunique()
    retention_matrix = purchases.pivot_table(
        index='cohort_month',
        columns='cohort_index',
        values='customer_id',
        aggfunc='nunique',
    )

    # 转为留存率 — 缺失 cohort 或 size=0 时留存率留空而非静默放大
    for idx in retention_matrix.index:
        size = cohort_sizes.get(idx, 0)
        if size > 0:
            retention_matrix.loc[idx] = (
                retention_matrix.loc[idx] / size * 100
            ).round(1)
        else:
            logger.warning("  cohort %s size=0 或缺失，留存率留空", idx)

    retention_matrix = retention_matrix.sort_index()

    # 日志输出
    for cohort, row in retention_matrix.head(8).iterrows():
        m0 = int(row.get(0, 0))
        m1 = row.get(1, None)
        m3 = row.get(3, None)
        parts = [f"cohort={cohort}, size={m0}"]
        if m1 is not None:
            parts.append(f"M+1={m1:.1f}%")
        if m3 is not None:
            parts.append(f"M+3={m3:.1f}%")
        logger.info("  %s", ", ".join(parts))

    if len(retention_matrix) > 8:
        logger.info("  ... (%d cohorts total)", len(retention_matrix))

    return retention_matrix


# ═══════════════════════════════════════════════════════════════
# 基准快照 & 策略摘要 (阶段 6)
# ═══════════════════════════════════════════════════════════════

def save_baseline(funnel_wide: pd.DataFrame) -> dict[str, float | int | str]:
    """保存漏斗基准快照到 JSON

    双口径说明:
    - session_conversion_rate (整体会话转化率): 购买会话 / 全部会话
      分母=所有会话(含未浏览直接购买的异常场景)
    - view_to_purchase_rate (浏览到购买转化率): 购买会话 / 有过浏览行为的会话
      分母=仅包含至少有一次浏览行为的会话, 排除纯技术流量

    两个指标都正确, 只是分母不同, 适用于不同分析场景。
    """
    # total_revenue 为客户级数据，按 customer_id 去重求和
    cust_revenue = funnel_wide[['customer_id', 'total_revenue', 'has_refund']].drop_duplicates('customer_id')
    total_sessions = int(len(funnel_wide))
    purchase_sessions = int(funnel_wide['step_purchase'].sum())
    view_sessions = int(funnel_wide['step_view'].sum())

    snapshot = {
        'analysis_timestamp': datetime.now().isoformat(),
        'analysis_version': '2.0',
        'documentation': 'docs/04-results.md',
        'metrics': {
            'total_sessions': total_sessions,
            'purchase_sessions': purchase_sessions,
            'view_sessions': view_sessions,
            'session_conversion_rate_pct': round(purchase_sessions / total_sessions * 100, 2),
            'view_to_purchase_rate_pct': round(purchase_sessions / view_sessions * 100, 2) if view_sessions > 0 else 0,
            'total_revenue': round(float(cust_revenue['total_revenue'].sum()), 2),
            'refund_rate_pct': round(cust_revenue['has_refund'].mean() * 100, 2),
            'avg_session_duration_sec': round(float(funnel_wide['total_duration_sec'].mean()), 2),
        },
        'page_coverage': {col: int(funnel_wide[col].sum()) for col in PAGE_FUNNEL_COLS},
    }
    m = snapshot['metrics']
    logger.info("整体会话转化率 (Session CR): %.2f%% = 购买 %s / 全部 %s 会话",
                m['session_conversion_rate_pct'],
                f"{purchase_sessions:,}", f"{total_sessions:,}")
    logger.info("浏览到购买转化率 (View-to-Purchase CR): %.2f%% = 购买 %s / 浏览 %s 会话",
                m['view_to_purchase_rate_pct'],
                f"{purchase_sessions:,}", f"{view_sessions:,}")
    logger.info("注意: 两个转化率口径不同, 不可直接比较。")
    with open(BASELINE_JSON, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    logger.info("基准快照已保存: %s", BASELINE_JSON)
    return snapshot


def generate_strategy_brief(loss_df: pd.DataFrame,
                            funnel_wide: pd.DataFrame) -> list[str]:
    """基于分析结果自动生成策略摘要"""
    logger.info("=" * 60)
    logger.info("15. 策略摘要自动生成")
    logger.info("=" * 60)

    brief = []

    # 找到最高流失环节
    worst = loss_df.sort_values('环节流失率(%)', ascending=False).iloc[0]
    brief.append(f"P0 核心瓶颈: {worst['漏斗环节']} (流失率 {worst['环节流失率(%)']}%, 年损失 Y{worst['估算损失金额']:,.0f})")

    # 找到最低转化渠道
    ch = funnel_wide.groupby('traffic_source')['step_purchase'].mean() * 100
    worst_ch = ch.idxmin()
    brief.append(f"P1 渠道优化: {worst_ch} 转化率最低 ({ch[worst_ch]:.2f}%), 建议针对性优化该渠道落地页")

    # 找到最佳转化时段
    hourly_conv = funnel_wide.groupby('hour')['step_purchase'].mean() * 100
    best_hour = hourly_conv.idxmax()
    brief.append(f"P1 运营时机: 转化率高峰在 {best_hour}:00, 建议此时段加大投放和优惠触达")

    # 停留时长杠杆
    high_dur = funnel_wide[funnel_wide['total_duration_sec'] > 420]
    low_dur = funnel_wide[funnel_wide['total_duration_sec'] <= 60]
    brief.append(f"P2 停留时长杠杆: 深度参与转化率 {high_dur['step_purchase'].mean()*100:.1f}% vs 快速跳出 {low_dur['step_purchase'].mean()*100:.1f}%, 建议在 180s 触发优惠弹窗")

    # 退款
    refund_rate = funnel_wide['has_refund'].mean() * 100
    if refund_rate > 5:
        brief.append(f"P2 退款治理: 退款率 {refund_rate:.1f}%, 高于行业均值, 建议排查高退款品类")

    # 行业基准对标
    from python.config import CRO_BENCHMARKS
    session_cr = funnel_wide['step_purchase'].mean() * 100
    refund_rate = funnel_wide['has_refund'].mean() * 100
    logger.info("--- 行业基准对标 ---")
    benchmarks = [
        ('会话转化率', session_cr, CRO_BENCHMARKS['avg_session_cr'], CRO_BENCHMARKS['top_quartile_session_cr'], '%'),
        ('退款率', refund_rate, CRO_BENCHMARKS['avg_refund_rate'], None, '%'),
    ]
    for name, actual, avg, top, unit in benchmarks:
        status = '优于' if (name == '退款率' and actual <= avg) or (name != '退款率' and actual >= top) else '低于' if name != '退款率' else '高于'
        ref = f"行业平均 {avg}{unit}" + (f", 前25% {top}{unit}" if top else "")
        logger.info("  %s: %.2f%s (%s %s)", name, actual, unit, status, ref)

    for b in brief:
        logger.info("  %s", b)

    return brief


def what_if_simulation(loss_df: pd.DataFrame,
                       improvements: dict[str, float] | None = None) -> pd.DataFrame:
    """增量效果预估 — "如果 PDP→Cart 转化率提升 5pp，增量收入多少？"

    improvements: {'首页 → 列表页': 0.05, '详情页 → 购物车': 0.10, ...}
    默认演示最关键的三个环节。
    """
    logger.info("=" * 60)
    logger.info("What-If 增量效果模拟")
    logger.info("=" * 60)

    if improvements is None:
        improvements = {
            '详情页 → 购物车': 0.10,   # PDP→Cart +10pp
            '列表页 → 详情页': 0.05,   # PLP→PDP +5pp
            '购物车 → 结算页': 0.05,   # Cart→Checkout +5pp
        }

    results = []
    for label, uplift in improvements.items():
        row = loss_df[loss_df['漏斗环节'] == label]
        if row.empty:
            continue
        row = row.iloc[0]
        lost_sessions = row['流失会话数']
        expected_cr = row['预期转化率(%)'] / 100
        aov = row['客单价']
        # 提升后挽回：流失会话 × uplift × 预期转化率 × 客单价
        recovered_sessions = int(lost_sessions * uplift)
        recovered_revenue = recovered_sessions * expected_cr * aov
        results.append({
            '优化环节': label,
            '转化率提升': f'+{uplift*100:.0f}pp',
            '挽回会话数': recovered_sessions,
            '预期增量收入': round(recovered_revenue, 2),
            '当前损失': row['估算损失金额'],
        })
        logger.info("  %s +%dpp -> 挽回 %s 会话, 增量收入 Y%s",
                    label, int(uplift * 100), f"{recovered_sessions:,}",
                    f"{recovered_revenue:,.0f}")

    sim_df = pd.DataFrame(results)
    total_incremental = sim_df['预期增量收入'].sum()
    logger.info("合计预期增量收入: Y%s", f"{total_incremental:,.0f}")
    return sim_df
