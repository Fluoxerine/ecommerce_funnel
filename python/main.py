"""电商漏斗全流程 CRO 分析 — 主入口 (六阶段闭环)

用法:
    python python/main.py              # 默认运行全部 6 个阶段
    python python/main.py --stage 3    # 仅运行第 3 阶段（漏斗建模）
    python python/main.py --help       # 显示帮助信息
"""
import argparse
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.config import OUTPUT_DIR, CHART_DIR, logger
from python.funnel_analysis import (
    compute_page_funnel, compute_event_funnel, compute_channel_funnels,
    compute_channel_analysis, compute_device_analysis, compute_country_analysis,
    compute_loyalty_analysis, compute_acquisition_analysis, compute_category_funnel,
    compute_duration_analysis, compute_time_of_day_analysis, compute_trend_analysis,
    channel_device_cross_analysis, compute_churn_features, compute_churn_matrix,
    compute_loss_amount, compute_pie_priority, statistical_tests,
    compute_campaign_roas,
    save_baseline, generate_strategy_brief,
    compute_strict_page_funnel, compute_deep_link_analysis,
    compute_trend_attribution, compute_new_vs_returning_funnel,
    compute_weekend_analysis, compute_cohort_retention,
    compute_visit_cohort_retention,
)
from python.visualization import (
    plot_cleaning_funnel, plot_page_funnel, plot_event_funnel,
    plot_channel_funnels, plot_loss_waterfall, plot_channel_device_heatmap,
    plot_dimension_comparison, plot_trend, plot_duration_conversion,
    plot_churn_by_channel, plot_pie_matrix, plot_category_funnel,
    plot_strict_vs_coverage, plot_deep_link_comparison,
    plot_new_vs_returning, plot_weekend_comparison, plot_cohort_heatmap,
    plot_visit_cohort_heatmap,
    plot_page_funnel_interactive, plot_event_funnel_interactive,
    plot_strict_page_funnel, plot_strict_page_funnel_interactive,
    set_chart_meta,
)
from python.data_loader import load_all_tables


def _safe_plot(plot_fn, name: str, *args, **kwargs) -> None:
    """安全调用单个绘图函数 — 单图失败不中断其他图"""
    try:
        plot_fn(*args, **kwargs)
    except Exception:
        logger.error("图表 %s 生成失败:\n%s", name, traceback.format_exc())


def _stage_runner(stage_name: str, stage_fn, *args, **kwargs):
    """通用阶段执行器 — 计时 + 异常处理 + 日志"""
    t = time.time()
    logger.info("=" * 60)
    logger.info("%s", stage_name)
    logger.info("=" * 60)
    try:
        result = stage_fn(*args, **kwargs)
        logger.info("%s 完成 (%.1fs)", stage_name.split(":")[0], time.time() - t)
        return result
    except Exception:
        logger.error("%s 失败:\n%s", stage_name, traceback.format_exc())
        raise


def _run_stage1_data_exploration(tables):
    from python.data_loader import load_all_tables, print_data_overview, validate_data_integrity, data_quality_report
    print_data_overview(tables)
    validate_data_integrity(tables)
    data_quality_report(tables)
    return tables


def _run_stage2_cleaning(tables):
    from python.data_cleaning import (
        basic_cleaning_events, build_session_attributes,
        build_funnel_wide, save_cleaned_data,
    )
    events_cleaned, cleaning_stats = basic_cleaning_events(tables['events'])
    session_attr = build_session_attributes(events_cleaned, tables['customers'])
    funnel_wide = build_funnel_wide(events_cleaned, session_attr, tables['transactions'])
    save_cleaned_data(events_cleaned, funnel_wide)
    return events_cleaned, funnel_wide, cleaning_stats


def _run_stage3_funnel_modeling(funnel_wide, events_cleaned, tables):
    from python.funnel_analysis import (
        compute_page_funnel, compute_event_funnel, compute_channel_funnels,
        compute_channel_analysis, compute_device_analysis, compute_country_analysis,
        compute_loyalty_analysis, compute_acquisition_analysis, compute_category_funnel,
        compute_duration_analysis, compute_time_of_day_analysis, compute_trend_analysis,
        channel_device_cross_analysis, compute_strict_page_funnel,
        compute_deep_link_analysis, compute_new_vs_returning_funnel,
        compute_weekend_analysis, compute_cohort_retention,
        compute_visit_cohort_retention, compute_trend_attribution,
    )

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
    cohort_retention = compute_cohort_retention(funnel_wide)
    visit_cohort_retention = compute_visit_cohort_retention(funnel_wide)

    return {
        'page_funnel': page_funnel, 'strict_funnel': strict_funnel,
        'event_funnel': event_funnel, 'channel_funnels': channel_funnels,
        'deep_link_summary': deep_link_summary, 'deep_link_ch_comparison': deep_link_ch_comparison,
        'nr_results': nr_results, 'weekend_df': weekend_df,
        'channel_df': channel_df, 'device_df': device_df, 'country_df': country_df,
        'loyalty_df': loyalty_df, 'acq_df': acq_df, 'cat_df': cat_df,
        'duration_df': duration_df, 'hourly': hourly, 'dow': dow,
        'monthly': monthly, 'trend_attribution': trend_attribution,
        'cross_df': cross_df, 'cohort_retention': cohort_retention,
        'visit_cohort_retention': visit_cohort_retention,
    }


def _run_stage4_churn_diagnostics(funnel_wide):
    from python.funnel_analysis import compute_churn_features, compute_churn_matrix
    churn_features = compute_churn_features(funnel_wide)
    churn_matrix = compute_churn_matrix(funnel_wide)
    return churn_features, churn_matrix


def _run_stage5_loss_and_priority(funnel_wide, tables):
    from python.funnel_analysis import (
        compute_loss_amount, compute_pie_priority, statistical_tests,
        compute_campaign_roas,
    )
    loss_df = compute_loss_amount(funnel_wide, tables['transactions'])
    pie_df = compute_pie_priority(loss_df, total_sessions=len(funnel_wide))
    stat_results = statistical_tests(funnel_wide)
    camp_roas = compute_campaign_roas(funnel_wide, tables['campaigns'])
    return loss_df, pie_df, stat_results, camp_roas


def _run_stage6_strategy_and_baseline(funnel_wide, loss_df):
    from python.funnel_analysis import save_baseline, generate_strategy_brief, what_if_simulation
    snapshot = save_baseline(funnel_wide)
    strategy_brief = generate_strategy_brief(loss_df, funnel_wide)
    sim_df = what_if_simulation(loss_df)
    return snapshot, strategy_brief, sim_df


def _run_visualization(funnel_wide, cleaning_stats, stage3, loss_df, pie_df,
                       churn_matrix, churn_features):
    """生成全部图表 — 单图失败不中断其他图"""
    set_chart_meta(len(funnel_wide))
    t_viz = time.time()
    logger.info("=" * 60)
    logger.info("生成可视化图表 (25 张: 22 静态 PNG + 3 交互式 HTML)")
    logger.info("=" * 60)

    plots = [
        ('00_cleaning_funnel', plot_cleaning_funnel, cleaning_stats),
        ('01_page_funnel', plot_page_funnel, stage3['page_funnel']),
        ('02_event_funnel', plot_event_funnel, stage3['event_funnel']),
        ('03_channel_funnels', plot_channel_funnels, stage3['channel_funnels']),
        ('04_loss_waterfall', plot_loss_waterfall, loss_df),
        ('05_channel_device_heatmap', plot_channel_device_heatmap, stage3['cross_df']),
        ('06_dimension_comparison', plot_dimension_comparison,
         stage3['channel_df'], stage3['device_df'], stage3['loyalty_df']),
        ('07_monthly_trend', plot_trend, stage3['monthly']),
        ('08_duration_conversion', plot_duration_conversion, stage3['duration_df']),
        ('09_churn_by_channel', plot_churn_by_channel, churn_matrix),
        ('10_pie_matrix', plot_pie_matrix, pie_df),
        ('11_category_funnel', plot_category_funnel, stage3['cat_df']),
        ('12_strict_vs_coverage', plot_strict_vs_coverage, stage3['strict_funnel']),
        ('13_deep_link_analysis', plot_deep_link_comparison,
         stage3['deep_link_summary'], stage3['deep_link_ch_comparison']),
        ('14_new_vs_returning', plot_new_vs_returning, stage3['nr_results']),
        ('15_weekend_comparison', plot_weekend_comparison, stage3['weekend_df']),
        ('16_cohort_heatmap', plot_cohort_heatmap, stage3['cohort_retention']),
        ('16b_visit_cohort_heatmap', plot_visit_cohort_heatmap, stage3['visit_cohort_retention']),
        # 严格路径漏斗
        ('01b_strict_page_funnel', plot_strict_page_funnel, stage3['strict_funnel']),
    ]
    for name, fn, *args in plots:
        _safe_plot(fn, name, *args)

    # 交互式漏斗图 (plotly HTML)
    interactive_plots = [
        ('01_page_funnel_interactive', plot_page_funnel_interactive, stage3['page_funnel']),
        ('01b_strict_page_funnel_interactive', plot_strict_page_funnel_interactive, stage3['strict_funnel']),
        ('02_event_funnel_interactive', plot_event_funnel_interactive, stage3['event_funnel']),
    ]
    for name, fn, *args in interactive_plots:
        _safe_plot(fn, name, *args)

    logger.info("可视化生成完成 (%.1fs)", time.time() - t_viz)


def main() -> None:
    """六阶段全流程分析入口"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    logger.info("=" * 60)
    logger.info("Ecommerce Funnel CRO Analysis — 六阶段全流程")
    logger.info("启动时间: %s", time.strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("=" * 60)

    from python.data_loader import load_all_tables
    tables = load_all_tables()
    _stage_runner("阶段 1/6: 数据探查与口径统一", _run_stage1_data_exploration, tables)

    events_cleaned, funnel_wide, cleaning_stats = _stage_runner(
        "阶段 2/6: 数据清洗 + 漏斗宽表构建", _run_stage2_cleaning, tables)
    stage3 = _stage_runner(
        "阶段 3/6: 漏斗建模 + 多维度诊断",
        _run_stage3_funnel_modeling, funnel_wide, events_cleaned, tables)
    churn_features, churn_matrix = _stage_runner(
        "阶段 4/6: 流失根因诊断", _run_stage4_churn_diagnostics, funnel_wide)
    loss_df, pie_df, stat_results, camp_roas = _stage_runner(
        "阶段 5/6: 损失量化 + PIE + ROAS",
        _run_stage5_loss_and_priority, funnel_wide, tables)
    snapshot, strategy_brief, sim_df = _stage_runner(
        "阶段 6/6: 策略摘要 + 基准快照 + What-If",
        _run_stage6_strategy_and_baseline, funnel_wide, loss_df)
    _run_visualization(funnel_wide, cleaning_stats, stage3, loss_df, pie_df,
                       churn_matrix, churn_features)

    total_elapsed = time.time() - t_start
    logger.info("=" * 60)
    logger.info("Analysis Complete — 总耗时 %.1fs (%.1fmin)", total_elapsed, total_elapsed / 60)
    logger.info("=" * 60)
    logger.info("Charts: %s", CHART_DIR)
    logger.info("Data:   %s", OUTPUT_DIR)
    logger.info("Next:   python python/import_to_mysql.py")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='电商漏斗全流程 CRO 分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='示例:\n  python main.py              # 运行全部 6 阶段\n  python main.py --skip-viz    # 跳过图表生成',
    )
    parser.add_argument('--skip-viz', action='store_true', help='跳过可视化图表生成')
    parser.add_argument('--output', type=str, default=None, help='指定输出目录（覆盖 config.py 默认值）')
    args = parser.parse_args()

    if args.output:
        from python.config import OUTPUT_DIR, CHART_DIR
        OUTPUT_DIR = Path(args.output)
        CHART_DIR = OUTPUT_DIR / 'charts'

    main()
