from pathlib import Path
import json, warnings, math
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import norm
from statsmodels.stats.diagnostic import het_breuschpagan, acorr_ljungbox
from statsmodels.tsa.stattools import adfuller

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data' / 'interim' / 'hmrc_monthly_api_core'
OUT = ROOT / 'results' / 'tables'
OUT.mkdir(parents=True, exist_ok=True)
ONS_FILE = ROOT / 'data' / 'raw' / 'ons' / 'ONS_MM23_selected_food_CPI_2014_Aug2026.csv'

JSON_FILES = {
    'Meat': 'meat_core_monthly.json',
    'Fish': 'fish_core_monthly.json',
    'Milk, cheese & eggs': 'milk_cheese_eggs_core_monthly.json',
    'Oils & fats': 'oils_fats_core_monthly.json',
    'Fruit': 'fruit_core_monthly.json',
    'Vegetables': 'vegetables_core_monthly.json',
}
HMRC_COLS = ['MonthId','import_value_gbp','net_mass_kg','hhi','top3_share','supplier_count','unit_value_gbp_per_kg']

# ---------------------------
# Build analytical HMRC panel
# ---------------------------
frames = []
for category, filename in JSON_FILES.items():
    arr = json.load(open(BASE / filename, encoding='utf-8'))
    if len(arr) != 151:
        raise ValueError(f'{category}: expected 151 monthly rows, got {len(arr)}')
    d = pd.DataFrame(arr, columns=HMRC_COLS)
    d['category'] = category
    d['month'] = pd.to_datetime(d['MonthId'].astype(str), format='%Y%m')
    frames.append(d)

hmrc = pd.concat(frames, ignore_index=True).sort_values(['category','month']).reset_index(drop=True)
hmrc['hhi_10000'] = hmrc['hhi'] * 10000
hmrc['import_cost_change_pct'] = hmrc.groupby('category')['unit_value_gbp_per_kg'].transform(lambda s: 100*np.log(s/s.shift(1)))
hmrc['import_value_change_pct'] = hmrc.groupby('category')['import_value_gbp'].transform(lambda s: 100*np.log(s/s.shift(1)))
hmrc['mass_change_pct'] = hmrc.groupby('category')['net_mass_kg'].transform(lambda s: 100*np.log(s/s.shift(1)))

# ---------------------------
# ONS outcome series
# ---------------------------
ons = pd.read_csv(ONS_FILE, parse_dates=['month'])
ons = ons[ons['month'] <= pd.Timestamp('2026-07-01')].copy()
ons = ons.sort_values(['category','month'])
ons['cpi_log_change_pct'] = ons.groupby('category')['cpi_index_2015_100'].transform(lambda s: 100*np.log(s/s.shift(1)))
ons['cpi_yoy_log_pct'] = ons.groupby('category')['cpi_index_2015_100'].transform(lambda s: 100*np.log(s/s.shift(12)))

panel = hmrc.merge(ons, on=['category','month'], how='inner', validate='one_to_one').sort_values(['category','month']).reset_index(drop=True)
if len(panel) != 906 or panel['category'].nunique() != 6:
    raise ValueError(f'Unexpected merged panel shape: {panel.shape}, categories={panel.category.nunique()}')

panel['calendar_month'] = panel['month'].dt.month
panel['year'] = panel['month'].dt.year
panel['time_id'] = ((panel['month'].dt.year - panel['month'].dt.year.min())*12 + panel['month'].dt.month - 1).astype(int)
panel['trend'] = panel['time_id']
panel['disruption_2020_23'] = ((panel['month'] >= pd.Timestamp('2020-01-01')) & (panel['month'] <= pd.Timestamp('2023-12-01'))).astype(int)
panel['post_may2016'] = (panel['month'] >= pd.Timestamp('2016-05-01')).astype(int)
panel['post_jan2022'] = (panel['month'] >= pd.Timestamp('2022-01-01')).astype(int)
panel['ons_2026_flag'] = ((panel['month'] >= pd.Timestamp('2026-02-01')) & (panel['month'] <= pd.Timestamp('2026-07-01'))).astype(int)
panel['month_str'] = panel['month'].dt.strftime('%Y-%m')

for k in range(7):
    panel[f'cost_l{k}'] = panel.groupby('category')['import_cost_change_pct'].shift(k)
panel['hhi_l1'] = panel.groupby('category')['hhi'].shift(1)
panel['top3_l1'] = panel.groupby('category')['top3_share'].shift(1)

# Pre-2020 average HHI by category as a predetermined structural-concentration robustness moderator.
pre_hhi = panel.loc[panel['month'] < pd.Timestamp('2020-01-01')].groupby('category')['hhi'].mean().rename('pre2020_hhi')
panel = panel.merge(pre_hhi, on='category', how='left')

# Category-specific 1/99% winsorization for cost shocks (robustness only).
panel['import_cost_change_winsor_pct'] = np.nan
for cat, g in panel.groupby('category'):
    v = g['import_cost_change_pct'].dropna()
    lo, hi = v.quantile([0.01, 0.99])
    panel.loc[g.index, 'import_cost_change_winsor_pct'] = g['import_cost_change_pct'].clip(lo, hi)
for k in range(7):
    panel[f'wcost_l{k}'] = panel.groupby('category')['import_cost_change_winsor_pct'].shift(k)

main = panel.dropna(subset=['cpi_log_change_pct','hhi_l1'] + [f'cost_l{k}' for k in range(4)]).copy()
main = main.sort_values(['month','category']).reset_index(drop=True)
main['time_seq'] = pd.Categorical(main['month'], ordered=True).codes
for k in range(4):
    main[f'cost_hhi_l{k}'] = main[f'cost_l{k}'] * main['hhi_l1']
    main[f'cost_disrupt_l{k}'] = main[f'cost_l{k}'] * main['disruption_2020_23']
    main[f'triple_l{k}'] = main[f'cost_l{k}'] * main['hhi_l1'] * main['disruption_2020_23']
    main[f'cost_top3_l{k}'] = main[f'cost_l{k}'] * main['top3_l1']
    main[f'cost_prehhi_l{k}'] = main[f'cost_l{k}'] * main['pre2020_hhi']
main['hhi_disrupt'] = main['hhi_l1'] * main['disruption_2020_23']

# ---------------------------
# Estimation helpers
# ---------------------------
def fit_dk(formula, data, maxlags=4):
    d = data.sort_values(['month','category']).copy()
    if 'time_seq' not in d:
        d['time_seq'] = pd.Categorical(d['month'], ordered=True).codes
    m = smf.ols(formula, data=d).fit()
    try:
        r = m.get_robustcov_results(
            cov_type='hac-groupsum', time=d['time_seq'].to_numpy(),
            maxlags=maxlags, use_correction='hac'
        )
        cov_name = f'hac-groupsum (Driscoll-Kraay-type), maxlags={maxlags}'
    except Exception as exc:
        warnings.warn(f'hac-groupsum failed ({exc}); falling back to HAC')
        r = m.get_robustcov_results(cov_type='HAC', maxlags=maxlags, use_correction=True)
        cov_name = f'HAC fallback, maxlags={maxlags}'
    return m, r, cov_name


def robust_table(model, robust):
    names = model.model.exog_names
    coef = np.asarray(robust.params, dtype=float)
    se = np.asarray(robust.bse, dtype=float)
    t = np.divide(coef, se, out=np.full_like(coef, np.nan), where=se>0)
    p = 2*(1-norm.cdf(np.abs(t)))
    return pd.DataFrame({
        'term': names,
        'coef': coef,
        'std_error': se,
        't': t,
        'p_value': p,
        'ci_low': coef - 1.96*se,
        'ci_high': coef + 1.96*se,
    })


def lincomb(model, robust, weights):
    names = model.model.exog_names
    b = np.asarray(robust.params, dtype=float)
    cov = np.asarray(robust.cov_params(), dtype=float)
    w = np.array([weights.get(n, 0.0) for n in names], dtype=float)
    est = float(w @ b)
    var = float(w @ cov @ w)
    se = math.sqrt(max(var, 0.0))
    z = est/se if se > 0 else np.nan
    p = float(2*(1-norm.cdf(abs(z)))) if np.isfinite(z) else np.nan
    return {'estimate': est, 'std_error': se, 'ci_low': est-1.96*se, 'ci_high': est+1.96*se, 'p_value': p}

COST_TERMS = '+'.join([f'cost_l{k}' for k in range(4)])
INT_TERMS = '+'.join([f'cost_hhi_l{k}' for k in range(4)])
COSTD_TERMS = '+'.join([f'cost_disrupt_l{k}' for k in range(4)])
TRIPLE_TERMS = '+'.join([f'triple_l{k}' for k in range(4)])
CONTROLS = 'C(category)+C(calendar_month)+trend'

F1 = f'cpi_log_change_pct ~ {COST_TERMS}+{CONTROLS}'
F2 = f'cpi_log_change_pct ~ {COST_TERMS}+hhi_l1+{INT_TERMS}+{CONTROLS}'
F3 = f'cpi_log_change_pct ~ {COST_TERMS}+hhi_l1+disruption_2020_23+hhi_disrupt+{INT_TERMS}+{COSTD_TERMS}+{TRIPLE_TERMS}+{CONTROLS}'

models = {}
for nm, formula in [('RQ1', F1), ('RQ2', F2), ('RQ3', F3)]:
    m, r, cov_name = fit_dk(formula, main, maxlags=4)
    models[nm] = (m, r, robust_table(m,r), formula, cov_name)

# ---------------------------
# Main cumulative quantities
# ---------------------------
cum_rows = []
m1,r1,_,_,_ = models['RQ1']
cum_rows.append({'model':'RQ1','quantity':'Cumulative pass-through (lags 0-3)','hhi_label':'','hhi_level':np.nan,'regime':'All',**lincomb(m1,r1,{f'cost_l{k}':1 for k in range(4)})})

hvals = {
    'Low (25th pct)': float(main['hhi_l1'].quantile(.25)),
    'Median': float(main['hhi_l1'].median()),
    'High (75th pct)': float(main['hhi_l1'].quantile(.75)),
}
m2,r2,_,_,_ = models['RQ2']
for label,h in hvals.items():
    w = {}
    for k in range(4):
        w[f'cost_l{k}'] = 1
        w[f'cost_hhi_l{k}'] = h
    cum_rows.append({'model':'RQ2','quantity':'Cumulative pass-through at HHI','hhi_label':label,'hhi_level':h,'regime':'All',**lincomb(m2,r2,w)})
cum_rows.append({'model':'RQ2','quantity':'Cumulative HHI moderation slope','hhi_label':'','hhi_level':np.nan,'regime':'All',**lincomb(m2,r2,{f'cost_hhi_l{k}':1 for k in range(4)})})

m3,r3,_,_,_ = models['RQ3']
for regime, disrupted in [('Stable',0),('Disruption 2020-23',1)]:
    for label,h in hvals.items():
        w = {}
        for k in range(4):
            w[f'cost_l{k}'] = 1
            w[f'cost_hhi_l{k}'] = h
            if disrupted:
                w[f'cost_disrupt_l{k}'] = 1
                w[f'triple_l{k}'] = h
        cum_rows.append({'model':'RQ3','quantity':'Cumulative pass-through at HHI by regime','hhi_label':label,'hhi_level':h,'regime':regime,**lincomb(m3,r3,w)})

# HHI-moderation slope in each regime and their difference.
stable_slope_w = {f'cost_hhi_l{k}':1 for k in range(4)}
disrupt_slope_w = {}
for k in range(4):
    disrupt_slope_w[f'cost_hhi_l{k}'] = 1
    disrupt_slope_w[f'triple_l{k}'] = 1
cum_rows.append({'model':'RQ3','quantity':'HHI moderation slope - stable','hhi_label':'','hhi_level':np.nan,'regime':'Stable',**lincomb(m3,r3,stable_slope_w)})
cum_rows.append({'model':'RQ3','quantity':'HHI moderation slope - disruption','hhi_label':'','hhi_level':np.nan,'regime':'Disruption 2020-23',**lincomb(m3,r3,disrupt_slope_w)})
cum_rows.append({'model':'RQ3','quantity':'Incremental HHI moderation during disruption','hhi_label':'','hhi_level':np.nan,'regime':'Disruption minus stable',**lincomb(m3,r3,{f'triple_l{k}':1 for k in range(4)})})

# Difference in pass-through disruption vs stable at median HHI.
median_h = hvals['Median']
diff_w = {}
for k in range(4):
    diff_w[f'cost_disrupt_l{k}'] = 1
    diff_w[f'triple_l{k}'] = median_h
cum_rows.append({'model':'RQ3','quantity':'Disruption minus stable cumulative pass-through at median HHI','hhi_label':'Median','hhi_level':median_h,'regime':'Difference',**lincomb(m3,r3,diff_w)})

cum = pd.DataFrame(cum_rows)

# ---------------------------
# Diagnostics
# ---------------------------
rq1_resid = models['RQ1'][0].resid
rq1_exog = models['RQ1'][0].model.exog
bp = het_breuschpagan(rq1_resid, rq1_exog)
main_diag = main.copy(); main_diag['rq1_resid'] = rq1_resid.values

lb_rows=[]
for cat,g in main_diag.sort_values('month').groupby('category'):
    z = acorr_ljungbox(g['rq1_resid'], lags=[6,12], return_df=True)
    lb_rows.append({'category':cat,'lb6_stat':z.loc[6,'lb_stat'],'lb6_p':z.loc[6,'lb_pvalue'],'lb12_stat':z.loc[12,'lb_stat'],'lb12_p':z.loc[12,'lb_pvalue']})
lb = pd.DataFrame(lb_rows)

wide = main_diag.pivot(index='month',columns='category',values='rq1_resid').dropna()
N = wide.shape[1]; T = wide.shape[0]
corr = np.corrcoef(wide.to_numpy(), rowvar=False)
upper = corr[np.triu_indices(N,1)]
pesaran_cd = float(np.sqrt(2*T/(N*(N-1))) * upper.sum())
pesaran_p = float(2*(1-norm.cdf(abs(pesaran_cd))))

diag_summary = pd.DataFrame([
    {'diagnostic':'Breusch-Pagan LM','statistic':bp[0],'p_value':bp[1],'interpretation':'Conventional RQ1 residual heteroskedasticity test'},
    {'diagnostic':'Breusch-Pagan F','statistic':bp[2],'p_value':bp[3],'interpretation':'F version of residual heteroskedasticity test'},
    {'diagnostic':'Pesaran CD (RQ1 residuals)','statistic':pesaran_cd,'p_value':pesaran_p,'interpretation':'Cross-category residual dependence test'},
])

adf_rows=[]
for cat,g in panel.groupby('category'):
    for var in ['cpi_log_change_pct','import_cost_change_pct','hhi']:
        x = g[var].dropna().to_numpy()
        try:
            res = adfuller(x, autolag='AIC')
            adf_rows.append({'category':cat,'variable':var,'adf_stat':res[0],'p_value':res[1],'lags':res[2],'nobs':res[3]})
        except Exception as exc:
            adf_rows.append({'category':cat,'variable':var,'adf_stat':np.nan,'p_value':np.nan,'lags':np.nan,'nobs':len(x),'error':str(exc)})
adf = pd.DataFrame(adf_rows)

# ---------------------------
# QA summary
# ---------------------------
qa_rows=[]
for cat,g in panel.groupby('category'):
    cost = g['import_cost_change_pct'].dropna()
    qa_rows.append({
        'category':cat,'months':len(g),'start_month':g['month'].min(),'end_month':g['month'].max(),
        'missing_cpi':int(g['cpi_index_2015_100'].isna().sum()),'missing_unit_value':int(g['unit_value_gbp_per_kg'].isna().sum()),
        'min_hhi':g['hhi'].min(),'median_hhi':g['hhi'].median(),'max_hhi':g['hhi'].max(),
        'min_top3':g['top3_share'].min(),'max_top3':g['top3_share'].max(),
        'min_supplier_count':int(g['supplier_count'].min()),'max_supplier_count':int(g['supplier_count'].max()),
        'min_cost_change_pct':cost.min(),'p01_cost_change_pct':cost.quantile(.01),'p99_cost_change_pct':cost.quantile(.99),'max_cost_change_pct':cost.max(),
        'min_unit_value':g['unit_value_gbp_per_kg'].min(),'max_unit_value':g['unit_value_gbp_per_kg'].max(),
    })
qa = pd.DataFrame(qa_rows)

# ---------------------------
# Robustness specifications + cumulative effects
# ---------------------------
robust_coef_rows=[]
robust_cum_rows=[]

def fit_robust_spec(label, data, formula, focal_terms, cumulative_weights=None, maxlags=4):
    d = data.dropna(subset=['cpi_log_change_pct']).copy().sort_values(['month','category']).reset_index(drop=True)
    d['time_seq'] = pd.Categorical(d['month'], ordered=True).codes
    m,r,cov_name = fit_dk(formula,d,maxlags=maxlags)
    tab = robust_table(m,r)
    for term in focal_terms:
        rr = tab.loc[tab['term']==term]
        if len(rr):
            rec = rr.iloc[0].to_dict(); rec.update({'specification':label,'nobs':int(r.nobs),'r2':m.rsquared,'covariance':cov_name}); robust_coef_rows.append(rec)
    if cumulative_weights is not None:
        rec = lincomb(m,r,cumulative_weights); rec.update({'specification':label,'nobs':int(r.nobs),'r2':m.rsquared,'covariance':cov_name}); robust_cum_rows.append(rec)
    return m,r

# 0-6 lags
sample6 = panel.dropna(subset=['cpi_log_change_pct']+[f'cost_l{k}' for k in range(7)]).copy()
f6 = 'cpi_log_change_pct ~ ' + '+'.join([f'cost_l{k}' for k in range(7)]) + '+C(category)+C(calendar_month)+trend'
fit_robust_spec('RQ1 lags 0-6', sample6, f6, [f'cost_l{k}' for k in range(7)], {f'cost_l{k}':1 for k in range(7)}, maxlags=6)

# winsorized cost 0-3
samplew = panel.dropna(subset=['cpi_log_change_pct']+[f'wcost_l{k}' for k in range(4)]).copy()
fw = 'cpi_log_change_pct ~ ' + '+'.join([f'wcost_l{k}' for k in range(4)]) + '+C(category)+C(calendar_month)+trend'
fit_robust_spec('RQ1 winsorized 1-99%', samplew, fw, [f'wcost_l{k}' for k in range(4)], {f'wcost_l{k}':1 for k in range(4)})

# exclusion / break subsamples
for label, data in [
    ('RQ1 exclude Feb-Jul 2026 ONS flag', main.loc[main['ons_2026_flag']==0]),
    ('RQ1 post-May-2016', main.loc[main['post_may2016']==1]),
    ('RQ1 post-Jan-2022', main.loc[main['post_jan2022']==1]),
]:
    fit_robust_spec(label, data, F1, [f'cost_l{k}' for k in range(4)], {f'cost_l{k}':1 for k in range(4)})

# full month-year FE
f_time = f'cpi_log_change_pct ~ {COST_TERMS}+C(category)+C(month_str)'
fit_robust_spec('RQ1 full month-year FE', main, f_time, [f'cost_l{k}' for k in range(4)], {f'cost_l{k}':1 for k in range(4)})

# top-3 moderator
f_top = f'cpi_log_change_pct ~ {COST_TERMS}+top3_l1+' + '+'.join([f'cost_top3_l{k}' for k in range(4)]) + '+' + CONTROLS
fit_robust_spec('RQ2 Top-3 moderator slope', main, f_top, [f'cost_top3_l{k}' for k in range(4)], {f'cost_top3_l{k}':1 for k in range(4)})

# predetermined pre-2020 HHI moderator
f_pre = f'cpi_log_change_pct ~ {COST_TERMS}+pre2020_hhi+' + '+'.join([f'cost_prehhi_l{k}' for k in range(4)]) + '+' + CONTROLS
fit_robust_spec('RQ2 pre-2020 average HHI moderator slope', main, f_pre, [f'cost_prehhi_l{k}' for k in range(4)], {f'cost_prehhi_l{k}':1 for k in range(4)})

robust_coef = pd.DataFrame(robust_coef_rows)
robust_cum = pd.DataFrame(robust_cum_rows)

# ---------------------------
# Category-specific RQ1 models
# ---------------------------
cat_rows=[]
for cat,g in panel.groupby('category'):
    d = g.dropna(subset=['cpi_log_change_pct']+[f'cost_l{k}' for k in range(4)]).copy()
    f = 'cpi_log_change_pct ~ ' + COST_TERMS + '+C(calendar_month)+trend'
    m = smf.ols(f, data=d).fit(cov_type='HAC', cov_kwds={'maxlags':4,'use_correction':True})
    names=list(m.params.index); w=np.zeros(len(names))
    for k in range(4):
        term=f'cost_l{k}'
        if term in names: w[names.index(term)] = 1
    est=float(w @ m.params.to_numpy()); se=float(np.sqrt(max(0,w @ m.cov_params().to_numpy() @ w)))
    p=float(2*(1-norm.cdf(abs(est/se)))) if se>0 else np.nan
    cat_rows.append({'category':cat,'nobs':int(m.nobs),'cum_pass_through':est,'std_error':se,'ci_low':est-1.96*se,'ci_high':est+1.96*se,'p_value':p,'r2':m.rsquared})
cat_results = pd.DataFrame(cat_rows)

# ---------------------------
# Model summaries and save
# ---------------------------
coef_tables={nm: tab for nm,(_,_,tab,_,_) in models.items()}
model_rows=[]
for nm,(m,r,tab,formula,cov_name) in models.items():
    model_rows.append({'model':nm,'nobs':int(r.nobs),'r_squared':m.rsquared,'adj_r_squared':m.rsquared_adj,'formula':formula,'covariance':cov_name})
model_summary = pd.DataFrame(model_rows)

# Additional quality-gate statement based on live extraction audit, recorded separately.
live_audit = pd.DataFrame([
    ['Meat',5239,151,0,0,6,0.0],
    ['Fish',11057,151,0,0,10,3.8599641494516924e-7],
    ['Milk, cheese & eggs',4583,151,0,0,11,0.0],
    ['Oils & fats',9560,151,0,0,25,0.0],
    ['Fruit',14069,151,0,0,19,0.0],
    ['Vegetables',13688,151,0,0,4,2.2607814522773397e-9],
], columns=['category','country_month_records','months','null_country_rows','suppressed_rows','bad_mass_rows','bad_mass_value_share'])
live_audit['country_month_records_total'] = live_audit['country_month_records'].sum()

# save
PROCESSED = ROOT / 'data' / 'processed'
PROCESSED.mkdir(parents=True, exist_ok=True)
hmrc.to_csv(PROCESSED/'hmrc_monthly_core_measures_2014_2026.csv', index=False)
panel.to_csv(PROCESSED/'master_panel_core_2014_2026.csv', index=False)
main.to_csv(PROCESSED/'analysis_sample_main_lag03.csv', index=False)
hmrc.to_csv(OUT/'hmrc_monthly_core_measures_2014_2026.csv', index=False)
panel.to_csv(OUT/'master_panel_core_2014_2026.csv', index=False)
main.to_csv(OUT/'analysis_sample_main_lag03.csv', index=False)
qa.to_csv(OUT/'qa_category_summary.csv', index=False)
live_audit.to_csv(OUT/'hmrc_live_extraction_audit.csv', index=False)
lb.to_csv(OUT/'diagnostic_ljung_box_by_category.csv', index=False)
adf.to_csv(OUT/'diagnostic_adf_by_category.csv', index=False)
diag_summary.to_csv(OUT/'diagnostic_global_tests.csv', index=False)
cum.to_csv(OUT/'cumulative_effects_rq1_rq3.csv', index=False)
robust_coef.to_csv(OUT/'robustness_coefficients.csv', index=False)
robust_cum.to_csv(OUT/'robustness_cumulative_effects.csv', index=False)
cat_results.to_csv(OUT/'category_specific_rq1.csv', index=False)
model_summary.to_csv(OUT/'model_summary.csv', index=False)
for nm,t in coef_tables.items():
    t.to_csv(OUT/f'{nm.lower()}_coefficients.csv', index=False)

# Machine-readable findings summary.
findings = {
    'sample': {'panel_rows':len(panel),'categories':int(panel.category.nunique()),'months_per_category':151,'main_model_rows':len(main),'start':'2014-01','end':'2026-07'},
    'hhi_reference': hvals,
    'rq1': cum.loc[(cum.model=='RQ1')].to_dict('records'),
    'rq2': cum.loc[(cum.model=='RQ2')].to_dict('records'),
    'rq3': cum.loc[(cum.model=='RQ3')].to_dict('records'),
    'category_specific_rq1': cat_results.to_dict('records'),
    'robustness_cumulative': robust_cum.to_dict('records'),
    'diagnostics_global': diag_summary.to_dict('records'),
}
def _json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value

(OUT/'findings_summary.json').write_text(json.dumps(_json_safe(findings), indent=2, default=str, allow_nan=False), encoding='utf-8')

# Human-readable summary.
lines=[]
lines.append('UK FOOD PRICE PASS-THROUGH - TECHNICAL ANALYSIS SUMMARY')
lines.append('='*56)
lines.append(f'Panel: {len(panel)} category-month rows; {panel.category.nunique()} categories; Jan 2014-Jul 2026; 151 months/category.')
lines.append(f'Main lag(0-3) estimation sample: {len(main)} rows.')
lines.append('')
for _,row in cum.iterrows():
    lines.append(f"{row['model']} | {row['quantity']} | {row.get('hhi_label','')} | {row['regime']} | est={row['estimate']:.6f} | SE={row['std_error']:.6f} | 95% CI [{row['ci_low']:.6f}, {row['ci_high']:.6f}] | p={row['p_value']:.6g}")
lines.append('')
lines.append('Robustness cumulative effects:')
for _,row in robust_cum.iterrows():
    lines.append(f"{row['specification']} | est={row['estimate']:.6f} | 95% CI [{row['ci_low']:.6f}, {row['ci_high']:.6f}] | p={row['p_value']:.6g} | n={int(row['nobs'])}")
lines.append('')
lines.append(f"Diagnostics: Pesaran CD={pesaran_cd:.4f}, p={pesaran_p:.6g}; Breusch-Pagan LM p={bp[1]:.6g}.")
(OUT/'analysis_summary.txt').write_text('\n'.join(lines), encoding='utf-8')

print('\n'.join(lines[:42]))
print('\nCategory-specific RQ1:')
print(cat_results.round(6).to_string(index=False))
print('\nRobustness cumulative:')
print(robust_cum.round(6).to_string(index=False))
print('\nOutputs:', OUT)
