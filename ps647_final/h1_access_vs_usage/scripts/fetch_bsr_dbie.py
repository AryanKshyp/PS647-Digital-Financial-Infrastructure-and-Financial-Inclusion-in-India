#!/usr/bin/env python3
"""
Pull BSR (Basic Statistical Return) publication tables from RBI's DBIE portal
(data.rbi.org.in) via its public JSON gateway + the SAP BusinessObjects
RESTful "raylight" web service that sits behind it.

Why this exists
---------------
The state-wise NUMBER OF CREDIT ACCOUNTS (BSR-1) and NUMBER OF DEPOSIT
ACCOUNTS (BSR-2) are published ONLY as DBIE web tables. There is no static
.xlsx/.pdf anywhere on rbi.org.in / rbidocs.rbi.org.in that carries them
(the annual BSR press releases are text-only and just point at DBIE; the
Handbook of Statistics on Indian States and the Economic Survey statistical
appendix carry amounts, not account counts).

How the access works (no credentials needed, all public endpoints)
------------------------------------------------------------------
1. POST /CIMS_Gateway_DBIE/GATEWAY/SERVICES/security_generateSessionToken
   (header channelkey: key2)  -> `authorization` response header = session id.
2. POST /CIMS_Gateway_LOGIN/GATEWAY/SERVICES/login_getSapToken
   -> makes the gateway mint a *trusted* SAP BOE logon token for the
      anonymous portal user, bound to this session.
3. POST /CIMS_Gateway_DBIE/GATEWAY/SERVICES/dbie_getReportLink
   body {reportId: <AES-encrypted id>, lang: <AES-encrypted "en">}
   -> AES-encrypted `sapLink` = /BOE/OpenDocument/opendoc/openDocument.jsp
      ?sIDType=CUID&iDocID=<CUID>&token=<SAP logon token>
   The AES key is derived exactly as the Angular SPA does (constants below).
4. The `token` from that link is a valid `X-SAP-LogonToken` for
   /BOE/OpenDocument/2409211437/biprwsproxy/biprws  (the BI RESTful WS).
5. cmsquery maps CUID -> SI_ID; then
   PUT  /raylight/v1/documents/<id>/parameters   (refreshes all providers)
   GET  /raylight/v1/documents/<id>/dataproviders/DP0/flows/0
   returns the FULL underlying result set (all periods, all states) as JSON,
   which is far more useful than the on-screen report (the report itself is
   filtered to one quarter by an input control).

Outputs land in raw/bsr_accounts/.
"""

import base64
import hashlib
import html
import json
import os
import sys
from urllib.parse import unquote

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# --- AES params lifted from the DBIE Angular bundle (main.*.js, class Ll) ---
_TOKEN = "48d6b976d7135745b47b407cd8e659a45d8ebaca4ee95f87d5d939604f472268"
_TOKEN_STATUS = "577bd45a17977269694908d80905c32a"
_TOKEN_RESP = "dc0da04af8fee58593442bf834b30739"
_KEY = hashlib.pbkdf2_hmac("sha1", _TOKEN.encode(), bytes.fromhex(_TOKEN_STATUS), 1000, 32)
_IV = bytes.fromhex(_TOKEN_RESP)

HOST = "https://data.rbi.org.in"
RWS = HOST + "/BOE/OpenDocument/2409211437/biprwsproxy/biprws"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")


def enc(s):
    c = AES.new(_KEY, AES.MODE_CBC, _IV)
    return base64.b64encode(c.encrypt(pad(str(s).encode(), 16))).decode()


def dec(b64):
    c = AES.new(_KEY, AES.MODE_CBC, _IV)
    return unpad(c.decrypt(base64.b64decode(b64)), 16).decode("utf-8", "replace")


class Dbie:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Origin": HOST, "Referer": HOST + "/"})
        self.sid = None
        self.sap = None

    def _gw(self, svc, body=None, gw="CIMS_Gateway_DBIE"):
        r = self.s.post(f"{HOST}/{gw}/GATEWAY/SERVICES/{svc}",
                        headers={"Content-Type": "application/json",
                                 "channelkey": "key2",
                                 "datatype": "application/json",
                                 **({"authorization": self.sid} if self.sid else {})},
                        data=json.dumps({"body": body or {}}), timeout=180)
        return json.loads(html.unescape(r.text).replace("\xa0", " "))

    def login(self):
        r = self.s.post(f"{HOST}/CIMS_Gateway_DBIE/GATEWAY/SERVICES/security_generateSessionToken",
                        headers={"Content-Type": "application/json", "channelkey": "key2",
                                 "datatype": "application/json"},
                        data=json.dumps({"body": {}}), timeout=90)
        self.sid = r.headers["authorization"]
        self._gw("login_getSapToken", {"portalCode": "DBIE", "user": "", "code": ""},
                 gw="CIMS_Gateway_LOGIN")
        return self.sid

    def all_reports(self):
        return self._gw("dbie_getAllDBIEReports")["body"]["response"]

    def report_cuid_and_token(self, report_id):
        """DBIE reportId -> (SAP CUID, SAP logon token). Refreshes self.sap."""
        r = self._gw("dbie_getReportLink", {"reportId": enc(report_id), "lang": enc("en")})
        link = dec(r["body"]["sapLink"])
        cuid = link.split("iDocID=")[1].split("&")[0]
        self.sap = unquote(link.split("token=")[1])
        return cuid, self.sap

    # ---- SAP BI RESTful web service ----
    def _rws(self, method, path, body=None, accept="application/json"):
        h = {"Accept": accept, "X-SAP-LogonToken": self.sap}
        if body is not None:
            h["Content-Type"] = "application/json"
        r = self.s.request(method, RWS + path, headers=h,
                           data=json.dumps(body) if body is not None else None, timeout=600)
        return r

    def cuid_to_docid(self, cuid):
        q = {"query": f"SELECT SI_ID, SI_NAME, SI_CUID FROM CI_INFOOBJECTS WHERE SI_CUID='{cuid}'"}
        e = self._rws("POST", "/v1/cmsquery", q).json()["entries"]
        return e[0]["SI_ID"], e[0]["SI_NAME"]

    def fetch_flow(self, doc_id, dp=None, flow=0):
        """Refresh the document then return (columns, rows) of one data provider flow.

        With dp=None the data provider carrying the most rows is used (the
        detail query; the others are little 'Total'/'Amt' helper queries).
        """
        self._rws("PUT", f"/raylight/v1/documents/{doc_id}/parameters",
                  {"parameters": {"parameter": []}})
        if dp is None:
            dps = self._rws("GET", f"/raylight/v1/documents/{doc_id}/dataproviders") \
                      .json()["dataproviders"]["dataprovider"]
            dp = max(dps, key=lambda p: int(p.get("rowCount") or 0))["id"]
        r = self._rws("GET", f"/raylight/v1/documents/{doc_id}/dataproviders/{dp}/flows/{flow}")
        r.raise_for_status()
        d = r.json()["flow"]
        cols = [m["$"] for m in d["metadata"]["value"]]
        rows = [x["value"] for x in d["row"]]
        return cols, rows

    def export(self, doc_id, fmt="xlsx"):
        mt = {"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
              "pdf": "application/pdf"}[fmt]
        self._rws("PUT", f"/raylight/v1/documents/{doc_id}/parameters",
                  {"parameters": {"parameter": []}})
        return self._rws("GET", f"/raylight/v1/documents/{doc_id}", accept=mt).content


# DBIE reportId -> output basename
TARGETS = {
    943:  ("bsr1_quarterly_state_credit_excl_rrb",
           "Quarterly BSR-1 Table 1.3 - Outstanding credit of SCBs according to state (excl. RRBs)"),
    1134: ("bsr1_annual_state_credit_incl_rrb",
           "Annual BSR-1 Table 1.3 - State-wise outstanding credit of SCBs (incl. RRBs)"),
    853:  ("bsr2_annual_state_deposits_incl_rrb",
           "Annual BSR-2 Table 2.3 - Deposits of SCBs according to State/UT (incl. RRBs)"),
    1309: ("bsr2_quarterly_state_deposits_excl_rrb",
           "Quarterly BSR-2 Table 2.3 - Deposits of SCBs according to State/UT (excl. RRBs)"),
}

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))),
                   "raw", "bsr_accounts")


def main(ids=None):
    os.makedirs(OUT, exist_ok=True)
    d = Dbie()
    d.login()
    manifest = {}
    for rid in (ids or TARGETS):
        base, desc = TARGETS[rid]
        cuid, _ = d.report_cuid_and_token(rid)
        doc_id, name = d.cuid_to_docid(cuid)
        cols, rows = d.fetch_flow(doc_id)
        json.dump({"reportId": rid, "cuid": cuid, "docId": doc_id, "docName": name,
                   "description": desc, "columns": cols, "rows": rows},
                  open(os.path.join(OUT, base + "_raw.json"), "w"))
        import csv
        with open(os.path.join(OUT, base + "_long.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        manifest[rid] = {"description": desc, "cuid": cuid, "docId": doc_id,
                         "docName": name, "columns": cols, "n_rows": len(rows)}
        print(f"{rid}: {name} -> {len(rows)} rows, cols={cols}")
    json.dump(manifest, open(os.path.join(OUT, "SOURCE_MANIFEST.json"), "w"), indent=1)


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]] or None)
