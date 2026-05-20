"""数据清洗模块 — 单元测试"""
import pandas as pd
import numpy as np
from python.data_cleaning import (
    basic_cleaning_events, build_session_attributes, build_funnel_wide,
)


def _make_events_df() -> pd.DataFrame:
    return pd.DataFrame({
        'event_id': [1, 2, 3, 4, 5, 6, 7, 8],
        'timestamp': pd.to_datetime([
            '2023-01-01 10:00:00', '2023-01-01 10:02:00',
            '2023-01-01 10:00:00', '2023-01-01 10:03:00',
            '2023-01-01 10:05:00', '2023-01-01 10:00:00',
            '2023-01-01 10:00:00', '2023-01-01 10:01:00',
        ]),
        'customer_id': [1, 1, 2, 2, 2, 3, 4, 4],
        'session_id': [101, 101, 102, 102, 102, 103, 104, 104],
        'event_type': ['view', 'add_to_cart', 'view', 'click', 'purchase',
                       'bounce', 'view', 'click'],
        'product_id': [10, 10, 20, 20, 20, None, 30, 30],
        'device_type': ['desktop', 'desktop', 'mobile', 'mobile', 'mobile',
                        'tablet', 'desktop', 'desktop'],
        'traffic_source': ['Organic', 'Organic', 'Email', 'Email', 'Email',
                           'Direct', 'Social', 'Social'],
        'campaign_id': [1, 1, 2, 2, 2, None, 3, 3],
        'page_category': ['PLP', 'PDP', 'Home', 'PDP', 'Checkout',
                          'Home', 'PLP', 'PDP'],
        'session_duration_sec': [55.0, 120.0, 40.0, 90.0, 30.0, 3.0, 200.0, 100.0],
        'experiment_group': ['Control', 'Control', 'Variant_B', 'Variant_B',
                             'Variant_B', 'Control', 'Variant_A', 'Variant_A'],
    })


def _make_customers_df() -> pd.DataFrame:
    return pd.DataFrame({
        'customer_id': [1, 2, 3, 4],
        'country': ['US', 'UK', 'FR', 'IN'],
        'age': [25, 34, 28, 42],
        'gender': ['Male', 'Female', 'Male', 'Female'],
        'loyalty_tier': ['Silver', 'Gold', 'Bronze', 'Platinum'],
        'acquisition_channel': ['Organic', 'Paid Search', 'Social', 'Email'],
        'signup_date': pd.to_datetime(['2022-06-01', '2022-03-15', '2023-01-10', '2021-11-20']),
    })


def _make_transactions_df() -> pd.DataFrame:
    return pd.DataFrame({
        'transaction_id': [1],
        'timestamp': pd.to_datetime(['2023-01-01 10:05:00']),
        'customer_id': [2],
        'product_id': [20],
        'quantity': [1],
        'discount_applied': [0.0],
        'gross_revenue': [99.0],
        'campaign_id': [2],
        'refund_flag': [0],
    })


class TestBasicCleaningEvents:
    def test_drop_duplicates(self):
        df = _make_events_df()
        df_dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        cleaned, stats = basic_cleaning_events(df_dup)
        assert len(cleaned) == len(df)
        assert '去重后' in stats

    def test_dropna_core_columns(self):
        df = _make_events_df()
        df.loc[0, 'session_id'] = np.nan
        cleaned, stats = basic_cleaning_events(df)
        assert 0 not in cleaned.index

    def test_filter_session_duration_too_high(self):
        df = _make_events_df()
        df.loc[0, 'session_duration_sec'] = 999999.0
        cleaned, stats = basic_cleaning_events(df)
        assert len(cleaned) < len(df)

    def test_filter_invalid_event_type(self):
        df = _make_events_df()
        df.loc[0, 'event_type'] = 'invalid_type'
        cleaned, stats = basic_cleaning_events(df)
        assert 'invalid_type' not in cleaned['event_type'].values

    def test_known_event_types_preserved(self):
        df = _make_events_df()
        cleaned, stats = basic_cleaning_events(df)
        for et in cleaned['event_type'].unique():
            assert et in ['view', 'click', 'add_to_cart', 'bounce', 'purchase']

    def test_cleaning_stats_keys(self):
        df = _make_events_df()
        _, stats = basic_cleaning_events(df)
        for key in ['原始数据', '去重后', '核心字段非空', '时长异常值过滤', '事件类型白名单']:
            assert key in stats, f"Missing key: {key}"


class TestBuildSessionAttributes:
    def test_output_shape(self):
        events, _ = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        assert len(attr) == events['session_id'].nunique()

    def test_derived_time_features(self):
        events, _ = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        for col in ['hour', 'weekday', 'date', 'year', 'month']:
            assert col in attr.columns

    def test_customer_attributes_merged(self):
        events, _ = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        for col in ['country', 'age', 'gender', 'loyalty_tier', 'acquisition_channel']:
            assert col in attr.columns


class TestBuildFunnelWide:
    def test_all_sessions_present(self):
        events, _ = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        txn = _make_transactions_df()
        wide = build_funnel_wide(events, attr, txn)
        assert len(wide) == events['session_id'].nunique()

    def test_step_columns_binary(self):
        events, _ = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        txn = pd.DataFrame(columns=['transaction_id', 'timestamp', 'customer_id',
                                     'product_id', 'quantity', 'discount_applied',
                                     'gross_revenue', 'campaign_id', 'refund_flag'])
        wide = build_funnel_wide(events, attr, txn)
        for col in ['step1_home', 'step2_plp', 'step3_pdp', 'step4_cart', 'step5_checkout']:
            assert wide[col].isin([0, 1]).all()

    def test_funnel_logic_purchase_has_checkout(self):
        events, _ = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        txn = _make_transactions_df()
        wide = build_funnel_wide(events, attr, txn)
        purchasers = wide[wide['step_purchase'] == 1]
        if len(purchasers) > 0:
            assert (purchasers['step5_checkout'] == 1).all(), \
                "All purchase sessions must have checkout"

    def test_is_bounced_column(self):
        events, _ = basic_cleaning_events(_make_events_df())
        customers = _make_customers_df()
        attr = build_session_attributes(events, customers)
        txn = _make_transactions_df()
        wide = build_funnel_wide(events, attr, txn)
        assert 'is_bounced' in wide.columns
        assert wide['is_bounced'].isin([0, 1]).all()
