#!/usr/bin/env python3
"""
H5 Step 1 -- build the conversion-capacity moderators and placebo controls.

Reads  raw/diglit/nfhs5_states_factsheet.csv   (NFHS-5 2019-21 state fact sheets, long format)
       hardcoded NSS 75th round tables          (transcribed from raw/diglit/nsso75_round_analysis.pdf)
       hardcoded Census 2011 literacy           (census2011.co.in, Census of India 2011)
Writes data/09_diglit.csv                       one row per panel state_key

SOURCES AND PROVENANCE
----------------------
1. NFHS-5 (2019-21), International Institute for Population Sciences.
   State fact sheets, 131 indicators x 36 states/UTs. Obtained via the compiled mirror
   github.com/jvargh7/nfhs5_factsheets ("data for analysis/states.csv"), which the author
   flags as not extensively cross-checked. VERIFIED here against independently published
   figures before use -- see assert_nfhs_spotchecks(). Indicators used:
     #18 Women who have ever used the internet (%)      -> diglit_w      [PRIMARY MODERATOR]
     #19 Men who have ever used the internet (%)        -> diglit_m
     #16 Women with 10 or more years of schooling (%)   -> schooling_w   [PLACEBO]
     #1  Female population 6+ who ever attended school  -> everschool_w  [PLACEBO]
     #123 Women having a mobile phone they use (%)      -> mobile_w      [ALT MODERATOR]
     #122 Women having a bank account they use (%)      -> bankacct_w    [VALIDATION ONLY]

2. NSS 75th round (July 2017-June 2018), Schedule 25.2, MoSPI/NSO.
   Tables 13 and 14, "All Areas / Persons" column, persons aged 5 years and above.
   Transcribed from raw/diglit/nsso75_round_analysis.pdf (Mehta, Education for All in India),
   which reproduces the NSO state tables. Covers 22 major states only -- the NE states and
   small UTs are not in the published table. Used as the PRE-WINDOW robustness moderator:
   2017-18 strictly precedes every outcome year (FY2019-FY2023).

3. Census 2011 literacy rate, from census2011.co.in (Census of India 2011).
   Telangana did not exist in 2011; the undivided Andhra Pradesh value is assigned to both
   ANDHRA PRADESH and TELANGANA and flagged in `lit2011_undivided_ap`.

DERIVED URBAN SHARE
-------------------
Census 2011 publishes no single machine-readable state urbanisation table we could verify,
so urban share is DERIVED from NFHS-5's own urban/rural/total decomposition:

    total = u*urban + (1-u)*rural   =>   u = (total - rural) / (urban - rural)

This is the implied urban share of the NFHS-5 women's sample, NOT the Census figure. It tracks
Census 2011 closely (Delhi 98.2 vs 97.5, Kerala 48.6 vs 47.7, Maharashtra 46.7 vs 45.2,
Puducherry 69.7 vs 68.3) but is a survey-sample quantity and is labelled as such. It is used
only as a placebo control, never as a headline variable.

D2 STATE HARMONISATION
----------------------
NFHS-5 reports Jammu & Kashmir and Ladakh separately; the panel merges them (D2). Because
these are percentages, they are combined as a POPULATION-WEIGHTED mean using Census 2011
populations, not summed.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared
RAW = SHARED / "raw" / "diglit"
DATA = SHARED / "data"

# NFHS-4 (2015-16) values of the same indicators, for the strictly PRE-WINDOW moderator.
# "Ever used the internet" is new in NFHS-5 and has no NFHS-4 counterpart, so the pre-window
# digital-adjacent measure is women's own mobile-phone ownership, which both rounds carry.
NFHS4_IND = {
    "mobile_w_2016":    "123. Women having a mobile phone that they themselves use (%)",
    "schooling_w_2016": "16. Women with 10 or more years of schooling (%)",
    "bankacct_w_2016":  "122. Women having a bank or savings account that they themselves use (%)",
}

# ---------------------------------------------------------------- NFHS-5 indicator map
NFHS_IND = {
    "diglit_w":    "18. Women who have ever used the internet (%)",
    "diglit_m":    "19. Men who have ever used the internet (%)",
    "schooling_w": "16. Women with 10 or more years of schooling (%)",
    "schooling_m": "17. Men with 10 or more years of schooling (%)",
    "everschool_w": "1. Female population age 6 years and above who ever attended school (%)",
    "mobile_w":    "123. Women having a mobile phone that they themselves use (%)",
    "bankacct_w":  "122. Women having a bank or savings account that they themselves use (%)",
}

# NFHS-5 state label -> panel state_key. Ladakh handled separately (D2 merge into J&K).
NFHS_TO_KEY = {
    "Andaman & Nicobar Islands": "ANDAMAN AND NICOBAR ISLANDS",
    "Andhra Pradesh": "ANDHRA PRADESH",
    "Arunachal Pradesh": "ARUNACHAL PRADESH",
    "Assam": "ASSAM",
    "Bihar": "BIHAR",
    "Chandigarh": "CHANDIGARH",
    "Chhattisgarh": "CHHATTISGARH",
    "NCT of Delhi": "DELHI",
    "Goa": "GOA",
    "Gujarat": "GUJARAT",
    "Haryana": "HARYANA",
    "Himachal Pradesh": "HIMACHAL PRADESH",
    "Jammu & Kashmir": "JAMMU AND KASHMIR",
    "Jharkhand": "JHARKHAND",
    "Karnataka": "KARNATAKA",
    "Kerala": "KERALA",
    "Madhya Pradesh": "MADHYA PRADESH",
    "Maharashtra": "MAHARASHTRA",
    "Manipur": "MANIPUR",
    "Meghalaya": "MEGHALAYA",
    "Mizoram": "MIZORAM",
    "Nagaland": "NAGALAND",
    "Odisha": "ODISHA",
    "Puducherry": "PUDUCHERRY",
    "Punjab": "PUNJAB",
    "Rajasthan": "RAJASTHAN",
    "Sikkim": "SIKKIM",
    "Tamil Nadu": "TAMIL NADU",
    "Telangana": "TELANGANA",
    "Tripura": "TRIPURA",
    "Uttar Pradesh": "UTTAR PRADESH",
    "Uttarakhand": "UTTARAKHAND",
    "West Bengal": "WEST BENGAL",
}

# Census 2011 populations, for the D2 J&K + Ladakh percentage merge.
# J&K total 12,541,302 (census2011.co.in) includes Ladakh; Ladakh = Leh 133,487 + Kargil 140,802.
POP_LADAKH_2011 = 133_487 + 140_802
POP_JK_TOTAL_2011 = 12_541_302
POP_JK_PROPER_2011 = POP_JK_TOTAL_2011 - POP_LADAKH_2011

# ---------------------------------------------------------------- NSS 75th round (2017-18)
# Tables 13 and 14, "All Areas / Persons" column, age 5+. 22 states only.
# Source: raw/diglit/nsso75_round_analysis.pdf, reproducing NSO Schedule 25.2 state tables.
NSS75 = {
    # state_key:                (able to operate computer %, able to use internet %)
    "ANDHRA PRADESH":           (14.4, 17.1),
    "ASSAM":                    (10.0, 16.6),
    "BIHAR":                    ( 8.0, 12.1),
    "CHHATTISGARH":             (10.8, 12.9),
    "DELHI":                    (42.8, 50.5),
    "GUJARAT":                  (22.2, 25.1),
    "HARYANA":                  (24.3, 30.9),
    "HIMACHAL PRADESH":         (24.6, 33.5),
    "JAMMU AND KASHMIR":        (12.6, 21.8),
    "JHARKHAND":                ( 8.2, 12.4),
    "KARNATAKA":                (19.3, 21.4),
    "KERALA":                   (41.5, 43.9),
    "MADHYA PRADESH":           ( 9.6, 13.5),
    "MAHARASHTRA":              (24.4, 28.8),
    "ODISHA":                   ( 8.5, 10.9),
    "PUNJAB":                   (26.6, 35.0),
    "RAJASTHAN":                (14.2, 17.1),
    "TAMIL NADU":               (27.4, 27.1),
    "TELANGANA":                (19.8, 25.0),
    "UTTARAKHAND":              (25.3, 35.6),
    "UTTAR PRADESH":            ( 9.7, 13.0),
    "WEST BENGAL":              (13.0, 14.9),
}
NSS75_ALL_INDIA = (16.5, 20.1)

# ---------------------------------------------------------------- MPCE, HCES 2022-23 (Rs./month)
# MoSPI, "Survey on Household Consumption Expenditure: Fact Sheet 2022-23", Statement 8,
# average MPCE for each State/UT. Downloaded to raw/diglit/hces_factsheet_2022_23.pdf.
#
# WHY THIS IS WORTH FETCHING. NSDP per capita is a PRODUCTION measure: corporate output books to
# the state where the firm is registered, which inflates Delhi and Maharashtra in exactly the way
# LIMITATIONS.md section 4 already documents for bank deposits (recorded at branch location).
# MPCE is a household CONSUMPTION measure from a survey of households and does not have that
# problem. For a moderator that is supposed to represent household RESOURCES, MPCE is the better
# construct and NSDP is the convenient one.
MPCE_2223 = {  # state_key: (rural Rs., urban Rs.)
    "ANDHRA PRADESH": (4870, 6782), "ARUNACHAL PRADESH": (5276, 8636),
    "ASSAM": (3432, 6136), "BIHAR": (3384, 4768), "CHHATTISGARH": (2466, 4483),
    "DELHI": (6576, 8217), "GOA": (7367, 8734), "GUJARAT": (3798, 6621),
    "HARYANA": (4859, 7911), "HIMACHAL PRADESH": (5561, 8075), "JHARKHAND": (2763, 4931),
    "KARNATAKA": (4397, 7666), "KERALA": (5924, 7078), "MADHYA PRADESH": (3113, 4987),
    "MAHARASHTRA": (4010, 6657), "MANIPUR": (4360, 4880), "MEGHALAYA": (3514, 6433),
    "MIZORAM": (5224, 7655), "NAGALAND": (4393, 7098), "ODISHA": (2950, 5187),
    "PUNJAB": (5315, 6544), "RAJASTHAN": (4263, 5913), "SIKKIM": (7731, 12105),
    "TAMIL NADU": (5310, 7630), "TELANGANA": (4802, 8158), "TRIPURA": (5206, 7405),
    "UTTARAKHAND": (4641, 7004), "UTTAR PRADESH": (3191, 5040), "WEST BENGAL": (3239, 5267),
    "ANDAMAN AND NICOBAR ISLANDS": (7332, 10268), "CHANDIGARH": (7467, 12575),
    "PUDUCHERRY": (6590, 7706),
    # D2: J&K and Ladakh are one panel unit. Census 2011 population weights, as for NFHS-5.
    "JAMMU AND KASHMIR": (
        (4296 * POP_JK_PROPER_2011 + 4035 * POP_LADAKH_2011) / POP_JK_TOTAL_2011,
        (6179 * POP_JK_PROPER_2011 + 6215 * POP_LADAKH_2011) / POP_JK_TOTAL_2011),
}

# ---------------------------------------------------------------- Census 2011 literacy (%)
# census2011.co.in / Census of India 2011. "Orissa" -> ODISHA.
# Telangana was part of undivided Andhra Pradesh in 2011 -> both get the AP value, flagged.
LIT2011 = {
    "ANDAMAN AND NICOBAR ISLANDS": 86.63, "ANDHRA PRADESH": 67.02,
    "ARUNACHAL PRADESH": 65.38, "ASSAM": 72.19, "BIHAR": 61.80,
    "CHANDIGARH": 86.05, "CHHATTISGARH": 70.28, "DELHI": 86.21,
    "GOA": 88.70, "GUJARAT": 78.03, "HARYANA": 75.55,
    "HIMACHAL PRADESH": 82.80, "JAMMU AND KASHMIR": 67.16, "JHARKHAND": 66.41,
    "KARNATAKA": 75.36, "KERALA": 94.00, "MADHYA PRADESH": 69.32,
    "MAHARASHTRA": 82.34, "MANIPUR": 76.94, "MEGHALAYA": 74.43,
    "MIZORAM": 91.33, "NAGALAND": 79.55, "ODISHA": 72.87,
    "PUDUCHERRY": 85.85, "PUNJAB": 75.84, "RAJASTHAN": 66.11,
    "SIKKIM": 81.42, "TAMIL NADU": 80.09, "TELANGANA": 67.02,
    "TRIPURA": 87.22, "UTTAR PRADESH": 67.68, "UTTARAKHAND": 78.82,
    "WEST BENGAL": 76.26,
}

# Published NFHS-5 values used to verify the mirror before we trust any of it.
SPOTCHECKS = [
    ("Bihar", "diglit_w", 20.6), ("Goa", "diglit_m", 82.9),
    ("Meghalaya", "diglit_m", 42.1), ("Sikkim", "diglit_w", 76.7),
    ("Mizoram", "diglit_w", 67.6), ("Andhra Pradesh", "diglit_w", 21.0),
    ("Tripura", "diglit_w", 22.9), ("NCT of Delhi", "diglit_m", 85.2),
]


def load_nfhs4(src: pd.DataFrame) -> pd.DataFrame:
    """NFHS-4 (2015-16) column of the same fact-sheet file. One value per state, no sector split."""
    frames = {}
    for short, label in NFHS4_IND.items():
        sub = src[src["Indicator"] == label]
        if sub.empty:
            sys.exit(f"FATAL: NFHS-4 indicator not found: {label}")
        frames[short] = pd.to_numeric(sub.set_index("state")["NFHS4"], errors="coerce").rename(short)
    return pd.concat(frames.values(), axis=1)


def load_nfhs() -> pd.DataFrame:
    src = pd.read_csv(RAW / "nfhs5_states_factsheet.csv")
    frames = {}
    for short, label in NFHS_IND.items():
        sub = src[src["Indicator"] == label]
        if sub.empty:
            sys.exit(f"FATAL: NFHS-5 indicator not found: {label}")
        f = sub.set_index("state")[["Urban", "Rural", "Total"]].apply(pd.to_numeric, errors="coerce")
        f.columns = [f"{short}_urban", f"{short}_rural", short]
        frames[short] = f
    out = pd.concat(frames.values(), axis=1)
    return out.join(load_nfhs4(src))


def assert_nfhs_spotchecks(nfhs: pd.DataFrame) -> None:
    """The mirror is flagged as un-cross-checked by its author. Verify before trusting it."""
    bad = []
    for state, col, expected in SPOTCHECKS:
        got = nfhs.loc[state, col]
        if not np.isclose(got, expected, atol=0.05):
            bad.append(f"{state}.{col}: got {got}, published {expected}")
    if bad:
        sys.exit("FATAL: NFHS-5 mirror failed verification against published figures:\n  "
                 + "\n  ".join(bad))
    print(f"  NFHS-5 mirror verified against {len(SPOTCHECKS)} independently published figures: all match")


def merge_ladakh(nfhs: pd.DataFrame) -> pd.DataFrame:
    """D2: J&K and Ladakh are one panel unit. These are percentages -> population-weight, not sum."""
    if "Ladakh" not in nfhs.index:
        print("  note: Ladakh absent from NFHS-5 file, no D2 merge needed")
        return nfhs
    wj, wl = POP_JK_PROPER_2011, POP_LADAKH_2011
    jk, lad = nfhs.loc["Jammu & Kashmir"], nfhs.loc["Ladakh"]
    combined = (jk * wj + lad * wl) / (wj + wl)
    # where Ladakh is missing an indicator, keep J&K's own value rather than propagating NaN
    combined = combined.where(lad.notna() & jk.notna(), jk)
    nfhs = nfhs.copy()
    nfhs.loc["Jammu & Kashmir"] = combined
    print(f"  D2: merged Ladakh into Jammu & Kashmir, population-weighted "
          f"({wl:,} / {wj + wl:,} = {wl / (wj + wl):.1%} Ladakh)")
    return nfhs.drop(index="Ladakh")


def main() -> int:
    print("\n" + "=" * 96)
    print("  H5 STEP 1 -- building conversion-capacity moderators")
    print("=" * 96 + "\n")

    nfhs = load_nfhs()
    print(f"  NFHS-5 loaded: {len(nfhs)} states/UTs x {len(NFHS_IND)} indicators")
    assert_nfhs_spotchecks(nfhs)
    nfhs = merge_ladakh(nfhs)

    nfhs = nfhs.rename(index=NFHS_TO_KEY)
    keep = sorted(set(NFHS_TO_KEY.values()))
    missing = [k for k in keep if k not in nfhs.index]
    if missing:
        sys.exit(f"FATAL: panel states absent from NFHS-5: {missing}")
    out = nfhs.loc[keep].copy()
    print(f"  mapped to {len(out)} panel state keys "
          f"(dropped {len(nfhs) - len(out)} units not in the panel: Lakshadweep, DNH&DD -- D1)")

    # ---- derived urban share, from NFHS-5's own urban/rural/total decomposition
    denom = out["diglit_w_urban"] - out["diglit_w_rural"]
    out["urban_share_nfhs"] = np.where(
        denom.abs() > 1e-9, (out["diglit_w"] - out["diglit_w_rural"]) / denom * 100, np.nan)
    # Chandigarh has no rural sample -- it is a wholly urban UT.
    n_imputed = int(out["urban_share_nfhs"].isna().sum())
    out["urban_share_nfhs"] = out["urban_share_nfhs"].fillna(100.0)
    out["urban_share_nfhs"] = out["urban_share_nfhs"].clip(0, 100)
    print(f"  derived urban share from NFHS-5 urban/rural split "
          f"({n_imputed} fully-urban UT set to 100)")

    # ---- MPCE, combined across sectors using the derived urban share
    u = out["urban_share_nfhs"] / 100
    mr = pd.Series({k: v[0] for k, v in MPCE_2223.items()})
    mu = pd.Series({k: v[1] for k, v in MPCE_2223.items()})
    out["mpce_rural"], out["mpce_urban"] = mr, mu
    out["mpce"] = u * mu + (1 - u) * mr
    out["ln_mpce"] = np.log(out["mpce"])
    if out["mpce"].isna().any():
        sys.exit(f"FATAL: missing MPCE for {list(out.index[out['mpce'].isna()])}")
    print(f"  HCES 2022-23 MPCE merged for {len(out)}/{len(out)} states "
          f"(rural+urban combined at each state's derived urban share)")

    # ---- change in digital-adjacent endowment, NFHS-4 (2015-16) -> NFHS-5 (2019-21)
    out["mobile_w_change"] = out["mobile_w"] - out["mobile_w_2016"]

    # ---- gender gap in digital literacy (links to H4)
    out["diglit_gap"] = out["diglit_m"] - out["diglit_w"]
    out["diglit_both"] = (out["diglit_w"] + out["diglit_m"]) / 2

    # ---- NSS 75th round, pre-window
    out["nss75_computer"] = pd.Series({k: v[0] for k, v in NSS75.items()})
    out["nss75_internet"] = pd.Series({k: v[1] for k, v in NSS75.items()})
    n75 = int(out["nss75_computer"].notna().sum())
    print(f"  NSS 75th (2017-18) merged for {n75}/{len(out)} states "
          f"(published table covers major states only)")

    # ---- Census 2011 literacy
    out["lit2011"] = pd.Series(LIT2011)
    out["lit2011_undivided_ap"] = out.index.isin(["ANDHRA PRADESH", "TELANGANA"])
    if out["lit2011"].isna().any():
        sys.exit(f"FATAL: missing Census 2011 literacy for {list(out.index[out['lit2011'].isna()])}")

    cols = ["diglit_w", "diglit_m", "diglit_both", "diglit_gap",
            "diglit_w_urban", "diglit_w_rural",
            "nss75_computer", "nss75_internet",
            "schooling_w", "schooling_m", "everschool_w", "mobile_w", "bankacct_w",
            "mobile_w_2016", "schooling_w_2016", "bankacct_w_2016", "mobile_w_change",
            "mpce", "ln_mpce", "mpce_rural", "mpce_urban",
            "lit2011", "lit2011_undivided_ap", "urban_share_nfhs"]
    out = out[cols]
    out.index.name = "state_key"

    DATA.mkdir(exist_ok=True)
    out.round(4).to_csv(DATA / "09_diglit.csv")
    print(f"\n  wrote {DATA / '09_diglit.csv'}  ({len(out)} states x {len(cols)} columns)\n")

    # ---- cross-source validation: the two independent digital-literacy measures should agree
    ok = out["nss75_computer"].notna()
    r_nss = out.loc[ok, "diglit_w"].corr(out.loc[ok, "nss75_computer"])
    r_int = out.loc[ok, "diglit_w"].corr(out.loc[ok, "nss75_internet"])
    r_mob = out["diglit_w"].corr(out["mobile_w"])
    print("  CROSS-SOURCE VALIDATION (different surveys, different years, different respondents)")
    print(f"    NFHS-5 women internet  vs  NSS 75th computer ability   r = {r_nss:.3f}  (n={ok.sum()})")
    print(f"    NFHS-5 women internet  vs  NSS 75th internet ability   r = {r_int:.3f}  (n={ok.sum()})")
    print(f"    NFHS-5 women internet  vs  NFHS-5 women mobile phone   r = {r_mob:.3f}  (n={len(out)})")

    print("\n  MODERATOR SPREAD (the H5 Gate 2 input)")
    for c in ["diglit_w", "diglit_m", "nss75_computer", "mobile_w_2016", "ln_mpce"]:
        s = out[c].dropna()
        print(f"    {c:16s} n={len(s):2d}  min={s.min():5.1f}  p25={s.quantile(.25):5.1f}  "
              f"med={s.median():5.1f}  p75={s.quantile(.75):5.1f}  max={s.max():5.1f}  sd={s.std():5.1f}")

    print("\n  extremes on the primary moderator (diglit_w):")
    srt = out["diglit_w"].sort_values()
    print("    lowest  :", ", ".join(f"{k.title()} {v:.1f}" for k, v in srt.head(4).items()))
    print("    highest :", ", ".join(f"{k.title()} {v:.1f}" for k, v in srt.tail(4).items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
