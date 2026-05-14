"""数据清洗模块 — 单元测试"""
import pandas as pd
import numpy as np
from python.data_cleaning import (
    basic_cleaning, funnel_specific_cleaning, build_funnel_wide
)


def _make_test_df() -> pd.DataFrame:
    data = {
        'SessionID': ['s1', 's1', 's2', 's2', 's2', 's3', 's4', 's4'],
        'UserID': ['u1', 'u1', 'u2', 'u2', 'u2', 'u3', 'u4', 'u4'],
        'Timestamp': pd.to_datetime([
            '2025-01-01 10:00:00', '2025-01-01 10:02:00',
            '2025-01-01 10:00:00', '2025-01-01 10:03:00', '2025-01-01 10:05:00',
            '2025-01-01 10:00:00', '2025-01-01 10:00:00', '2025-01-01 10:01:00',
        ]),
        'PageType': ['home', 'product_page', 'home', 'checkout', 'confirmation',
                     'home', 'home', 'home'],
        'DeviceType': ['Desktop', 'Desktop', 'Mobile', 'Mobile', 'Mobile',
                       'Tablet', 'Desktop', 'Desktop'],
        'Country': ['USA', 'USA', 'UK', 'UK', 'UK', 'France', 'India', 'India'],
        'ReferralSource': ['Google', 'Google', 'Email', 'Email', 'Email',
                           'Direct', 'Social Media', 'Social Media'],
        'TimeOnPage_seconds': [55, 120, 40, 90, 30, 3, 200, 100],
        'ItemsInCart': [0, 1, 0, 3, 0, 0, 0, 0],
        'Purchased': [0, 0, 1, 1, 1, 0, 0, 0],
    }
    return pd.DataFrame(data)


class TestBasicCleaning:
    def test_drop_duplicates(self):
        df = _make_test_df()
        df_dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        cleaned = basic_cleaning(df_dup)
        assert len(cleaned) == len(df)

    def test_null_core_columns(self):
        df = _make_test_df()
        df.loc[0, 'SessionID'] = None
        cleaned = basic_cleaning(df)
        assert 0 not in cleaned.index

    def test_fill_null_non_core(self):
        df = _make_test_df()
        df.loc[0, 'Country'] = np.nan
        cleaned = basic_cleaning(df)
        assert cleaned.loc[cleaned.index[0], 'Country'] == 'Unknown'

    def test_filter_future_time(self):
        df = _make_test_df()
        df.loc[0, 'Timestamp'] = pd.Timestamp('2099-01-01')
        cleaned = basic_cleaning(df)
        assert len(cleaned) < len(df)

    def test_filter_invalid_purchased(self):
        df = _make_test_df()
        df.loc[0, 'Purchased'] = 2
        cleaned = basic_cleaning(df)
        assert (cleaned['Purchased'].isin([0, 1])).all()

    def test_pageType_lowercased(self):
        df = _make_test_df()
        cleaned = basic_cleaning(df)
        assert (cleaned['PageType'] == cleaned['PageType'].str.lower()).all()


class TestFunnelSpecificCleaning:
    def test_sort_by_session_time(self):
        df = basic_cleaning(_make_test_df())
        cleaned = funnel_specific_cleaning(df)
        s1 = cleaned[cleaned['SessionID'] == 's1']
        assert s1['Timestamp'].is_monotonic_increasing

    def test_dedup_page_within_session(self):
        df = _make_test_df()
        cleaned = basic_cleaning(df)
        cleaned = funnel_specific_cleaning(cleaned)
        s4 = cleaned[cleaned['SessionID'] == 's4']
        assert len(s4) == 1

    def test_filter_short_sessions(self):
        df = _make_test_df()
        cleaned = basic_cleaning(df)
        cleaned = funnel_specific_cleaning(cleaned)
        assert 's3' not in cleaned['SessionID'].values

    def test_derived_time_features(self):
        df = _make_test_df()
        cleaned = basic_cleaning(df)
        cleaned = funnel_specific_cleaning(cleaned)
        assert 'hour' in cleaned.columns
        assert 'weekday' in cleaned.columns
        assert 'date' in cleaned.columns


class TestBuildFunnelWide:
    def test_all_sessions_present(self):
        df = basic_cleaning(_make_test_df())
        df = funnel_specific_cleaning(df)
        wide = build_funnel_wide(df)
        expected_sessions = df['SessionID'].nunique()
        assert len(wide) == expected_sessions

    def test_step_columns_binary(self):
        df = basic_cleaning(_make_test_df())
        df = funnel_specific_cleaning(df)
        wide = build_funnel_wide(df)
        for col in ['step1_home', 'step2_product', 'step3_cart',
                    'step4_checkout', 'step5_confirm']:
            assert wide[col].isin([0, 1]).all()

    def test_funnel_logic_consistency(self):
        df = basic_cleaning(_make_test_df())
        df = funnel_specific_cleaning(df)
        wide = build_funnel_wide(df)
        confirm_sessions = wide[wide['step5_confirm'] == 1]
        assert (confirm_sessions['step4_checkout'] == 1).all()

    def test_purchased_equals_step5(self):
        df = basic_cleaning(_make_test_df())
        df = funnel_specific_cleaning(df)
        wide = build_funnel_wide(df)
        assert (wide['is_purchased'] == wide['step5_confirm']).all()
