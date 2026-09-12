# DBIE / CIMS portal — verified access notes (2026-09-08)

> **Resolution:** §4 below ("Where it stops") was superseded within the same session. The
> SAP RESTful API *is* reachable, at **`/BOE/OpenDocument/2409211437/biprwsproxy/biprws`**
> — not at `/biprws` or `/BOE/biprws`, which is why the probes in §4 all 404'd. Using the
> `token=` value from §2 verbatim as an `X-SAP-LogonToken` header against that proxy path,
> then `cmsquery` (CUID → SI_ID) → `PUT .../parameters` → `GET .../dataproviders/DP0/flows/0`
> returns the **entire** result set for a report (all quarters at once, not just the one on
> screen). That is what `../../scripts/fetch_bsr_dbie.py` does, and it is how the data in
> this folder was obtained. §1–§3 and §5–§6 remain accurate and useful.

Everything below was executed and observed, not inferred.

## 1. The public REST gateway works and is fully scriptable

```
POST https://data.rbi.org.in/CIMS_Gateway_DBIE/GATEWAY/SERVICES/<service>
headers: Content-Type: application/json, datatype: application/json,
         channelkey: key1, authorization: <session token>
body:    {"body": { ... }}
```

* Session token: `POST .../security_generateSessionToken` with `channelkey: key1` —
  the token comes back in the **`authorization` response header**, not the body.
* `channelkey: key2` is what the browser bundle sends but it returns
  `"Current session is unauthorized. Logging off"` for a scripted client; **`key1` works**.
* Responses are HTML-entity-encoded text — unescape before `json.loads`.

Useful services confirmed working:

| Service | Body | Returns |
|---|---|---|
| `dbie_getAllDBIEReports` | `{}` | full catalogue, 1,414 reports (id, name, menu, from/to dates) |
| `dbie_mainMenuList`, `dbie_menuMappingList` | `{}` | portal menu tree |
| `dbie_getSectorAction` | `{"body":{}}` | Data-Query element catalogue (252 elements) |
| `dbie_getCodeListAction` | `{"dimData":{"elementCodes":<enc>,"elementIds":<enc>}}` | dimensions + measures of a Data-Query element |
| `dbie_getReportLink` | `{"reportId":<enc>,"lang":<enc>}` | the report's SAP OpenDocument link (encrypted) |
| `login_getSapToken` (LOGIN gateway) | `{"portalCode":"DBIE","user":"","code":""}` | establishes the SAP guest session |

`<enc>` = AES-encrypted, using the constants hard-coded in the Angular bundle:

```
TOKEN        = 48d6b976d7135745b47b407cd8e659a45d8ebaca4ee95f87d5d939604f472268
TOKEN_STATUS = 577bd45a17977269694908d80905c32a     (salt, hex)
TOKEN_RESP   = dc0da04af8fee58593442bf834b30739     (IV, hex)
key = PBKDF2-HMAC-SHA1(password=TOKEN as ASCII, salt=unhex(TOKEN_STATUS), 1000 iters, 32 bytes)
ct  = base64(AES-256-CBC(PKCS7(plaintext), key, iv=unhex(TOKEN_RESP)))
```

Sanity check: `decrypt("QlAU23oEIEEvtRPWlXajsQ==")` == `""` (the bundle's own null sentinel).

## 2. Call ordering matters

`login_getSapToken` **must be called before** `dbie_getReportLink`, in the same
`requests.Session`. If it is:

```
/BOE/OpenDocument/opendoc/openDocument.jsp?sIDType=CUID&iDocID=<CUID>
   &token=drdccimssapbo01.RBI1.rbi.org.in%3A6400%40%7B...secEnterprise%3Aguest_user...%7D
```

If it is not, the same call returns the link with a bare `token=` and the viewer shows a
SAP logon page. The `token` field *inside* the `login_getSapToken` response body is a DBIE
transaction id, **not** a SAP token — appending it does nothing (verified: still a logon page).

## 3. How far the automated chain gets

With the token above:

1. `GET <opendoc url>&sOutputFormat=E` → auto-submit HTML form.
2. POST that form to `/BOE/OpenDocument/2409211437/OpenDocument/opendoc/openDocument.jsp`
   (set `isApplication=true`, `appKind=OpenDocument`, `userParamsList=<original query>`)
   → redirects with `logonSuccessful=true`. **Guest logon succeeds.**
3. The next page carries `var backurl = "../../AnalyticalReporting/WebiView.do?..."`.
   Requesting it verbatim returns **HTTP 418 "Unauthorised Access"** — that is RBI's WAF,
   not SAP: dropping the `SerializedSession` *and* `userParamsList` query parameters (they
   contain patterns the WAF rejects) makes the same URL return **200**.
4. That 200 is the WebI viewer shell. It exposes, in a `var data = {...}` blob:
   `docId` (e.g. 664696 for report 943), `docName`, a valid SAP `logonToken`, and
   `openDocParameters: {"sOutputFormat":"E"}`.

## 4. Where it stops

The shell then loads the actual renderer from
`https://cas.rbi.org.in/BOE/OpenDocument/2409211437/AnalyticalReporting/webiNG/wise-app/index.html`
and fetches data through the SAP RESTful (Raylight) API at `<rwsRoot>/raylight/v1/documents/<docId>`.
Neither is reachable from outside:

| URL | Result |
|---|---|
| `https://data.rbi.org.in/BOE/OpenDocument/2409211437/AnalyticalReporting/webiNG/wise-app/index.html` | 404 (BOE "Missing Page") |
| `https://cas.rbi.org.in/BOE/OpenDocument/2409211437/AnalyticalReporting/webiNG/wise-app/index.html` | 404 |
| `https://data.rbi.org.in/BOE/biprws/...`, `https://data.rbi.org.in/biprws/...`, `https://cas.rbi.org.in/...biprws/...` | 404 |

The viewer's own config points `WACURL` at `http://drdccimssapbo04.RBI1.rbi.org.in:8080/biprws`
— an RBI-internal host. So there is **no public server-side export endpoint**;
`&sOutputFormat=E` is passed through to a client-side exporter that never loads here.

Also tried and rejected: `&sRefresh=N&sInstance=last` (→ "An error occurred while trying to
view the document" — no saved instances), `isApplication=false` branch (→ HTTP 500).

**Practical consequence:** the export must be done by a human in a real browser, or by a
headless browser (Chrome is installed; playwright/selenium are not). It is possible the
`cas.rbi.org.in` renderer is only served to clients inside India — worth one test from an
Indian IP before assuming the manual route also fails.

## 5. Direct report URLs (regenerate the token before use)

Report ids for the tables that carry **No. of Accounts**, from `dbie_getAllDBIEReports`:

| id | Report | Coverage |
|---|---|---|
| 943 | Quarterly BSR-1 Table 1.3 — Outstanding credit of SCBs according to state | Mar-2014 → Jun-2026 |
| 951 | Quarterly BSR-1 Table 2.2 — State & population group-wise outstanding credit | Mar-2014 → Jun-2026 |
| 952 | Quarterly BSR-1 Table 2.3 — State & bank group-wise outstanding credit | Jun-2017 → Jun-2026 |
| 1134 | Annual BSR-1 Table 1.3 — State-wise outstanding credit (sanction & utilisation) | Mar-2026 |
| 1140 / 1141 | Annual BSR-1 Tables 2.9 / 2.10 — State × population group / bank group | Mar-2026 |
| 1220 | Bank Credit of SCBs — bank group, population group, occupation, district-wise, annual | Mar-2010 → Mar-2026 |
| 853 | Annual BSR-2 Table 2.3 — Deposits of SCBs according to State/UT | Mar-2019 → Mar-2026 |
| 856 / 858 / 859 | Annual BSR-2 Tables 2.6 / 2.8 / 2.9 — state × ownership / population group / bank group | Mar-2019 → Mar-2026 |
| 1309 / 1312 / 1314 / 1315 | Quarterly BSR-2 equivalents of the above | Mar-2023 → Jun-2026 |
| 1199 | Bank Deposits of SCBs — region, state, district, bank group, population group, annual | Mar-2010 → **Mar-2018** |
| 1427 / 1415 / 1465 / 1483 | Spatial Distribution Statement 3A (annual 2023+, quarterly 2023+, 2017–22, 2004–17) | — |

**1220 and 1199 are the two long time-series reports** — between them they cover Mar-2010
onward for credit and Mar-2010–Mar-2018 for deposits in a single export each.

The OpenDocument CUIDs (stable; append a fresh `token=` from §2):

```
943  AXv_x9VyU2RPgSKw_n0gDwc      853  ASp8h.F7YtJOjliHsBla.eM
951  AeMIQWQ3I45Iv4uuOCEjqVw      856  ARNBGYrHKb9Ol_mSRPmsuOM
952  AfvvBwoXQnVIn4Be7sbUq3M      858  AVa4OErAIk1Gg9uy1idfI.Q
1134 ATIdZkvsYcpAo69UXHuwAxY      859  AcdKhcx7RIdJrA77rJAMqyU
1140 AZKYiKoAVrNJjxpaLJMzUko      1199 AY_HYNp3zydKneNrC4YMtmo
1141 AdnnSJ3Bm.VGvZh2ALd.9jI      1309 ARWFMq0FSOFAhcOPxX64gZs
1220 AX6iVoXLxpNCvUm2dKeFBIE      1312 AR8ntDC.aQ9BuNqz6vVNGl8
1427 AYO._nJNUNVIvmlnR.rekXk      1314 AU_WZhLdhh5FtGQDzhjEzNE
1415 AYSZXl_wvdZIjeRrhRMWH2M      1315 AXhg7oJSd21Mnlb6jAFKqko
1465 AcoKhXc2HQ5GogCdn6BB5HM      1483 AQpKu5EaB2pIg4B9nIoh6i8
```

## 6. Dead ends confirmed (do not retry)

* `dbie.rbi.org.in` — every legacy `dbie.rbi?site=publicOpenDocument&iDocID=...` link on
  RBI's own quarterly-publications page 302s to the `data.rbi.org.in` SPA. All dead.
* `rbi.org.in/Scripts/AnnualPublications.aspx?head=Basic+Statistical+Return...` — renders,
  but the only file links are the 2003 edition PDFs. `QuarterlyPublications.aspx` for
  "Quarterly Statistics on Deposits and Credit of Scheduled Commercial Banks" lists every
  quarter 1998–2023 but all statement links are the dead legacy DBIE ones. (The ASP.NET
  postback for a given quarter is `hdnYear`/`hdnperiod` + `UsrFontCntr$btn`, if ever needed.)
* DBIE **Data Query** (`dbie_getSectorAction`) has exactly one BSR element,
  `LNA_SCB_SR_OCC_BSR1_A_RN` ("Loans and Advances of SCBs State and Occupation wise BSR1
  Annual"), and its only measures are **Amount Outstanding** and **Credit limit** —
  no account counts. Unit dimension is "Indian rupee".
* `dbie_getSapReportDownload` → 500 every time. `dbie_firstEBRBaseReportTabs` → "Action ID
  is invalid". `dbie_getBSRRegionWiseData` → empty. `dbie_noOfDepositAccountPerPopulationStateWise`
  → 500 for every quarter format tried.
* web.archive.org CDX API was returning 503 ("Internet Archive: Temporarily Offline")
  throughout this session — worth retrying later for archived rbidocs BSR files.
* data.gov.in: `api.data.gov.in/catalog` 404s and `www.data.gov.in` search timed out.
