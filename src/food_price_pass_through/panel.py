from __future__ import annotations

import numpy as np
import pandas as pd


def load_ons(path) -> pd.DataFrame:
    x = pd.read_csv(path, parse_dates=["month"])
    x = x.sort_values(["category", "month"]).copy()
    if "cpi_log_change_pct" not in x:
        x["cpi_log_change_pct"] = x.groupby("category")["cpi_index_2015_100"].transform(
            lambda s: 100 * np.log(s / s.shift(1))
        )
    if "cpi_yoy_log_pct" not in x:
        x["cpi_yoy_log_pct"] = x.groupby("category")["cpi_index_2015_100"].transform(
            lambda s: 100 * np.log(s / s.shift(12))
        )
    return x


def merge_core_panel(ons: pd.DataFrame, trade: pd.DataFrame, disruption_start: str, disruption_end: str) -> pd.DataFrame:
    panel = ons.merge(trade.drop(columns=["MonthId"], errors="ignore"), on=["category", "month"], how="inner")
    latest_common = panel.groupby("category")["month"].max().min()
    panel = panel[panel["month"] <= latest_common].copy()
    panel["disruption_2020_23"] = (
        (panel["month"] >= pd.Timestamp(disruption_start))
        & (panel["month"] <= pd.Timestamp(disruption_end))
    ).astype(int)
    panel["hmrc_post_may2016"] = (panel["month"] >= pd.Timestamp("2016-05-01")).astype(int)
    panel["hmrc_post_jan2022"] = (panel["month"] >= pd.Timestamp("2022-01-01")).astype(int)
    panel["ons_2026_quality_flag"] = (
        (panel["month"] >= pd.Timestamp("2026-02-01"))
        & (panel["month"] <= pd.Timestamp("2026-07-01"))
    ).astype(int)
    return panel.sort_values(["category", "month"]).reset_index(drop=True)
