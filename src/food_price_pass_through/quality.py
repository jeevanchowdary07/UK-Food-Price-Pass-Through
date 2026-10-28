from __future__ import annotations

import pandas as pd


def quality_summary(panel: pd.DataFrame) -> pd.DataFrame:
    return (
        panel.groupby("category", as_index=False)
        .agg(
            first_month=("month", "min"),
            last_month=("month", "max"),
            n=("month", "size"),
            min_country_coverage=("known_country_coverage", "min"),
            median_country_coverage=("known_country_coverage", "median"),
            min_mass_coverage=("mass_value_coverage", "min"),
            median_mass_coverage=("mass_value_coverage", "median"),
            max_suppressed_value_share=("suppressed_value_share", "max"),
            missing_hhi=("hhi", lambda s: int(s.isna().sum())),
            missing_unit_value=("unit_value_gbp_per_kg", lambda s: int(s.isna().sum())),
        )
    )


def apply_quality_gate(
    panel: pd.DataFrame,
    min_country_coverage: float,
    min_mass_value_coverage: float,
) -> pd.DataFrame:
    x = panel.copy()
    x["quality_pass"] = (
        (x["known_country_coverage"] >= min_country_coverage)
        & (x["mass_value_coverage"] >= min_mass_value_coverage)
        & x["hhi"].notna()
        & x["import_cost_change_pct"].notna()
        & x["cpi_log_change_pct"].notna()
    )
    return x
