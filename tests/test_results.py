from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parents[1]; T=ROOT/'results/tables'

def cumulative(): return pd.read_csv(T/'cumulative_effects_rq1_rq3.csv')
def test_rq_models_present(): assert {'RQ1','RQ2','RQ3'}.issubset(set(cumulative().model))
def test_rq1_cumulative_matches_reported():
    r=cumulative(); x=r[r.model=='RQ1'].iloc[0]; assert np.isclose(x.estimate,0.125339,atol=1e-6)
def test_rq1_ci_above_zero():
    r=cumulative(); x=r[r.model=='RQ1'].iloc[0]; assert x.ci_low>0 and x.ci_high>0
def test_rq2_moderation_not_significant():
    r=cumulative(); x=r[(r.model=='RQ2')&(r.quantity=='Cumulative HHI moderation slope')].iloc[0]; assert x.p_value>0.05
def test_rq3_disruption_difference_significant():
    r=cumulative(); x=r[(r.model=='RQ3')&r.quantity.str.startswith('Disruption minus stable')].iloc[0]; assert x.estimate>0 and x.p_value<0.05
def test_rq3_hhi_specific_effect_not_significant():
    r=cumulative(); x=r[(r.model=='RQ3')&(r.quantity=='Incremental HHI moderation during disruption')].iloc[0]; assert x.p_value>0.05
def test_all_primary_rq1_robustness_positive():
    r=pd.read_csv(T/'robustness_cumulative_effects.csv'); r=r[r.specification.str.startswith('RQ1')]; assert (r.estimate>0).all() and (r.ci_low>0).all()
def test_qa_all_pass():
    q=pd.read_csv(T/'qa_gate_final.csv'); assert len(q)==6 and (q.qa_gate=='PASS').all()
def test_eight_final_figures_exist(): assert len(list((ROOT/'results/figures/01_dissertation_figures').glob('figure_*.png')))==8
