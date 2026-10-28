from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def panel(): return pd.read_csv(ROOT/'data/processed/master_panel_core_2014_2026.csv',parse_dates=['month'])
def main(): return pd.read_csv(ROOT/'data/processed/analysis_sample_main_lag03.csv',parse_dates=['month'])

def test_master_panel_rows(): assert len(panel())==906
def test_six_categories(): assert panel().category.nunique()==6
def test_151_months_per_category(): assert (panel().groupby('category').size()==151).all()
def test_master_panel_is_unique(): assert not panel().duplicated(['category','month']).any()
def test_master_panel_period():
    p=panel(); assert p.month.min()==pd.Timestamp('2014-01-01') and p.month.max()==pd.Timestamp('2026-07-01')
def test_no_missing_cpi(): assert panel()['cpi_index_2015_100'].notna().all()
def test_no_missing_unit_value(): assert panel()['unit_value_gbp_per_kg'].notna().all()
def test_hhi_bounds(): assert panel()['hhi'].between(0,1).all()
def test_top3_bounds(): assert panel()['top3_share'].between(0,1).all()
def test_supplier_count_positive(): assert (panel()['supplier_count']>0).all()
def test_main_sample_rows(): assert len(main())==882
def test_main_lags_complete(): assert main()[[f'cost_l{k}' for k in range(4)]].notna().all().all()
