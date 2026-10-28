from pathlib import Path
import math
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "results" / "tables"
F = ROOT / "results" / "figures" / "01_dissertation_figures"

checks = []
def check(name, actual, expected=None, tol=1e-6, predicate=None):
    if predicate is not None:
        ok = bool(predicate(actual))
        exp = "rule"
    else:
        ok = math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=tol)
        exp = expected
    checks.append((name, actual, exp, ok))
    return ok

cum = pd.read_csv(T / "cumulative_effects_rq1_rq3.csv")
qa = pd.read_csv(T / "qa_gate_final.csv")
rob = pd.read_csv(T / "robustness_cumulative_effects.csv")
cat = pd.read_csv(T / "category_specific_rq1.csv")

rq1 = cum[(cum.model=="RQ1") & (cum.quantity.str.contains("Cumulative pass-through"))].iloc[0]
rq2 = cum[(cum.model=="RQ2") & (cum.quantity=="Cumulative HHI moderation slope")].iloc[0]
rq3d = cum[(cum.model=="RQ3") & (cum.quantity.str.startswith("Disruption minus stable"))].iloc[0]
rq3h = cum[(cum.model=="RQ3") & (cum.quantity=="Incremental HHI moderation during disruption")].iloc[0]

check("RQ1 cumulative estimate", rq1.estimate, 0.125339, 1e-6)
check("RQ1 CI lower", rq1.ci_low, 0.062008, 1e-6)
check("RQ1 CI upper", rq1.ci_high, 0.188670, 1e-6)
check("RQ1 p-value", rq1.p_value, 0.000104858, 2e-8)
check("RQ2 HHI moderation estimate", rq2.estimate, -0.102688, 1e-6)
check("RQ2 HHI moderation p-value", rq2.p_value, 0.818925, 1e-6)
check("RQ3 disruption-minus-stable estimate", rq3d.estimate, 0.123824, 1e-6)
check("RQ3 disruption-minus-stable p-value", rq3d.p_value, 0.007168, 1e-6)
check("RQ3 incremental HHI moderation", rq3h.estimate, 0.580920, 1e-6)
check("RQ3 incremental HHI p-value", rq3h.p_value, 0.439816, 1e-6)
check("QA categories", len(qa), 6, 0)
check("QA all PASS", (qa.qa_gate=="PASS").all(), predicate=lambda x:x is True or x==True)
check("RQ1 robustness all positive", (rob.loc[rob.specification.str.startswith('RQ1'),'estimate']>0).all(), predicate=lambda x:x is True or x==True)
check("Meat strongest category estimate", cat.loc[cat.cum_pass_through.idxmax(),'category'], predicate=lambda x:x=="Meat")
check("Eight numbered figures", len(list(F.glob('figure_*.png'))), 8, 0)

processed = ROOT / 'data' / 'processed'
if (processed/'master_panel_core_2014_2026.csv').exists():
    panel = pd.read_csv(processed/'master_panel_core_2014_2026.csv')
    check("Master panel rows", len(panel), 906, 0)
    check("Master panel categories", panel.category.nunique(), 6, 0)
if (processed/'analysis_sample_main_lag03.csv').exists():
    main = pd.read_csv(processed/'analysis_sample_main_lag03.csv')
    check("Primary analysis rows", len(main), 882, 0)

lines = ["# Reproducibility verification", "", "| Check | Actual | Expected | Status |", "|---|---:|---:|:---:|"]
for name, actual, expected, ok in checks:
    lines.append(f"| {name} | {actual} | {expected} | {'PASS' if ok else 'FAIL'} |")
all_ok = all(x[3] for x in checks)
lines += ["", f"**OVERALL VERIFICATION STATUS: {'PASS' if all_ok else 'FAIL'}**", ""]
report = ROOT / 'results' / 'reports' / 'REPRODUCIBILITY_REPORT.md'
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines))
if not all_ok:
    raise SystemExit(1)
