from __future__ import annotations

import numpy as np
import pandas as pd


def hhi_from_values(values: pd.Series) -> float:
    values = pd.to_numeric(values, errors="coerce").fillna(0.0)
    total = values.sum()
    if total <= 0:
        return np.nan
    shares = values / total
    return float((shares ** 2).sum())


def top_n_share(values: pd.Series, n: int = 3) -> float:
    values = pd.to_numeric(values, errors="coerce").fillna(0.0)
    total = values.sum()
    if total <= 0:
        return np.nan
    return float(values.nlargest(n).sum() / total)


def safe_log_change(series: pd.Series, periods: int = 1) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    prior = s.shift(periods)
    valid = (s > 0) & (prior > 0)
    out = pd.Series(np.nan, index=s.index, dtype=float)
    out.loc[valid] = 100 * np.log(s.loc[valid] / prior.loc[valid])
    return out


def aggregate_trade(raw: pd.DataFrame, country_dim: pd.DataFrame | None = None) -> pd.DataFrame:
    required = {"category", "MonthId", "CountryId", "SuppressionIndex", "ImportValue", "NetMass"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"Missing HMRC columns: {sorted(missing)}")

    x = raw.copy()
    x["ImportValue"] = pd.to_numeric(x["ImportValue"], errors="coerce")
    x["NetMass"] = pd.to_numeric(x["NetMass"], errors="coerce")
    x["SuppressionIndex"] = pd.to_numeric(x["SuppressionIndex"], errors="coerce").fillna(0)

    if country_dim is not None and not country_dim.empty:
        x = x.merge(country_dim[["CountryId", "CountryName"]], on="CountryId", how="left")
    else:
        x["CountryName"] = x["CountryId"].astype("Int64").astype(str)

    rows = []
    for (category, month), g in x.groupby(["category", "MonthId"], sort=True):
        total_value = g["ImportValue"].sum(min_count=1)
        known = g[(g["CountryId"].notna()) & (g["SuppressionIndex"] == 0)].copy()
        known_value = known["ImportValue"].sum(min_count=1)

        hhi = hhi_from_values(known["ImportValue"])
        top3 = top_n_share(known["ImportValue"], 3)

        usable = g[(g["NetMass"].notna()) & (g["NetMass"] > 0)].copy()
        usable_value = usable["ImportValue"].sum(min_count=1)
        usable_mass = usable["NetMass"].sum(min_count=1)
        unit_value = usable_value / usable_mass if pd.notna(usable_mass) and usable_mass > 0 else np.nan

        suppressed_value = g.loc[g["SuppressionIndex"] != 0, "ImportValue"].sum(min_count=1)
        rows.append({
            "category": category,
            "MonthId": int(month),
            "import_value": total_value,
            "known_country_value": known_value,
            "known_country_coverage": known_value / total_value if pd.notna(total_value) and total_value > 0 else np.nan,
            "suppressed_value_share": suppressed_value / total_value if pd.notna(total_value) and total_value > 0 and pd.notna(suppressed_value) else 0.0,
            "supplier_count": int((known["ImportValue"] > 0).sum()),
            "hhi": hhi,
            "hhi_10000": hhi * 10000 if pd.notna(hhi) else np.nan,
            "top3_share": top3,
            "usable_net_mass": usable_mass,
            "usable_mass_value": usable_value,
            "mass_value_coverage": usable_value / total_value if pd.notna(total_value) and total_value > 0 and pd.notna(usable_value) else np.nan,
            "unit_value_gbp_per_kg": unit_value,
        })

    out = pd.DataFrame(rows)
    out["month"] = pd.to_datetime(out["MonthId"].astype(str), format="%Y%m")
    out = out.sort_values(["category", "month"]).reset_index(drop=True)
    out["import_cost_change_pct"] = out.groupby("category")["unit_value_gbp_per_kg"].transform(safe_log_change)
    return out


def supplier_composition(raw: pd.DataFrame, country_dim: pd.DataFrame) -> pd.DataFrame:
    x = raw.merge(country_dim[["CountryId", "CountryName"]], on="CountryId", how="left")
    x = x[(x["SuppressionIndex"].fillna(0) == 0) & x["CountryId"].notna()].copy()
    g = x.groupby(["category", "MonthId", "CountryId", "CountryName"], as_index=False)["ImportValue"].sum()
    totals = g.groupby(["category", "MonthId"])["ImportValue"].transform("sum")
    g["supplier_share"] = g["ImportValue"] / totals
    g["month"] = pd.to_datetime(g["MonthId"].astype(str), format="%Y%m")
    return g
