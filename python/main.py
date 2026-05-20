"""电商漏斗全流程 CRO 分析 — 主入口 (六阶段闭环)"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.config import OUTPUT_DIR, CHART_DIR, logger
from python.data_loader import load_all_tables, print_data_overview, validate_data_integrity
from python.data_cleaning import (
    basic_cleaning_events, build_session_attributes,
    build_funnel_wide, save_cleaned_data,
)
from python.funnel_analysis import (
    compute_page_funnel, compute_event_funnel, compute_channel_funnels,
    compute_channel_analysis, compute_device_analysis, compute_country_analysis,
    compute_loyalty_analysis, compute_acquisition_analysis, compute_category_funnel,
    compute_duration_analysis, compute_time_of_day_analysis, compute_trend_analysis,
    channel_device_cross_analysis, compute_churn_features, compute_churn_matrix,
    compute_loss_amount, compute_pie_priority, statistical_tests,
    compute_ab_test_analysis, compute_campaign_roas,
    save_baseline, generate_strategy_brief,
    compute_strict_page_funnel, compute_deep_link_analysis,
    compute_trend_attribution, compute_new_vs_returning_funnel,
    compute_weekend_analysis, compute_cohort_retention,
)
from python.visualization import (
    plot_cleaning_funnel, plot_page_funnel, plot_event_funnel,
    plot_channel_funnels, plot_loss_waterfall, plot_channel_device_heatmap,
    plot_dimension_comparison, plot_trend, plot_duration_conversion,
    plot_churn_by_channel, plot_pie_matrix, plot_ab_test, plot_category_funnel,
    plot_strict_vs_coverage, plot_deep_link_comparison,
    plot_new_vs_returning, plot_weekend_comparison, plot_cohort_heatmap,
)


def _safe_plot(plot_fn, name: str, *args, **kwargs) -> None:
    """安全调用单个绘图函数 — 单图失败不中断其他图"""
    try:
        plot_fn(*args, **kwargs)
    except Exception:
        logger.error("图表 %s 生成失败:\n%s", name, traceback.format_exc())


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Ecommerce Funnel CRO Analysis — 六阶段全流程")
    logger.info("=" * 60)

    try:
        # ══════════════════════════════════════════════════════
        # 阶段 1: 数据探查与口径统一
        # ══════════════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("阶段 1/6: 数据探查与口径统一")
        logger.info("=" * 60)
        tables = load_all_tables()
        print_data_overview(tables)
        validate_data_integrity(tables)

        # ══════════════════════════════════════════════════════
        # 阶段 2: 数据清洗 + 漏斗宽表构建
        # ══════════════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("阶段 2/6: 数据清洗 + 漏斗宽表构建")
        logger.info("=" * 60)
        events_cleaned, cleaning_stats = basic_cleaning_events(tables['events'])
        session_attr = build_session_attributes(events_cleaned, tables['customers'])
        funnel_wide = build_funnel_wide(events_cleaned, session_attr, tables['transactions'])
        save_cleaned_data(events_cleaned, funnel_wide)

        # ══════════════════════════════════════════════════════
        # 阶段 3: 漏斗建模拆解 + 多维度诊断
        # ══════════════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("阶段 3/6: 漏斗建模 + 多维度诊断")
        logger.info("=" * 60)
        page_funnel = compute_page_funnel(funnel_wide)
        strict_funnel = compute_strict_page_funnel(funnel_wide, events_cleaned)
        event_funnel = compute_event_funnel(funnel_wide)
        channel_funnels = compute_channel_funnels(funnel_wide)

        deep_link_summary, deep_link_ch_comparison = compute_deep_link_analysis(funnel_wide)

        nr_results = compute_new_vs_returning_funnel(funnel_wide)
        weekend_df = compute_weekend_analysis(funnel_wide)

        channel_df = compute_channel_analysis(funnel_wide)
        device_df = compute_device_analysis(funnel_wide)
        country_df = compute_country_analysis(funnel_wide)
        loyalty_df = compute_loyalty_analysis(funnel_wide)
        acq_df = compute_acquisition_analysis(funnel_wide)
        cat_df = compute_category_funnel(funnel_wide, events_cleaned, tables['products'])
        duration_df = compute_duration_analysis(funnel_wide)

        hourly, dow = compute_time_of_day_analysis(funnel_wide)
        monthly = compute_trend_analysis(funnel_wide)
        trend_attribution = compute_trend_attribution(funnel_wide)
        cross_df = channel_device_cross_analysis(funnel_wide)

        # Cohort 留存分析
        cohort_retention = compute_cohort_retention(funnel_wide)

        # ══════════════════════════════════════════════════════
        # 阶段 4: 流失根因诊断
        # ══════════════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("阶段 4/6: 流失根因诊断")
        logger.info("=" * 60)
        churn_features = compute_churn_features(funnel_wide)
        churn_matrix = compute_churn_matrix(funnel_wide)

        # ══════════════════════════════════════════════════════
        # 阶段 5: 损失量化 + PIE + A/B + ROAS
        # ══════════════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("阶段 5/6: 损失量化 + PIE + A/B + ROAS")
        logger.info("=" * 60)
        loss_df = compute_loss_amount(funnel_wide, tables['transactions'])
        pie_df = compute_pie_priority(loss_df)
        stat_results = statistical_tests(funnel_wide)
        ab_groups = compute_ab_test_analysis(funnel_wide)
        camp_roas = compute_campaign_roas(funnel_wide, tables['campaigns'])

        # ══════════════════════════════════════════════════════
        # 阶段 6: 效果追踪框架 + 策略输出
        # ══════════════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("阶段 6/6: 策略摘要 + 基准快照")
        logger.info("=" * 60)
        snapshot = save_baseline(funnel_wide)
        strategy_brief = generate_strategy_brief(loss_df, funnel_wide)

        # ══════════════════════════════════════════════════════
        # 可视化（18 张图）
        # ══════════════════════════════════════════════════════
        logger.info("=" * 60)
        logger.info("生成可视化图表")
        logger.info("=" * 60)

        _safe_plot(plot_cleaning_funnel, '00_cleaning_funnel', cleaning_stats)
        _safe_plot(plot_page_funnel, '01_page_funnel', page_funnel)
        _safe_plot(plot_event_funnel, '02_event_funnel', event_funnel)
        _safe_plot(plot_channel_funnels, '03_channel_funnels', channel_funnels)
        _safe_plot(plot_loss_waterfall, '04_loss_waterfall', loss_df)
        _safe_plot(plot_channel_device_heatmap, '05_channel_device_heatmap', cross_df)
        _safe_plot(plot_dimension_comparison, '06_dimension_comparison',
                   channel_df, device_df, loyalty_df)
        _safe_plot(plot_trend, '07_monthly_trend', monthly)
        _safe_plot(plot_duration_conversion, '08_duration_conversion', duration_df)
        _safe_plot(plot_churn_by_channel, '09_churn_by_channel', churn_matrix)
        _safe_plot(plot_pie_matrix, '10_pie_matrix', pie_df)
        _safe_plot(plot_ab_test, '11_ab_test', ab_groups)
        _safe_plot(plot_category_funnel, '12_category_funnel', cat_df)
        _safe_plot(plot_strict_vs_coverage, '13_strict_vs_coverage', strict_funnel)
        _safe_plot(plot_deep_link_comparison, '14_deep_link_analysis',
                   deep_link_summary, deep_link_ch_comparison)
        _safe_plot(plot_new_vs_returning, '15_new_vs_returning', nr_results)
        _safe_plot(plot_weekend_comparison, '16_weekend_comparison', weekend_df)
        _safe_plot(plot_cohort_heatmap, '17_cohort_heatmap', cohort_retention)

    except Exception:
        logger.error("分析流程中断:\n%s", traceback.format_exc())
        raise

    # ══════════════════════════════════════════════════════
    logger.info("=" * 60)
    logger.info("Analysis Complete")
    logger.info("=" * 60)
    logger.info("Charts: %s", CHART_DIR)
    logger.info("Data:   %s", OUTPUT_DIR)
    logger.info("Next:   python python/import_to_mysql.py")


if __name__ == '__main__':
    main()
