# Formula-to-code map

| Analytical quantity | Formula | Implementation |
|---|---|---|
| Supplier shares | `V_j / ΣV_j` | `features.py::hhi_from_values`, `supplier_composition` |
| HHI | `Σs_j²` | `features.py::hhi_from_values` |
| Top-3 share | sum of largest 3 value shares | `features.py::top_n_share` |
| Unit value | usable import value / usable net mass | `features.py::aggregate_trade`; final analysis extract |
| Monthly log change | `100 × ln(x_t/x_t-1)` | `features.py::safe_log_change`; analysis script |
| RQ1 cumulative effect | `Σβ_k, k=0..3` | `models.py::lincomb`; analysis script |
| RQ2 marginal pass-through | `Σ(β_k+θ_k h)` | linear-combination weights in analysis script |
| RQ3 regime pass-through | base + disruption interactions | linear-combination weights in analysis script |
| Cumulative SE | `sqrt(w'Σw)` | `models.py::lincomb`; analysis script |
| Robust covariance | cross-section/time HAC | `models.py::fit_dk`; analysis script |
