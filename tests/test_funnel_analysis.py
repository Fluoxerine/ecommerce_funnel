"""漏斗分析模块 — 单元测试"""
import pandas as pd
import numpy as np
from python.funnel_analysis import (
    compute_page_funnel, compute_event_funnel, compute_channel_analysis,
    compute_device_analysis, compute_loss_amount, compute_pie_priority,
    compute_duration_analysis, compute_churn_features,
    statistical_tests, compute_cohort_retention,
)


def _make_wide_df(n: int = 100) -> pd.DataFrame:
    """构造漏斗宽表测试数据，保证漏斗逻辑一致性"""
    np.random.seed(42)
    base_date = pd.Timestamp('2023-01-01')
    data = {
        'session_id': [f's{i}' for i in range(n)],
        'customer_id': [f'u{i}' for i in range(n)],
        'traffic_source': np.random.choice(
            ['Organic', 'Paid Search', 'Social', 'Email', 'Direct'], n),
        'device_type': np.random.choice(['desktop', 'mobile', 'tablet'], n),
        'experiment_group': np.random.choice(['Control', 'Variant_A', 'Variant_B'], n),
        'total_duration_sec': np.random.uniform(10, 600, n),
        'event_count': np.random.randint(2, 20, n),
        'hour': np.random.randint(0, 24, n),
        'weekday': np.random.randint(0, 7, n),
        'year': np.random.choice([2021, 2022, 2023], n),
        'month': np.random.randint(1, 13, n),
        'has_refund': np.random.choice([0, 1], n, p=[0.95, 0.05]),
        'total_revenue': np.random.uniform(50, 500, n),
        'total_transactions': np.random.randint(0, 5, n),
        'loyalty_tier': np.random.choice(['Bronze', 'Silver', 'Gold', 'Platinum'], n),
        'country': np.random.choice(['US', 'UK', 'IN', 'BR', 'CA'], n),
        'acquisition_channel': np.random.choice(
            ['Organic', 'Paid Search', 'Social', 'Email', 'Referral'], n),
        'session_start': [base_date + pd.Timedelta(days=i) for i in range(n)],
    }

    # 构建漏斗步骤 — 保证后一步依赖前一步
    data['step1_home'] = 1
    data['step2_plp'] = np.random.choice([0, 1], n, p=[0.3, 0.7])
    data['step3_pdp'] = np.where(
        data['step2_plp'] == 1,
        np.random.choice([0, 1], n, p=[0.2, 0.8]),
        0,
    )
    data['step4_cart'] = np.where(
        data['step3_pdp'] == 1,
        np.random.choice([0, 1], n, p=[0.5, 0.5]),
        0,
    )
    data['step5_checkout'] = np.where(
        data['step4_cart'] == 1,
        np.random.choice([0, 1], n, p=[0.1, 0.9]),
        0,
    )

    # 行为漏斗
    data['step_view'] = 1
    data['step_click'] = np.random.choice([0, 1], n, p=[0.4, 0.6])
    data['step_add_cart'] = np.random.choice([0, 1], n, p=[0.5, 0.5])
    data['step_purchase'] = data['step5_checkout']

    data['is_bounced'] = np.where(
        (data['step2_plp'] == 0) & (data['step_purchase'] == 0),
        np.random.choice([0, 1], n, p=[0.5, 0.5]),
        0,
    )
    data['is_purchased'] = data['step_purchase']

    return pd.DataFrame(data)


class TestComputePageFunnel:
    def test_five_stages(self):
        wide = _make_wide_df()
        funnel_df = compute_page_funnel(wide)
        assert len(funnel_df) == 5

    def test_first_stage_100_pct(self):
        wide = _make_wide_df()
        funnel_df = compute_page_funnel(wide)
        assert funnel_df.iloc[0]['上一阶段转化率(%)'] == 100.0

    def test_cross_reference_rate_not_exceed_100(self):
        """交叉引用转化率不应超过 100%"""
        wide = _make_wide_df()
        funnel_df = compute_page_funnel(wide)
        for _, row in funnel_df[1:].iterrows():
            assert row['上一阶段转化率(%)'] <= 100.0, \
                f"转化率 {row['上一阶段转化率(%)']}% > 100% at {row['漏斗阶段']}"


class TestComputeEventFunnel:
    def test_four_stages(self):
        wide = _make_wide_df()
        funnel_df = compute_event_funnel(wide)
        assert len(funnel_df) == 4

    def test_overall_rate_decreases(self):
        wide = _make_wide_df()
        funnel_df = compute_event_funnel(wide)
        rates = funnel_df['整体转化率(%)'].values
        for i in range(len(rates) - 1):
            assert rates[i] >= rates[i + 1], \
                f"整体转化率应递减: {rates[i]:.1f}% -> {rates[i+1]:.1f}%"


class TestChannelAnalysis:
    def test_all_channels_present(self):
        wide = _make_wide_df()
        result = compute_channel_analysis(wide)
        for ch in ['Organic', 'Paid Search', 'Social', 'Email', 'Direct']:
            assert ch in result.index

    def test_conversion_rate_range(self):
        wide = _make_wide_df()
        result = compute_channel_analysis(wide)
        assert (result['转化率(%)'] >= 0).all()
        assert (result['转化率(%)'] <= 100).all()

    def test_flow_share_sums_to_100(self):
        wide = _make_wide_df()
        result = compute_channel_analysis(wide)
        assert abs(result['流量占比(%)'].sum() - 100.0) < 1.0


class TestDeviceAnalysis:
    def test_all_devices_present(self):
        wide = _make_wide_df()
        result = compute_device_analysis(wide)
        for d in ['desktop', 'mobile', 'tablet']:
            assert d in result.index


class TestLossAmount:
    def test_total_loss_nonnegative(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide)
        assert loss['估算损失金额'].sum() >= 0

    def test_lost_sessions_not_exceed_total(self):
        """流失会话总数不应超过总会话数"""
        wide = _make_wide_df()
        loss = compute_loss_amount(wide)
        total_lost = loss['流失会话数'].sum()
        total_sessions = len(wide)
        assert total_lost <= total_sessions, \
            f"流失会话 {total_lost} > 总会话 {total_sessions}"

    def test_four_stages(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide)
        assert len(loss) == 4

    def test_loss_rate_range(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide)
        for rate in loss['环节流失率(%)']:
            assert 0 <= rate <= 100


class TestPiePriority:
    def test_pie_scores_positive(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide)
        pie = compute_pie_priority(loss)
        assert (pie['PIE得分'] > 0).all()

    def test_pie_output_columns(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide)
        pie = compute_pie_priority(loss)
        for col in ['Potential', 'Importance', 'Ease', 'PIE得分']:
            assert col in pie.columns


class TestDurationAnalysis:
    def test_bucket_labels(self):
        wide = _make_wide_df()
        result = compute_duration_analysis(wide)
        assert len(result) >= 1


class TestChurnFeatures:
    def test_results_not_empty(self):
        wide = _make_wide_df()
        results = compute_churn_features(wide)
        assert len(results) > 0

    def test_required_keys(self):
        wide = _make_wide_df()
        results = compute_churn_features(wide)
        required = ['流失环节', '特征', '流失组均值', '转化组均值', 'p值', '显著性', 'Cohens_d']
        for r in results:
            for key in required:
                assert key in r


class TestStatisticalTests:
    def test_all_dims_present(self):
        wide = _make_wide_df()
        results = statistical_tests(wide)
        for dim in ['traffic_source', 'device_type', 'loyalty_tier', 'country']:
            assert dim in results

    def test_cramers_v_in_output(self):
        wide = _make_wide_df()
        results = statistical_tests(wide)
        for dim, info in results.items():
            assert 'cramers_v' in info, f"Missing cramers_v for {dim}"
            assert 'effect_strength' in info, f"Missing effect_strength for {dim}"
            assert info['cramers_v'] >= 0, f"Cramér's V应>=0, got {info['cramers_v']}"

    def test_bonferroni_alpha(self):
        wide = _make_wide_df()
        results = statistical_tests(wide)
        for info in results.values():
            assert info['bonferroni_alpha'] == 0.0125


class TestCohortRetention:
    def test_returns_dataframe(self):
        wide = _make_wide_df(200)
        result = compute_cohort_retention(wide)
        assert isinstance(result, pd.DataFrame)

    def test_retention_rate_range(self):
        wide = _make_wide_df(200)
        result = compute_cohort_retention(wide)
        if not result.empty:
            flat = result.values.flatten()
            valid = flat[~np.isnan(flat)]
            assert (valid >= 0).all()
            assert (valid <= 100).all()

    def test_empty_no_purchases(self):
        wide = _make_wide_df(50)
        wide['step_purchase'] = 0
        result = compute_cohort_retention(wide)
        assert result.empty


class TestLossAmountWithTransactions:
    def test_uses_transactions_aov(self):
        """验证 compute_loss_amount 优先使用 transactions 表单笔 AOV"""
        wide = _make_wide_df(100)
        txn = pd.DataFrame({
            'transaction_id': range(50),
            'timestamp': pd.to_datetime(['2023-01-01'] * 50),
            'customer_id': [f'u{i}' for i in range(50)],
            'product_id': range(50),
            'quantity': [1] * 50,
            'discount_applied': [0.0] * 50,
            'gross_revenue': [100.0] * 50,
            'campaign_id': [1] * 50,
            'refund_flag': [0] * 50,
        })
        loss = compute_loss_amount(wide, txn)
        assert len(loss) == 4
        # AOV 应接近 100 (transactions表均值) 而非客户累计值均值
        assert 90 <= loss['客单价'].iloc[0] <= 110
