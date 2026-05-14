"""电商漏斗 CRO 分析 — 主入口"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.config import OUTPUT_DIR, CHART_DIR, logger
from python.data_loader import load_raw_data, print_data_overview, validate_data_integrity
from python.data_cleaning import (
    basic_cleaning, funnel_specific_cleaning, build_funnel_wide, save_cleaned_data,
)
from python.funnel_analysis import (
    compute_funnel, compute_channel_analysis, compute_device_analysis,
    compute_duration_analysis, compute_cart_item_analysis,
    compute_loss_amount, compute_entry_path_analysis,
    compute_time_of_day_analysis, channel_device_cross_analysis,
    statistical_tests, compute_pie_priority,
)
from python.churn_diagnostics import (
    compute_churn_features, compute_churn_by_dimension,
)
from python.visualization import (
    plot_funnel_plotly, plot_funnel_static, plot_loss_waterfall,
    plot_channel_device_heatmap, plot_dimension_comparison,
    plot_time_analysis, plot_duration_conversion,
    plot_churn_by_channel, plot_path_sankey, plot_pie_matrix,
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Ecommerce Funnel CRO Analysis")
    logger.info("=" * 60)

    # [1] Load
    df = load_raw_data()
    print_data_overview(df)
    issues = validate_data_integrity(df)
    if issues:
        logger.warning("Data quality issues: %s", issues)

    # [2-3] Clean + funnel wide
    df_cleaned = basic_cleaning(df)
    df_cleaned = funnel_specific_cleaning(df_cleaned)
    funnel_wide = build_funnel_wide(df_cleaned)
    save_cleaned_data(df_cleaned, funnel_wide)

    # [4] Funnel overview
    funnel_df = compute_funnel(funnel_wide)

    # [5] Channel
    channel_df = compute_channel_analysis(funnel_wide)

    # [6] Device
    device_df = compute_device_analysis(funnel_wide)

    # [7] Duration
    duration_df = compute_duration_analysis(df_cleaned)

    # [8] Cart items
    cart_df = compute_cart_item_analysis(df_cleaned, funnel_wide)

    # [9] Loss amount
    loss_df = compute_loss_amount(funnel_wide)

    # [10] Entry path
    entry_df = compute_entry_path_analysis(df_cleaned)

    # [11] Time analysis
    hourly, dow = compute_time_of_day_analysis(df_cleaned)

    # [12] Cross analysis
    cross_df = channel_device_cross_analysis(funnel_wide)

    # [13] Statistical tests
    stat_results = statistical_tests(funnel_wide, df_cleaned)

    # [14] Churn diagnostics
    churn_features = compute_churn_features(funnel_wide, df_cleaned)
    churn_by_dim = compute_churn_by_dimension(funnel_wide)

    # [15] PIE
    pie_df = compute_pie_priority(loss_df)

    # [16] Visualization
    logger.info("=" * 60)
    logger.info("16. 生成可视化图表 (10 张)")
    logger.info("=" * 60)

    plot_funnel_plotly(funnel_df)
    plot_funnel_static(funnel_df)
    plot_loss_waterfall(loss_df)
    plot_channel_device_heatmap(cross_df)
    plot_dimension_comparison(channel_df, device_df)
    plot_time_analysis(hourly, dow)
    plot_duration_conversion(duration_df)
    plot_churn_by_channel(churn_by_dim)
    plot_path_sankey(df_cleaned)
    plot_pie_matrix(pie_df)

    # [17] Done
    logger.info("=" * 60)
    logger.info("Analysis Complete")
    logger.info("=" * 60)
    logger.info("Charts: %s", CHART_DIR)
    logger.info("Data: %s", OUTPUT_DIR)
    logger.info("Next: python python/import_to_mysql.py")
    logger.info("      then run sql/ scripts for SQL-side analysis")


if __name__ == '__main__':
    main()
