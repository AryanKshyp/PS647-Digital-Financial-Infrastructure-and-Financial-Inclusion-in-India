#!/usr/bin/env python3
"""
Parse the Report of the Technical Group on Population Projections,
"Population Projections for India and States 2011-2036" (NCP/MoHFW, July 2020).

Source PDF:
  https://nhm.gov.in/New_Updates_2018/Report_Population_Projection_2019.pdf
  saved as raw/population/Population_Projections_India_States_2011-2036_TechnicalGroup_July2020.pdf

Outputs (all in raw/population/):
  1. pop_total_annual_1july_2011_2036.csv
       Table 11 (PDF pp. 86-98): projected TOTAL population by sex, as on 1 July,
       every year 2011-2036, for India + 37 states/UTs. Units: thousands.
  2. pop_total_annual_1march_2011_2036.csv
       Table 8 (PDF pp. 47-59): same but as on 1 March. Units: thousands.
  3. pop_broad_agegroups_quinquennial.csv
       Table T-17 (24 state blocks): population by broad age group
       (18+, 0-14, 15-59, 60+) for 2011/2016/2021/2026/2031/2036. Units: thousands.
  4. pop_by_5yr_ageband_quinquennial.csv
       Table 18: projected population by 5-year age band and sex, as on 1 March,
       for 2011/2016/2021/2026/2031/2036. Units: thousands.

NOTE: the report gives ANNUAL data only for TOTAL population (tables 8-16).
Age-band / 18+ detail exists only for the quinquennial years 2011, 2016, 2021,
2026, 2031, 2036. To get adult population for every year 2018-2024 you must
interpolate the adult SHARE between quinquennial points and apply it to the
annual total. No such per-year adult figure is published; do not invent one.
"""

import csv
import os
import re
import sys

try:
    import pypdf
except ImportError:
    sys.exit("pip3 install pypdf")

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "population")
BASE = os.path.normpath(BASE)
PDF = os.path.join(
    BASE, "Population_Projections_India_States_2011-2036_TechnicalGroup_July2020.pdf"
)

# Column order of units in Tables 8 and 11 (verified from the printed column
# headers on each page of the PDF; 38 units x 3 columns = columns 2..115).
UNITS = [
    "INDIA", "JAMMU & KASHMIR (UT)", "HIMACHAL PRADESH", "PUNJAB", "HARYANA",
    "NCT OF DELHI", "RAJASTHAN", "UTTAR PRADESH", "BIHAR", "ASSAM",
    "WEST BENGAL", "JHARKHAND", "ODISHA", "CHHATTISGARH", "MADHYA PRADESH",
    "GUJARAT", "MAHARASHTRA", "ANDHRA PRADESH", "KARNATAKA", "KERALA",
    "TAMIL NADU", "CHANDIGARH", "UTTARAKHAND", "SIKKIM", "ARUNACHAL PRADESH",
    "NAGALAND", "MANIPUR", "MIZORAM", "TRIPURA", "MEGHALAYA", "DAMAN & DIU",
    "DADRA & NAGAR HAVELI", "GOA", "LAKSHADWEEP", "PUDUCHERRY",
    "ANDAMAN & NICOBAR ISLANDS", "TELANGANA", "LADAKH",
]

NUM = re.compile(r"^-?[\d,]+(?:\.\d+)?$")


def to_num(s):
    s = s.replace(",", "").strip()
    if s in ("", "-", "*"):
        return None
    return float(s) if "." in s else int(s)


def load_pages():
    r = pypdf.PdfReader(PDF)
    return [(p.extract_text() or "") for p in r.pages]


def parse_annual_table(pages, first_pdf_page, last_pdf_page):
    """Tables 8 / 11: rows are years, 3 units (9 numeric cols) per page."""
    out = {}  # (unit, year) -> (persons, male, female)
    unit_idx = 0
    for pi in range(first_pdf_page - 1, last_pdf_page):
        text = pages[pi]
        # figure out how many units on this page from the column-number line
        colline = None
        for line in text.split("\n"):
            toks = line.split()
            if len(toks) in (7, 10) and toks[0] == "1" and all(t.isdigit() for t in toks):
                colline = toks
                break
        n_units = (len(colline) - 1) // 3 if colline else 3
        page_units = UNITS[unit_idx: unit_idx + n_units]
        for line in text.split("\n"):
            toks = line.split()
            # data rows: year followed by n_units*3 numbers
            if len(toks) >= 1 + n_units * 3 and re.fullmatch(r"20\d\d", toks[0]):
                vals = toks[1: 1 + n_units * 3]
                if not all(NUM.match(v) for v in vals):
                    continue
                year = int(toks[0])
                for k, u in enumerate(page_units):
                    trio = vals[3 * k: 3 * k + 3]
                    out[(u, year)] = tuple(to_num(v) for v in trio)
        unit_idx += n_units
    return out


# T-17 blocks: (pdf page, unit name) -- verified by scanning for the
# "18 years and above" row.
def find_t17_pages(pages):
    res = []
    for i, x in enumerate(pages):
        if "18 years and above" in x:
            lines = [l.strip() for l in x.split("\n") if l.strip()]
            name = None
            for j, l in enumerate(lines):
                if "Projected Population Characteristics" in l:
                    name = lines[j + 1]
                    break
            res.append((i + 1, name))
    return res


T17_ROWS = {
    "18 years and above": "pop_18plus",
    "0-14": "pop_0_14",
    "15-59": "pop_15_59",
    "60+": "pop_60plus",
}
QYEARS = [2011, 2016, 2021, 2026, 2031, 2036]


def parse_t17(pages):
    rows = []
    for pg, unit in find_t17_pages(pages):
        text = pages[pg - 1]
        lines = [l.strip() for l in text.split("\n")]
        # restrict to the block between "Population by broad age" and "Proportion"
        try:
            a = next(i for i, l in enumerate(lines) if l.startswith("Population by broad age"))
            b = next(i for i, l in enumerate(lines) if l.startswith("Proportion"))
        except StopIteration:
            print("  !! could not locate broad-age block on page", pg)
            continue
        vals = {}
        # also grab Total / Male / Female from the top Population (000') block
        for l in lines[:a]:
            toks = l.split()
            if toks and toks[0] in ("Total", "Male", "Female") and len(toks) == 7:
                if all(NUM.match(t) for t in toks[1:]):
                    vals["pop_" + toks[0].lower()] = [to_num(t) for t in toks[1:]]
            # Rajasthan: the Total row values are printed on the "Population (000')"
            # header line instead of on the "Total" line.
            if l.startswith("Population (000')") and "pop_total" not in vals:
                toks = l.split()[2:]
                if len(toks) == 6 and all(NUM.match(t) for t in toks):
                    vals["pop_total"] = [to_num(t) for t in toks]
        for l in lines[a:b]:
            for key, name in T17_ROWS.items():
                if l.startswith(key):
                    toks = l[len(key):].split()
                    if len(toks) == 6 and all(NUM.match(t) for t in toks):
                        vals[name] = [to_num(t) for t in toks]
        for k, y in enumerate(QYEARS):
            rec = {"unit": unit, "year": y, "pdf_page": pg}
            for name in ["pop_total", "pop_male", "pop_female", "pop_18plus",
                         "pop_0_14", "pop_15_59", "pop_60plus"]:
                rec[name] = vals.get(name, [None] * 6)[k]
            rows.append(rec)
    return rows


AGE_BANDS = ["0-1", "0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34",
             "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69",
             "70-74", "75-79", "80+", "Total"]


def parse_table18(pages):
    """Table 18: two half-tables (2011/2016/2021 then 2026/2031/2036).

    Row labels and their numbers are often on different text lines, so walk a
    token stream anchored on the known age-band label sequence instead.
    """
    rows = []
    for pg, unit in find_t17_pages(pages):
        # locate the Table-18 page in this state block
        start = None
        for cand in range(pg, pg + 3):
            if "TABLE-18" in pages[cand] or "TABLE - 18" in pages[cand]:
                start = cand
                break
        if start is None:
            print("  !! no TABLE-18 for", unit)
            continue
        # region = Table-18 page plus following pages until TABLE-19 appears
        region = [pages[start]]
        src_pages = [start + 1]
        j = start + 1
        while j < len(pages) and "TABLE-19" not in pages[j] and "TABLE - 19" not in pages[j]:
            region.append(pages[j])
            src_pages.append(j + 1)
            j += 1
        toks = " ".join(region).split()

        i = 0
        for half in (0, 1):
            yrs = QYEARS[3 * half: 3 * half + 3]
            for band in AGE_BANDS:
                # find next occurrence of this band label
                while i < len(toks) and toks[i] != band:
                    i += 1
                if i >= len(toks):
                    print(f"  !! {unit} half{half} missing band {band}")
                    break
                i += 1
                nums = []
                while i < len(toks) and len(nums) < 9:
                    if NUM.match(toks[i]):
                        nums.append(toks[i])
                    i += 1
                if len(nums) != 9:
                    print(f"  !! {unit} {band} half{half}: got {len(nums)} numbers")
                    break
                for k, y in enumerate(yrs):
                    rows.append({
                        "unit": unit, "year": y, "age_band": band,
                        "persons": to_num(nums[3 * k]),
                        "male": to_num(nums[3 * k + 1]),
                        "female": to_num(nums[3 * k + 2]),
                        "pdf_page": src_pages[0],
                    })
    return rows


def parse_table20(pages):
    """Table 20: projected population by sex for SINGLE ages 5 to 23,
    as on 1 March, for 2011/2016/2021/2026/2031/2036."""
    rows = []
    for pg, unit in find_t17_pages(pages):
        start = None
        for cand in range(pg, pg + 5):
            if "TABLE-20" in pages[cand] or "TABLE - 20" in pages[cand]:
                start = cand
                break
        if start is None:
            print("  !! no TABLE-20 for", unit)
            continue
        region, src = [], start + 1
        j = start
        while j < len(pages):
            txt = pages[j]
            if j > start and ("T-17" in txt or "TABLE-21" in txt or "APPENDIX" in txt
                              or "TABLE-20" in txt):
                break
            # drop the table title line: it contains the literal tokens "5" and "23"
            keep = [l for l in txt.split("\n") if "Ages 5 To 23" not in l
                    and "Ages 5 to 23" not in l]
            region.append("\n".join(keep))
            j += 1
        toks = " ".join(region).split()
        i = 0
        ok = True
        for half in (0, 1):
            yrs = QYEARS[3 * half: 3 * half + 3]
            for age in range(5, 24):
                lbl = str(age)
                while i < len(toks) and toks[i] != lbl:
                    i += 1
                if i >= len(toks):
                    print(f"  !! {unit} T20 half{half} age {age} not found")
                    ok = False
                    break
                i += 1
                nums = []
                while i < len(toks) and len(nums) < 9:
                    if NUM.match(toks[i]):
                        nums.append(toks[i])
                    i += 1
                if len(nums) != 9:
                    ok = False
                    break
                for k, y in enumerate(yrs):
                    rows.append({"unit": unit, "year": y, "age": age,
                                 "persons": to_num(nums[3 * k]),
                                 "male": to_num(nums[3 * k + 1]),
                                 "female": to_num(nums[3 * k + 2]),
                                 "pdf_page": src})
            if not ok:
                break
    return rows


def write_csv(path, fields, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote", path, len(rows), "rows")


def main():
    pages = load_pages()
    print("pages:", len(pages))

    for label, (p0, p1), fname in [
        ("Table 11 (1 July)", (86, 98), "pop_total_annual_1july_2011_2036.csv"),
        ("Table 8 (1 March)", (47, 59), "pop_total_annual_1march_2011_2036.csv"),
        ("Table 14 (1 October)", (125, 137), "pop_total_annual_1october_2011_2036.csv"),
    ]:
        d = parse_annual_table(pages, p0, p1)
        rows = [{"unit": u, "year": y, "persons_000": v[0],
                 "male_000": v[1], "female_000": v[2]}
                for (u, y), v in sorted(d.items(), key=lambda kv: (UNITS.index(kv[0][0]), kv[0][1]))]
        print(label, "->", len(rows), "rows,", len({u for u, _ in d}), "units")
        write_csv(os.path.join(BASE, fname),
                  ["unit", "year", "persons_000", "male_000", "female_000"], rows)

    t18 = parse_table18(pages)
    t20 = parse_table20(pages)
    write_csv(os.path.join(BASE, "pop_by_5yr_ageband_quinquennial.csv"),
              ["unit", "year", "age_band", "persons", "male", "female", "pdf_page"],
              t18)
    write_csv(os.path.join(BASE, "pop_by_single_age_5to23_quinquennial.csv"),
              ["unit", "year", "age", "persons", "male", "female", "pdf_page"],
              t20)

    t17 = parse_t17(pages)
    # NCT OF DELHI: the "18 years and above" row is printed BLANK in the source
    # PDF (p.185 of the report / PDF p.189). Reconstruct it exactly as
    #   18+ = Total - (0-4 band, Table 18) - sum(single ages 5..17, Table 20)
    # This identity reproduces the published 18+ figure exactly for every other
    # state, so the reconstruction is not an estimate.
    b04 = {(r["unit"], r["year"]): r["persons"] for r in t18 if r["age_band"] == "0-4"}
    age = {(r["unit"], r["year"], r["age"]): r["persons"] for r in t20}
    for r in t17:
        if r["pop_18plus"] is None and r["pop_total"] is not None:
            k = (r["unit"], r["year"])
            try:
                s = sum(age[(r["unit"], r["year"], a)] for a in range(5, 18))
                r["pop_18plus"] = r["pop_total"] - b04[k] - s
                r["pop_18plus_source"] = "derived_T18_T20 (row blank in PDF)"
            except KeyError:
                pass
        else:
            r["pop_18plus_source"] = "published T-17"
    write_csv(os.path.join(BASE, "pop_broad_agegroups_quinquennial.csv"),
              ["unit", "year", "pop_total", "pop_male", "pop_female",
               "pop_18plus", "pop_18plus_source", "pop_0_14", "pop_15_59",
               "pop_60plus", "pdf_page"],
              t17)


if __name__ == "__main__":
    main()
