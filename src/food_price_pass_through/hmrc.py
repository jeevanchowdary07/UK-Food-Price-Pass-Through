from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode
import time
import re
import pandas as pd
import requests

BASE = "https://api.uktradeinfo.com/OTS"
COUNTRY_ENDPOINT = "https://api.uktradeinfo.com/Country"
COMMODITY_ENDPOINT = "https://api.uktradeinfo.com/Commodity"


def _commodity_filter(spec: dict) -> str:
    terms = []
    for code in spec.get("hs2", []):
        terms.append(f"Commodity/Hs2Code eq '{code}'")
    for code in spec.get("hs4", []):
        terms.append(f"Commodity/Hs4Code eq '{code}'")
    if not terms:
        raise ValueError("Commodity mapping is empty.")
    return "(" + " or ".join(terms) + ")"


def build_ots_url(spec: dict, start_month: int, end_month: int) -> str:
    filt = (
        f"(FlowTypeId eq 1 or FlowTypeId eq 3) and "
        f"MonthId ge {start_month} and MonthId le {end_month} and "
        f"{_commodity_filter(spec)}"
    )
    # Keep SuppressionIndex in the grouping so the quality audit can quantify
    # suppressed records rather than losing that information during aggregation.
    apply = (
        f"filter({filt})/"
        "groupby((MonthId,CountryId,SuppressionIndex),"
        "aggregate(Value with sum as ImportValue,NetMass with sum as NetMass))"
    )
    return BASE + "?" + urlencode({"$apply": apply}, safe="()/',$= ").replace("+", "%20")


def _get_json(session: requests.Session, url: str, timeout: int = 120, retries: int = 5) -> dict:
    last = None
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:  # noqa: BLE001 - preserve last network error
            last = exc
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"HMRC request failed after {retries} attempts: {url}") from last


def fetch_odata(session: requests.Session, url: str, delay_seconds: float = 1.05) -> list[dict]:
    rows: list[dict] = []
    next_url: str | None = url
    calls = 0
    while next_url:
        obj = _get_json(session, next_url)
        rows.extend(obj.get("value", []))
        next_url = obj.get("@odata.nextLink")
        calls += 1
        if next_url:
            time.sleep(delay_seconds)
        if calls > 5000:
            raise RuntimeError("Pagination safety limit reached.")
    return rows


def fetch_countries(session: requests.Session) -> pd.DataFrame:
    rows = fetch_odata(session, COUNTRY_ENDPOINT)
    keep = ["CountryId", "CountryName", "CountryCodeAlpha", "RegionId", "Area1a"]
    return pd.DataFrame(rows)[keep].drop_duplicates("CountryId")


def acquire_category(
    category: str,
    spec: dict,
    start_month: int,
    end_month: int,
    output_dir: Path,
    session: requests.Session | None = None,
) -> tuple[pd.DataFrame, str]:
    session = session or requests.Session()
    session.headers.update({"User-Agent": "uk-food-price-pass-through-academic-research"})
    url = build_ots_url(spec, start_month, end_month)
    rows = fetch_odata(session, url)
    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(f"No HMRC records returned for {category}.")
    df.insert(0, "category", category)
    df["ImportValue"] = pd.to_numeric(df["ImportValue"], errors="coerce")
    df["NetMass"] = pd.to_numeric(df["NetMass"], errors="coerce")
    output_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9]+", "_", category).strip("_").lower()
    df.to_csv(output_dir / f"{safe}.csv", index=False)
    return df, url


def acquire_all(config: dict, mapping_version: str, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    session = requests.Session()
    session.headers.update({"User-Agent": "uk-food-price-pass-through-academic-research"})
    project = config["project"]
    frames = []
    log = []
    for category, meta in config["categories"].items():
        df, url = acquire_category(
            category=category,
            spec=meta[mapping_version],
            start_month=int(project["start_month"]),
            end_month=int(project["requested_end_month"]),
            output_dir=output_dir,
            session=session,
        )
        frames.append(df)
        log.append({"category": category, "mapping": mapping_version, "url": url, "rows": len(df)})
    countries = fetch_countries(session)
    countries.to_csv(output_dir / "country_dimension.csv", index=False)
    return pd.concat(frames, ignore_index=True), pd.DataFrame(log)
