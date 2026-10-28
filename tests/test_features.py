import numpy as np
import pandas as pd
from food_price_pass_through.features import hhi_from_values, top_n_share, safe_log_change

def test_hhi_equal_four_suppliers():
    assert np.isclose(hhi_from_values(pd.Series([25,25,25,25])), 0.25)

def test_hhi_monopoly():
    assert np.isclose(hhi_from_values(pd.Series([100,0,0])), 1.0)

def test_hhi_zero_total_is_nan():
    assert np.isnan(hhi_from_values(pd.Series([0,0,0])))

def test_top3_share():
    assert np.isclose(top_n_share(pd.Series([40,30,20,10]),3),0.90)

def test_top3_zero_total_is_nan():
    assert np.isnan(top_n_share(pd.Series([0,0,0]),3))

def test_log_change():
    s=pd.Series([100.,110.]); out=safe_log_change(s)
    assert np.isnan(out.iloc[0]) and np.isclose(out.iloc[1],100*np.log(1.1))

def test_log_change_nonpositive_becomes_nan():
    out=safe_log_change(pd.Series([100.,0.,110.]))
    assert np.isnan(out.iloc[1]) and np.isnan(out.iloc[2])
