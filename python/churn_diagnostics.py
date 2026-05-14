"""流失诊断模块：流失 vs 转化用户特征对比 + 统计显著性检验"""
import pandas as pd
import numpy as np
from scipy import stats
from python.config import logger


def compute_churn_features(funnel_wide: pd.DataFrame,
                            df_cleaned: pd.DataFrame) -> dict:
    """各流失节点的用户特征对比分析"""
    logger.info("=" * 60)
    logger.info("16. 流失节点特征对比")
    logger.info("=" * 60)

    churn_nodes = [
        ('product_to_cart', 'step2_product', 'step3_cart'),
        ('cart_to_checkout', 'step3_cart', 'step4_checkout'),
        ('checkout_to_confirm', 'step4_checkout', 'step5_confirm'),
    ]

    session_features = _compute_session_features(df_cleaned)

    results = {}
    for node_name, stage_col, next_col in churn_nodes:
        lost_mask = (funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 0)
        converted_mask = (funnel_wide[stage_col] == 1) & (funnel_wide[next_col] == 1)

        lost_sessions = funnel_wide[lost_mask]['SessionID']
        converted_sessions = funnel_wide[converted_mask]['SessionID']

        if len(lost_sessions) < 2 or len(converted_sessions) < 2:
            logger.info("  %s: insufficient samples, skip", node_name)
            continue

        lost_features = session_features[session_features['SessionID'].isin(lost_sessions)]
        converted_features = session_features[session_features['SessionID'].isin(converted_sessions)]

        comparison = _compare_groups(lost_features, converted_features, node_name)
        if comparison is not None:
            results[node_name] = comparison

    return results


def _compute_session_features(df_cleaned: pd.DataFrame) -> pd.DataFrame:
    features = df_cleaned.groupby('SessionID').agg(
        总停留时长=('TimeOnPage_seconds', 'sum'),
        页面访问数=('PageType', 'count'),
        最大购物车商品数=('ItemsInCart', 'max'),
    ).reset_index()

    session_attribs = df_cleaned.groupby('SessionID').first()[
        ['DeviceType', 'Country', 'ReferralSource', 'hour', 'weekday']
    ].reset_index()

    return features.merge(session_attribs, on='SessionID')


def _compare_groups(lost: pd.DataFrame, converted: pd.DataFrame,
                    node_name: str) -> pd.DataFrame:
    """对比流失组和转化组的各项特征"""
    rows = []
    numeric_cols = ['总停留时长', '页面访问数', '最大购物车商品数']

    for col in numeric_cols:
        if col not in lost.columns:
            continue
        lost_vals = lost[col].dropna()
        conv_vals = converted[col].dropna()

        if len(lost_vals) < 2 or len(conv_vals) < 2:
            continue

        t_stat, p_val = stats.ttest_ind(lost_vals, conv_vals)
        d = _cohens_d(lost_vals.values, conv_vals.values)
        sig = '***' if p_val < 0.001 else ('**' if p_val < 0.01 else (
            '*' if p_val < 0.05 else 'ns'))
        rows.append({
            '特征': col,
            '流失组均值': round(float(lost_vals.mean()), 2),
            '转化组均值': round(float(conv_vals.mean()), 2),
            '差异方向': 'higher' if lost_vals.mean() > conv_vals.mean() else 'lower',
            "Cohen's d": round(abs(d), 2) if not np.isnan(d) else 0,
            '显著性': sig,
        })

    if not rows:
        return None

    result = pd.DataFrame(rows)
    logger.info("  [%s]", node_name)
    for _, row in result.iterrows():
        logger.info("    %s: lost %.2f vs converted %.2f (%s)",
                    row['特征'], row['流失组均值'], row['转化组均值'], row['显著性'])

    return result


def _cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return float('nan')
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled == 0:
        return 0.0
    return float((np.mean(group1) - np.mean(group2)) / pooled)


def compute_churn_by_dimension(funnel_wide: pd.DataFrame,
                                churn_node: str = 'product_to_cart') -> pd.DataFrame:
    """按维度拆解特定流失节点的流失率"""
    logger.info("=" * 60)
    logger.info("17. 分维度流失率拆解")
    logger.info("=" * 60)

    node_config = {
        'product_to_cart': ('step2_product', 'step3_cart', 'Browse->Cart'),
        'cart_to_checkout': ('step3_cart', 'step4_checkout', 'Cart->Checkout'),
        'checkout_to_confirm': ('step4_checkout', 'step5_confirm', 'Checkout->Confirm'),
    }

    stage_col, next_col, label = node_config[churn_node]
    logger.info("Analyzing node: %s", label)

    dimensions = ['ReferralSource', 'DeviceType', 'Country']
    all_results = []

    for dim in dimensions:
        result = funnel_wide.groupby(dim).agg(
            到达阶段=('SessionID', 'nunique'),
            流失数=(next_col, lambda x: int((funnel_wide.loc[x.index, stage_col] == 1).sum() - x.sum())),
        )
        result['流失率(%)'] = (result['流失数'] / result['到达阶段'] * 100).round(2)
        result = result.sort_values('流失率(%)', ascending=False)
        result['维度'] = dim
        result = result.reset_index().rename(columns={dim: '维度值'})
        all_results.append(result)

        logger.info("  By %s:", dim)
        for _, row in result.head(5).iterrows():
            logger.info("    %s: %.2f%% (lost %s / reached %s)",
                        row['维度值'], row['流失率(%)'],
                        f"{int(row['流失数']):,}", f"{int(row['到达阶段']):,}")

    return pd.concat(all_results, ignore_index=True)
