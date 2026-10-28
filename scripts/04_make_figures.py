from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
T=ROOT/'results'/'tables'; OUT=ROOT/'results'/'figures'/'01_dissertation_figures'; OUT.mkdir(parents=True,exist_ok=True)
panel=pd.read_csv(ROOT/'data'/'processed'/'master_panel_core_2014_2026.csv',parse_dates=['month'])
cum=pd.read_csv(T/'cumulative_effects_rq1_rq3.csv')
cat=pd.read_csv(T/'category_specific_rq1.csv')
rob=pd.read_csv(T/'robustness_cumulative_effects.csv')

def save_line(variable,title,ylabel,name,shade=True):
    plt.figure(figsize=(11,6))
    for c,g in panel.groupby('category'):
        plt.plot(g['month'],g[variable],label=c)
    if shade: plt.axvspan(pd.Timestamp('2020-01-01'),pd.Timestamp('2023-12-01'),alpha=.08)
    plt.xlabel('Month'); plt.ylabel(ylabel); plt.title(title); plt.legend(ncol=2,fontsize=8); plt.tight_layout(); plt.savefig(OUT/name,dpi=220); plt.close()

save_line('cpi_index_2015_100','UK food CPI by selected category, Jan 2014–Jul 2026','CPI index (2015=100)','figure_01_cpi_trends.png',False)
save_line('hhi','Import-supplier concentration by food category','HHI (0–1)','figure_02_hhi_trends.png')
save_line('unit_value_gbp_per_kg','Import unit value proxy by food category','Import unit value (£/kg)','figure_03_unit_value_trends.png')

x=panel.dropna(subset=['import_cost_change_pct','cpi_log_change_pct'])
plt.figure(figsize=(9,6))
for c,g in x.groupby('category'): plt.scatter(g['import_cost_change_pct'],g['cpi_log_change_pct'],s=16,alpha=.55,label=c)
plt.axhline(0,linewidth=.8); plt.axvline(0,linewidth=.8); plt.xlabel('Monthly import-unit-value change (%)'); plt.ylabel('Monthly CPI log change (%)'); plt.title('Import-cost movements and consumer food-price changes'); plt.legend(ncol=2,fontsize=8); plt.tight_layout(); plt.savefig(OUT/'figure_04_cost_cpi_scatter.png',dpi=220); plt.close()

c2=cat.sort_values('cum_pass_through'); y=np.arange(len(c2)); plt.figure(figsize=(9,5.5)); plt.errorbar(c2['cum_pass_through'],y,xerr=[c2['cum_pass_through']-c2['ci_low'],c2['ci_high']-c2['cum_pass_through']],fmt='o',capsize=4); plt.axvline(0,linewidth=.8); plt.yticks(y,c2['category']); plt.xlabel('Cumulative pass-through, lags 0–3'); plt.title('Category-specific cumulative import-cost pass-through'); plt.tight_layout(); plt.savefig(OUT/'figure_05_category_pass_through.png',dpi=220); plt.close()

order=['Low (25th pct)','Median','High (75th pct)']
r2=cum[(cum.model=='RQ2')&(cum.quantity=='Cumulative pass-through at HHI')].set_index('hhi_label').loc[order].reset_index(); xp=np.arange(3); plt.figure(figsize=(8,5.5)); plt.errorbar(xp,r2.estimate,yerr=[r2.estimate-r2.ci_low,r2.ci_high-r2.estimate],fmt='o',capsize=5); plt.axhline(0,linewidth=.8); plt.xticks(xp,order); plt.ylabel('Cumulative pass-through, lags 0–3'); plt.title('RQ2: Pass-through at low, median and high HHI'); plt.tight_layout(); plt.savefig(OUT/'figure_06_rq2_hhi_marginal.png',dpi=220); plt.close()

r3=cum[(cum.model=='RQ3')&(cum.quantity=='Cumulative pass-through at HHI by regime')]; plt.figure(figsize=(9,5.5));
for reg,g in r3.groupby('regime'):
    g=g.set_index('hhi_label').loc[order].reset_index(); plt.plot(order,g.estimate,marker='o',label=reg); plt.fill_between(np.arange(3),g.ci_low.to_numpy(),g.ci_high.to_numpy(),alpha=.08)
plt.axhline(0,linewidth=.8); plt.ylabel('Cumulative pass-through, lags 0–3'); plt.title('RQ3: Pass-through by HHI and disruption regime'); plt.legend(); plt.tight_layout(); plt.savefig(OUT/'figure_07_rq3_regime_hhi.png',dpi=220); plt.close()

rr=rob[rob.specification.str.startswith('RQ1')].sort_values('estimate'); y=np.arange(len(rr)); plt.figure(figsize=(10,6)); plt.errorbar(rr.estimate,y,xerr=[rr.estimate-rr.ci_low,rr.ci_high-rr.estimate],fmt='o',capsize=4); plt.axvline(0,linewidth=.8); plt.yticks(y,rr.specification); plt.xlabel('Cumulative pass-through'); plt.title('RQ1 robustness: cumulative estimates'); plt.tight_layout(); plt.savefig(OUT/'figure_08_rq1_robustness.png',dpi=220); plt.close()
print(f'Created {len(list(OUT.glob("figure_*.png")))} figures.')
