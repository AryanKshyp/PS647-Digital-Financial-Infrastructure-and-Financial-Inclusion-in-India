#!/usr/bin/env python3
"""
Print a ready-to-open browser URL for a DBIE report, so you can skip the portal
navigation and land straight on the report viewer.

    python3 scripts/dbie_report_url.py            # the reports we need for BSR
    python3 scripts/dbie_report_url.py 951 853    # any report ids

Paste the printed URL into a browser. The SAP logon token is minted fresh on each
run and expires quickly, so generate the link immediately before opening it.
Once the report loads, use the viewer's export control to save XLSX/CSV.

Report ids come from `dbie_getAllDBIEReports` (see scripts/dbie_client.py).
"""

import html
import json
import sys

from dbie_client import DBIE, encrypt, decrypt

LOGIN = "https://data.rbi.org.in/CIMS_Gateway_LOGIN/GATEWAY/SERVICES"
ORIGIN = "https://data.rbi.org.in"

# What we actually need for the Access variable (deposit + credit ACCOUNT counts).
WANTED = {
    "951": "BSR-1 Table 2.2 - State & population group-wise outstanding credit "
           "(no. of accounts + amount), QUARTERLY, Mar-2014..Jun-2026  -> take March quarters 2018-2024",
    "853": "BSR-2 Table 2.3 - Deposits of SCBs by State/UT "
           "(no. of accounts + amount), ANNUAL, Mar-2019..Mar-2026     -> covers 2019-2024",
    "1199": "BSR-2 Time Series - Bank Deposits of SCBs by Region/State/District/Bank group/Pop group, "
            "ANNUAL, Mar-2010..Mar-2018                                -> supplies the missing 2018",
    "943": "BSR-1 Table 1.3 - Outstanding credit of SCBs by state, QUARTERLY, Mar-2014..Jun-2026 "
           "(fallback / cross-check for 951)",
}


def sap_logon(d: DBIE, session: str) -> None:
    """Authenticate the session against SAP BO (as guest_user).

    This MUST happen before dbie_getReportLink. Once it has, the sapLink that
    getReportLink returns already carries a full SAP logon token in its `token=`
    query parameter. Without it, the link comes back ending in a bare `token=`
    and the viewer shows a logon page.

    Do NOT append anything to the returned URL -- the DBIE session id is not a
    SAP token, and tacking it on truncates a valid token into an invalid one.
    """
    r = d.s.post(
        f"{LOGIN}/login_getSapToken",
        headers={"Content-Type": "application/json", "channelkey": "key2",
                 "datatype": "application/json", "authorization": session},
        data=json.dumps({"body": {"portalCode": "DBIE", "user": "", "code": ""}}),
        timeout=90,
    )
    r.raise_for_status()
    status = json.loads(html.unescape(r.text)).get("header", {}).get("status")
    if status != "success":
        raise RuntimeError(f"SAP logon failed: {status}")


def main(ids):
    d = DBIE()
    session = d.session_token()
    sap_logon(d, session)

    for rid in ids:
        try:
            o = d.call("dbie_getReportLink",
                       {"reportId": encrypt(str(rid)), "lang": encrypt("English")})
            link = o.get("body", {}).get("sapLink")
            if not link:
                print(f"[{rid}] no link returned: {o.get('header')}")
                continue
            path = decrypt(link)
            embedded = path.split("token=")[-1]
            if len(embedded) < 10:
                print(f"[{rid}] WARNING: link has no SAP token -- it will show a logon page.")
            print(f"\n=== report {rid} ===")
            if str(rid) in WANTED:
                print(f"  {WANTED[str(rid)]}")
            print(f"  {ORIGIN}{path}")
        except Exception as e:
            print(f"[{rid}] FAILED: {e}")

    print("\nTokens expire fast - open the link right away, or re-run this script.")


if __name__ == "__main__":
    main(sys.argv[1:] or list(WANTED))
