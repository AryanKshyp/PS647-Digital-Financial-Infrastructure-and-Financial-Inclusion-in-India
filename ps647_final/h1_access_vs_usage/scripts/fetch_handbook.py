#!/usr/bin/env python3
"""
Fetch RBI Handbook of Statistics on Indian States 2024-25 tables.

Each table lives at https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=<id>
and is rendered as HTML, split across two <table> elements: the first covers the
earlier years, the second (marked "Concld.") the later years. We pull both,
stitch them on the state-name column, and write one tidy long CSV per table plus
the untouched HTML for provenance.

No transformation of values beyond stripping thousands separators and footnote
markers -- harmonisation and index construction happen downstream.
"""

import re
import sys
import time
import html as htmllib
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared

RAW = SHARED / "raw/handbook_states"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BASE = "https://www.rbi.org.in/Scripts/PublicationsView.aspx?id={}"

# Tables we need from the 2024-25 edition.
TABLES = {
    23601: ("t152_bank_offices", "Table 152: State-wise Distribution of Offices of Scheduled Commercial Banks"),
    23604: ("t155_deposits", "Table 155: State-wise Deposits by Scheduled Commercial Banks"),
    23605: ("t156_credit", "Table 156: State-wise Credit by Scheduled Commercial Banks"),
    23468: ("t19_pc_nsdp_current", "Table 19: Per Capita Net State Domestic Product (Current Prices)"),
    23469: ("t19_pc_nsdp_constant", "Table 20: Per Capita Net State Domestic Product (Constant Prices)"),
    23602: ("t153_cd_ratio_sanction", "Table 153: State-wise Credit-Deposit Ratio (Place of Sanction)"),
    23603: ("t154_cd_ratio_utilisation", "Table 154: State-wise Credit-Deposit Ratio (Place of Utilisation)"),
}

# Rows that are regional aggregates or footnotes, not states.
NON_STATE = re.compile(
    r"^(NORTHERN|NORTH[- ]EASTERN|EASTERN|CENTRAL|WESTERN|SOUTHERN)\s+REGION$|"
    r"^ALL[- ]INDIA$|^TOTAL$|^Note|^Source|^\*|^-$|^nan$",
    re.I,
)

YEAR_RE = re.compile(r"^(?:19|20)\d{2}(?:-\d{2})?$")


def fetch(table_id: str) -> str:
    r = requests.get(BASE.format(table_id), headers={"User-Agent": UA}, timeout=90)
    r.raise_for_status()
    return r.text


def clean_cell(v):
    """Strip footnote markers, thousands separators, and RBI's null placeholders."""
    if pd.isna(v):
        return None
    s = str(v).strip()
    s = htmllib.unescape(s)
    s = s.replace(",", "").replace("–", "-").replace("—", "-")
    s = re.sub(r"[@#*$]+$", "", s).strip()
    if s in {"", "-", "--", "..", "...", "n.a.", "N.A.", "NA", "nan", "Neg.", "@"}:
        return None
    return s


def find_header_row(df: pd.DataFrame) -> int:
    """The header row is the one where most cells look like years."""
    best, best_n = None, 0
    for i in range(min(8, len(df))):
        cells = [clean_cell(c) for c in df.iloc[i].tolist()[1:]]
        n = sum(1 for c in cells if c and YEAR_RE.match(c))
        if n > best_n:
            best, best_n = i, n
    return best if best_n >= 2 else None


def tidy_block(df: pd.DataFrame) -> pd.DataFrame:
    """Turn one HTML table block into long (state, year, value)."""
    hdr = find_header_row(df)
    if hdr is None:
        return pd.DataFrame(columns=["state_raw", "year_label", "value"])

    years = [clean_cell(c) for c in df.iloc[hdr].tolist()]
    body = df.iloc[hdr + 1 :]

    recs = []
    for _, row in body.iterrows():
        state = clean_cell(row.iloc[0])
        if not state or NON_STATE.match(state):
            continue
        # Repeated title text in a merged cell -> skip
        if len(state) > 60:
            continue
        for j in range(1, len(row)):
            y = years[j] if j < len(years) else None
            if not y or not YEAR_RE.match(y):
                continue
            v = clean_cell(row.iloc[j])
            if v is None:
                recs.append({"state_raw": state, "year_label": y, "value": None})
                continue
            try:
                recs.append({"state_raw": state, "year_label": y, "value": float(v)})
            except ValueError:
                recs.append({"state_raw": state, "year_label": y, "value": None})
    return pd.DataFrame(recs)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    summary = []

    for tid, (slug, title) in TABLES.items():
        print(f"\n=== {slug}  (id={tid}) ===")
        try:
            page = fetch(str(tid))
        except Exception as e:
            print(f"  FETCH FAILED: {e}")
            summary.append((slug, "FETCH FAILED", "", ""))
            continue

        (RAW / f"{slug}.html").write_text(page, encoding="utf-8")

        blocks = pd.read_html(StringIO(page))
        parts = [tidy_block(b) for b in blocks if b.shape[0] > 5 and b.shape[1] > 3]
        parts = [p for p in parts if len(p)]
        if not parts:
            print("  NO DATA PARSED")
            summary.append((slug, "NO DATA", "", ""))
            continue

        long = pd.concat(parts, ignore_index=True)
        long = long.drop_duplicates(subset=["state_raw", "year_label"], keep="last")
        long["table"] = slug
        long["source_title"] = title
        long["source_url"] = BASE.format(tid)

        out = RAW / f"{slug}.csv"
        long.to_csv(out, index=False)

        yrs = sorted(long["year_label"].unique())
        n_states = long["state_raw"].nunique()
        cov = long.dropna(subset=["value"])
        print(f"  rows={len(long)}  states={n_states}  years={yrs[0]}..{yrs[-1]} ({len(yrs)})")
        print(f"  non-null values={len(cov)}  -> {out}")
        summary.append((slug, f"{n_states} states", f"{yrs[0]}..{yrs[-1]}", str(len(cov))))

        time.sleep(1.5)

    print("\n\n================ SUMMARY ================")
    for s in summary:
        print(f"  {s[0]:32s} {s[1]:14s} {s[2]:16s} nonnull={s[3]}")


if __name__ == "__main__":
    sys.exit(main())
