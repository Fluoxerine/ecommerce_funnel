"""集成测试 — 端到端完整流程验证"""
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from python.config import OUTPUT_DIR, CHART_DIR


class TestEndToEndPipeline:
    """完整分析流程的端到端测试"""

    def test_config_paths_exist(self):
        """验证配置路径存在或可创建"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        CHART_DIR.mkdir(parents=True, exist_ok=True)
        assert OUTPUT_DIR.exists()
        assert CHART_DIR.exists()

    def test_funnel_analysis_imports(self):
        """验证所有漏斗分析函数可正常导入"""
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
        )
        # 所有函数已成功导入，无 SyntaxError 或 ImportError
        assert callable(compute_page_funnel)

    def test_visualization_imports(self):
        """验证所有可视化函数可正常导入"""
        from python.visualization import (
            plot_cleaning_funnel, plot_page_funnel, plot_event_funnel,
            plot_channel_funnels, plot_loss_waterfall, plot_channel_device_heatmap,
            plot_dimension_comparison, plot_trend, plot_duration_conversion,
            plot_churn_by_channel, plot_pie_matrix, plot_category_funnel,
            plot_strict_vs_coverage, plot_deep_link_comparison,
            plot_new_vs_returning, plot_weekend_comparison, plot_cohort_heatmap,
        )
        assert callable(plot_page_funnel)

    def test_funnel_wide_logic(self):
        """测试漏斗宽表的核心逻辑（不依赖真实数据）"""
        from python.funnel_analysis import (
            compute_page_funnel, compute_event_funnel,
            compute_loss_amount, compute_pie_priority,
        )

        # 构造最小测试数据（包含所有必要列）
        np.random.seed(42)
        n = 100
        wide = pd.DataFrame({
            'session_id': [f's{i}' for i in range(n)],
            'customer_id': [f'u{i}' for i in range(n)],
            'traffic_source': np.random.choice(['Organic', 'Paid Search'], n),
            'device_type': np.random.choice(['desktop', 'mobile'], n),
            'experiment_group': ['Control'] * n,
            'campaign_id': [1] * n,
            'total_duration_sec': np.random.uniform(10, 600, n),
            'event_count': np.random.randint(2, 20, n),
            'hour': np.random.randint(0, 24, n),
            'weekday': np.random.randint(0, 7, n),
            'year': [2023] * n,
            'month': np.random.randint(1, 13, n),
            'has_refund': np.zeros(n),
            'total_revenue': np.random.uniform(50, 500, n),
            'total_transactions': np.random.randint(0, 3, n),
            'loyalty_tier': np.random.choice(['Bronze', 'Silver'], n),
            'country': np.random.choice(['US', 'UK'], n),
            'acquisition_channel': np.random.choice(['Organic', 'Paid Search'], n),
            'session_start': pd.Timestamp('2023-01-01'),
            'session_end': pd.Timestamp('2023-01-01'),
            # 页面漏斗步骤
            'step1_home': np.ones(n, dtype=int),
            'step2_plp': np.random.choice([0, 1], n, p=[0.3, 0.7]),
            'step3_pdp': np.where(
                np.random.choice([0, 1], n, p=[0.2, 0.8]) == 1,
                np.random.choice([0, 1], n, p=[0.2, 0.8]),
                0,
            ),
            'step4_cart': np.zeros(n, dtype=int),
            'step5_checkout': np.zeros(n, dtype=int),
            # 行为漏斗步骤
            'step_view': np.ones(n, dtype=int),
            'step_click': np.random.choice([0, 1], n, p=[0.4, 0.6]),
            'step_add_cart': np.random.choice([0, 1], n, p=[0.5, 0.5]),
            'step_purchase': np.zeros(n, dtype=int),
            # 其他
            'is_bounced': np.zeros(n, dtype=int),
            'is_purchased': np.zeros(n, dtype=int),
        })

        # 构造一些有购买的会话，确保 AOV 计算有效
        purchase_mask = np.zeros(n, dtype=int)
        purchase_mask[:10] = 1  # 前 10 个会话有购买

        wide['step_purchase'] = purchase_mask
        wide['step5_checkout'] = purchase_mask
        wide['is_purchased'] = purchase_mask
        wide['total_transactions'] = np.where(purchase_mask == 1, 1, 0)

        # 验证漏斗计算
        page_funnel = compute_page_funnel(wide)
        assert len(page_funnel) == 5
        assert page_funnel.iloc[0]['到达会话数'] == 100  # step1_home all 1
        assert page_funnel.iloc[0]['交叉到达率(%)'] == 100.0  # first stage always 100

        event_funnel = compute_event_funnel(wide)
        assert len(event_funnel) == 4
        assert event_funnel.iloc[0]['会话数'] == 100  # step_view all 1

        loss = compute_loss_amount(wide)
        assert len(loss) == 4
        assert loss['估算损失金额'].sum() >= 0
        assert '预期转化率(%)' in loss.columns

        pie = compute_pie_priority(loss)
        assert pie['PIE得分'].notna().all()
        assert (pie['PIE得分'] > 0).all()
        assert 'PIE_Ease-1' in pie.columns  # sensitivity range
        assert 'PIE_Ease+1' in pie.columns

    def test_safe_plot_error_handling(self):
        """测试 _safe_plot 的异常保护机制"""
        from python.visualization import plot_page_funnel

        # 构造错误数据（缺少列）触发异常
        bad_df = pd.DataFrame({'wrong_col': []})

        # 调用 _safe_plot 处理异常，验证不抛出
        from python.main import _safe_plot
        # 不应抛出异常，只记录错误
        _safe_plot(plot_page_funnel, 'test_error', bad_df)  # 异常被捕获

    def test_stage_runner_error_propagation(self):
        """测试 _stage_runner 异常处理"""
        from python.main import _stage_runner

        def fail_fn():
            raise ValueError("Test error")

        # 验证异常被正确抛出（不被吞掉）
        try:
            _stage_runner("Test Stage", fail_fn)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert str(e) == "Test error"

    def test_empty_dataframe_handling(self):
        """测试空 DataFrame 的边界情况处理"""
        from python.funnel_analysis import compute_channel_analysis, compute_device_analysis

        empty_df = pd.DataFrame({
            'session_id': [],
            'customer_id': [],
            'traffic_source': [],
            'device_type': [],
            'step_purchase': [],
            'step_view': [],
            'step1_home': [],
            'step2_plp': [],
            'step3_pdp': [],
            'step4_cart': [],
            'step5_checkout': [],
        })

        # 空数据应返回空结果，不崩溃
        result = compute_channel_analysis(empty_df)
        assert result.empty or len(result) == 0

    def test_cohort_empty_data(self):
        """测试 Cohort 分析对空数据的处理"""
        from python.funnel_analysis import compute_cohort_retention

        empty_df = pd.DataFrame({
            'session_id': [],
            'customer_id': [],
            'step_purchase': [],
            'session_start': pd.to_datetime([]),
        })

        result = compute_cohort_retention(empty_df)
        assert isinstance(result, pd.DataFrame)

    def test_loss_amount_no_transactions(self):
        """测试无 transactions 数据时的损失计算"""
        from python.funnel_analysis import compute_loss_amount

        np.random.seed(42)
        n = 50
        wide = pd.DataFrame({
            'session_id': [f's{i}' for i in range(n)],
            'customer_id': [f'u{i}' for i in range(n)],
            'traffic_source': ['Organic'] * n,
            'device_type': ['desktop'] * n,
            'experiment_group': ['Control'] * n,
            'campaign_id': [1] * n,
            'total_duration_sec': np.random.uniform(10, 600, n),
            'event_count': np.random.randint(2, 20, n),
            'hour': np.random.randint(0, 24, n),
            'weekday': np.random.randint(0, 7, n),
            'year': [2023] * n,
            'month': [1] * n,
            'has_refund': np.zeros(n),
            'total_revenue': np.random.uniform(50, 500, n),
            'total_transactions': np.random.randint(0, 3, n),
            'loyalty_tier': ['Bronze'] * n,
            'country': ['US'] * n,
            'acquisition_channel': ['Organic'] * n,
            'session_start': pd.Timestamp('2023-01-01'),
            'session_end': pd.Timestamp('2023-01-01'),
            'step1_home': np.ones(n, dtype=int),
            'step2_plp': np.random.choice([0, 1], n, p=[0.3, 0.7]),
            'step3_pdp': np.zeros(n, dtype=int),
            'step4_cart': np.zeros(n, dtype=int),
            'step5_checkout': np.zeros(n, dtype=int),
            'step_view': np.ones(n, dtype=int),
            'step_click': np.zeros(n, dtype=int),
            'step_add_cart': np.zeros(n, dtype=int),
            'step_purchase': np.zeros(n, dtype=int),
            'is_bounced': np.zeros(n, dtype=int),
            'is_purchased': np.zeros(n, dtype=int),
        })

        # 无 transactions 时应使用 funnel_wide 内的 per-transaction AOV 估算
        loss = compute_loss_amount(wide, transactions=None)
        assert len(loss) == 4
        assert loss['估算损失金额'].sum() >= 0