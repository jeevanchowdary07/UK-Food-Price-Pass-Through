# Research-question traceability

| RQ / check | Specification | Implementation | Main output | Reported result |
|---|---|---|---|---|
| RQ1 | 0–3 month distributed lag | `scripts/03_reproduce_final_analysis.py`; `models.py::lincomb` | `rq1_coefficients.csv`; `cumulative_effects_rq1_rq3.csv` | cumulative estimate 0.1253; Figure 05; Figure 08 |
| RQ2 | cost × lagged-HHI interactions | `scripts/03_reproduce_final_analysis.py` | `rq2_coefficients.csv`; cumulative effects table | HHI moderation p≈0.819; Figure 06 |
| RQ3 | cost × HHI × disruption interactions | `scripts/03_reproduce_final_analysis.py` | `rq3_coefficients.csv`; cumulative effects table | disruption difference p≈0.007; HHI-specific p≈0.440; Figure 07 |
| Diagnostics | Breusch–Pagan, Pesaran CD, Ljung–Box, ADF | `scripts/03_reproduce_final_analysis.py` | diagnostic CSVs | basis for robust covariance choice |
| Robustness | alternative lags, outlier treatment, periods, time effects and concentration measures | `scripts/03_reproduce_final_analysis.py` | `robustness_cumulative_effects.csv` | Figure 08 and sensitivity results |

This table links each research question to the code and output used to report the result.
