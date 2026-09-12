# Manual steps — BSR deposit & credit ACCOUNT COUNTS

> **SUPERSEDED — you almost certainly do not need this.** The extraction was subsequently
> automated end-to-end via the SAP BI RESTful proxy
> (`/BOE/OpenDocument/2409211437/biprwsproxy/biprws`), and FY2018–FY2024 account counts for
> both deposits and credit are already on disk. Run `../../scripts/fetch_bsr_dbie.py` to
> re-pull, read `README_SOURCES.md` for what was obtained, and `DBIE_ACCESS_NOTES.md` for
> the protocol. Keep this file only as a fallback if RBI changes the portal.

This was written when the last hop still looked like it needed a human clicking Export.

**Why we need it:** number of deposit accounts and number of credit accounts per state
are the two numerators for **DV1 (Access)**. Deposits/credit *amounts* (already collected)
only give DV2 (Usage). Without these, H1 cannot be tested.

---

## Fastest route — skip the portal navigation

From the project root:

```bash
cd scripts
python3 dbie_report_url.py
```

It prints a ready-to-open URL per report. **Open it immediately** — the SAP logon token
expires within minutes. Re-run the script for a fresh link any time.

Each printed URL must end in `...%2CUP%7D`. If it ends in anything else (e.g. a trailing
`59nqh0178…`), the token is corrupted and the viewer will show a logon page — re-run the
script. If it ends in a bare `&token=`, the SAP logon step failed; re-run it too.

Then in the report viewer: **Export** (toolbar, disk/arrow icon) → **Excel** → save into
`raw/bsr_accounts/`.

---

## The three reports to export

| # | Report | Frequency | Coverage | What to take |
|---|---|---|---|---|
| **951** | BSR-1 Table 2.2 — State & population group-wise outstanding credit | Quarterly | Mar-2014 → Jun-2026 | **March** quarters 2018–2024 → *credit accounts* |
| **853** | BSR-2 Table 2.3 — Deposits of SCBs by State/UT | Annual | Mar-2019 → Mar-2026 | 2019–2024 → *deposit accounts* |
| **1199** | BSR-2 Time Series — Bank Deposits of SCBs by Region/State/District/Bank group/Pop group | Annual | Mar-2010 → **Mar-2018** | 2018 only → fills the gap 853 leaves |

⚠️ **853 starts at March 2019**, so it does not cover FY2018. That is the only reason
1199 is on the list. If 1199 turns out not to carry account counts, alternatives:
report **943** (BSR-1 Table 1.3, quarterly 2014→2026) for credit, and for deposits either
accept FY2019–FY2024 (6 years) or find the March-2018 BSR-2 volume separately.

Each of these is a *single* export covering all years — three exports total, not one per year.

Suggested filenames:
```
raw/bsr_accounts/bsr1_t2.2_state_credit_quarterly.xlsx
raw/bsr_accounts/bsr2_t2.3_state_deposits_annual.xlsx
raw/bsr_accounts/bsr2_timeseries_state_deposits_2010_2018.xlsx
```

---

## If you prefer clicking through the portal

1. Go to **https://data.rbi.org.in** → **Reports**
2. Navigate the menu tree (values are exactly as they appear in the portal):

| Report | Menu | Section | Sub-section |
|---|---|---|---|
| 951 | Quarterly Basic Statistical Return (BSR) | Quarterly BSR-1 : Outstanding Credit of Scheduled Commercial Banks | Section 2: Outstanding Credit |
| 853 | Annual Basic Statistical Return (BSR)-2 | Basic Statistical Return (BSR)- 2 - Deposits with SCBs | Section 2: Deposits |
| 1199 | Annual Basic Statistical Return (BSR)-2 | Time Series | Time Series Detailed Data |

3. Open the report, set the date range to cover **31-Mar-2018 … 31-Mar-2024**, Export → Excel.

---

## What to check after exporting

- The tables report **No. of Accounts** *and* **Amount Outstanding**. We want the **account
  count** column — the amount column duplicates data we already have from the Handbook.
- BSR-1 credit is reported by **place of sanction** and **place of utilisation**. Pick one
  and stay consistent; note which in `data_fetching.md`. (Place of *utilisation* is the
  better match for a state-level inclusion story.)
- Check whether the state list splits **Ladakh** from J&K and **Daman/Diu** from DNH, then
  apply the §3 merge rule in `data_fetching.md`.
- Confirm the year labels: BSR stocks are as at **31 March**, matching the banking-year
  convention in §6 of `data_fetching.md`.

---

## Why this can't be fully scripted

Reverse-engineered from the portal's Angular bundle and reproduced in
`scripts/dbie_client.py` — all of this **is** automated:

- old `dbie.rbi.org.in` is dead; the live portal is **`data.rbi.org.in`**
- gateway `POST /CIMS_Gateway_DBIE/GATEWAY/SERVICES/<service>`, headers
  `channelkey: key2`, `datatype: application/json`, body `{"body":{...}}`
- session token from `security_generateSessionToken`, returned in the **`authorization`
  response header**
- `dbie_getAllDBIEReports` → full 1,414-report catalogue (saved reasoning behind the ids above)
- `dbie_getReportLink` → the report's SAP link. **Both `reportId` and `lang` must be
  AES-encrypted** or the service returns a generic 500. Cipher (constants hard-coded in the JS):
  `key = PBKDF2(TOKEN, salt=unhex(TOKEN_STATUS), 32B, 1000 iters, HMAC-SHA1)`,
  `ct = base64(AES-256-CBC(pkcs7(plain), key, iv=unhex(TOKEN_RESPONSE)))`
- `login_getSapToken` (on the LOGIN gateway) → authenticates the session as `guest_user`

**Ordering gotcha:** `login_getSapToken` must be called *before* `dbie_getReportLink`.
Once it has, the returned `sapLink` already carries a full SAP token in its `token=`
parameter — nothing should be appended to it. Call `getReportLink` first and the link
comes back ending in a bare `token=`, which renders a logon page. (The `token` field in
the `login_getSapToken` response is a DBIE session id, *not* a SAP token; appending it
turns a valid URL into an invalid one.)

**The blocker:** reports are SAP BusinessObjects WebI documents. Only `/BOE/` (the
interactive viewer) is exposed through RBI's reverse proxy — the SAP REST API `/biprws/`
returns 404 for every path. So there is no server-side export endpoint to call; the
Export button in the viewer is the only way out. Driving that would need a scripted
headless browser (Chrome is present, but neither playwright nor selenium is installed).
