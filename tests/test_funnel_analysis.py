"""漏斗分析模块 — 单元测试"""
import pandas as pd
import numpy as np
from python.funnel_analysis import (
    compute_funnel, compute_channel_analysis, compute_device_analysis,
    compute_loss_amount, compute_pie_priority,
)


def _make_wide_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 100
    data = {
        'SessionID': [f's{i}' for i in range(n)],
        'UserID': [f'u{i}' for i in range(n)],
        'DeviceType': np.random.choice(['Desktop', 'Mobile', 'Tablet'], n),
        'Country': np.random.choice(['USA', 'UK', 'France'], n),
        'ReferralSource': np.random.choice(['Direct', 'Email', 'Google', 'Social Media'], n),
        'step1_home': 1,
        'step2_product': np.random.choice([0, 1], n, p=[0.2, 0.8]),
        'step3_cart': np.random.choice([0, 1], n, p=[0.6, 0.4]),
        'step4_checkout': np.random.choice([0, 1], n, p=[0.3, 0.7]),
        'step5_confirm': np.random.choice([0, 1], n, p=[0.1, 0.9]),
    }
    df = pd.DataFrame(data)
    df.loc[df['step5_confirm'] == 1, 'step4_checkout'] = 1
    df.loc[df['step4_checkout'] == 1, 'step3_cart'] = 1
    df.loc[df['step3_cart'] == 1, 'step2_product'] = 1
    df['is_purchased'] = df['step5_confirm']
    return df


class TestComputeFunnel:
    def test_five_stages(self):
        wide = _make_wide_df()
        funnel_df = compute_funnel(wide)
        assert len(funnel_df) == 5

    def test_first_stage_100_pct(self):
        wide = _make_wide_df()
        funnel_df = compute_funnel(wide)
        assert funnel_df.iloc[0]['上一阶段转化率(%)'] == 100.0

    def test_monotonic_decrease(self):
        wide = _make_wide_df()
        funnel_df = compute_funnel(wide)
        counts = funnel_df['独立会话数'].values
        assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))


class TestChannelAnalysis:
    def test_all_channels_present(self):
        wide = _make_wide_df()
        result = compute_channel_analysis(wide)
        for ch in ['Google', 'Email', 'Direct', 'Social Media']:
            assert ch in result.index

    def test_conversion_rate_range(self):
        wide = _make_wide_df()
        result = compute_channel_analysis(wide)
        assert (result['整体转化率'] >= 0).all()
        assert (result['整体转化率'] <= 100).all()


class TestDeviceAnalysis:
    def test_all_devices(self):
        wide = _make_wide_df()
        result = compute_device_analysis(wide)
        for d in ['Desktop', 'Mobile', 'Tablet']:
            assert d in result.index


class TestLossAmount:
    def test_total_loss_nonnegative(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide, avg_cart_value=100)
        assert loss['估算损失金额'].sum() >= 0

    def test_loss_stages_order(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide, avg_cart_value=100)
        stages = loss['漏斗环节'].tolist()
        assert '浏览商品' in stages[0]
        assert '支付成功' in stages[-1]


class TestPiePriority:
    def test_pie_scores_positive(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide, avg_cart_value=100)
        pie = compute_pie_priority(loss)
        assert (pie['PIE得分'] > 0).all()

    def test_pie_output_columns(self):
        wide = _make_wide_df()
        loss = compute_loss_amount(wide, avg_cart_value=100)
        pie = compute_pie_priority(loss)
        for col in ['Potential', 'Importance', 'Ease', 'PIE得分']:
            assert col in pie.columns
