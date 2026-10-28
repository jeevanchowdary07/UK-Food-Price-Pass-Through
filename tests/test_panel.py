import pandas as pd
from food_price_pass_through.panel import merge_core_panel

def test_common_end_month():
    ons=pd.DataFrame({'category':['A','A','B','B'],'month':pd.to_datetime(['2026-06-01','2026-07-01','2026-06-01','2026-07-01']),'cpi_index_2015_100':[1,2,1,2],'cpi_log_change_pct':[0,1,0,1]})
    trade=pd.DataFrame({'category':['A','A','B'],'month':pd.to_datetime(['2026-06-01','2026-07-01','2026-06-01']),'MonthId':[202606,202607,202606],'hhi':[.2,.2,.3]})
    p=merge_core_panel(ons,trade,'2020-01-01','2023-12-01'); assert p.month.max()==pd.Timestamp('2026-06-01')

def test_disruption_flag_boundaries():
    ons=pd.DataFrame({'category':['A']*3,'month':pd.to_datetime(['2019-12-01','2020-01-01','2024-01-01']),'cpi_index_2015_100':[1,1,1]})
    trade=pd.DataFrame({'category':['A']*3,'month':ons.month,'MonthId':[201912,202001,202401],'hhi':[.2,.2,.2]})
    p=merge_core_panel(ons,trade,'2020-01-01','2023-12-01'); assert p.disruption_2020_23.tolist()==[0,1,0]
