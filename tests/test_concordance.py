from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'config/concordance/frozen_hs_coicop_concordance_v1.csv'

def load():
    return pd.read_csv(C,dtype=str)

def test_six_cpi_categories_present():
    assert load()['cpi_category'].nunique()==6

def test_butter_mapped_to_oils_and_fats():
    x=load(); rows=x[x['hs_code']=='0405']
    assert len(rows)==1 and rows.iloc[0]['cpi_category']=='Oils & fats'

def test_butter_not_mapped_to_dairy():
    x=load(); assert not ((x['cpi_category']=='Milk, cheese & eggs') & (x['hs_code']=='0405')).any()

def test_meat_hs02_present():
    x=load(); assert ((x['cpi_category']=='Meat') & (x['hs_code']=='02')).any()

def test_fish_hs03_present():
    x=load(); assert ((x['cpi_category']=='Fish') & (x['hs_code']=='03')).any()
