#!/usr/bin/env python3
"""
Minimal client for RBI's new DBIE portal (data.rbi.org.in), the successor to the
retired dbie.rbi.org.in. Used to reach BSR-1/BSR-2 state-wise account counts,
which are not published as static files anywhere.

Mechanics, all reverse-engineered from the site's own Angular bundle
(https://data.rbi.org.in/main.<hash>.js):

  gateway   POST https://data.rbi.org.in/CIMS_Gateway_DBIE/GATEWAY/SERVICES/<service>
  session   POST security_generateSessionToken  -> token in the `authorization`
            RESPONSE header; every later call sends it as an `authorization` header
  headers   Content-Type: application/json, channelkey: key2, datatype: application/json
  payload   {"body": { ... }}

Some services expect selected string fields to be encrypted. The bundle uses
CryptoJS with constants hard-coded in the JS (they are not per-session):

  key = PBKDF2(TOKEN, salt=unhex(TOKEN_STATUS), 32 bytes, 1000 iters, HMAC-SHA1)
  ct  = base64( AES-256-CBC(pkcs7(plaintext), key, iv=unhex(TOKEN_RESPONSE)) )

Everything here is read-only GET/POST against a public portal.
"""

import base64
import hashlib
import html
import json

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

BASE = "https://data.rbi.org.in/CIMS_Gateway_DBIE/GATEWAY/SERVICES"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# Hard-coded in the Angular bundle (class with generateKey/encrypt/decrypt).
TOKEN = "48d6b976d7135745b47b407cd8e659a45d8ebaca4ee95f87d5d939604f472268"
TOKEN_STATUS = "577bd45a17977269694908d80905c32a"   # PBKDF2 salt
TOKEN_RESPONSE = "dc0da04af8fee58593442bf834b30739"  # AES IV

_KEY = hashlib.pbkdf2_hmac("sha1", TOKEN.encode(), bytes.fromhex(TOKEN_STATUS), 1000, 32)
_IV = bytes.fromhex(TOKEN_RESPONSE)


def encrypt(plain: str) -> str:
    c = AES.new(_KEY, AES.MODE_CBC, _IV)
    return base64.b64encode(c.encrypt(pad(str(plain).encode(), AES.block_size))).decode()


def decrypt(ct: str):
    try:
        c = AES.new(_KEY, AES.MODE_CBC, _IV)
        return unpad(c.decrypt(base64.b64decode(ct)), AES.block_size).decode()
    except Exception:
        return None


class DBIE:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": UA,
            "Origin": "https://data.rbi.org.in",
            "Referer": "https://data.rbi.org.in/",
        })
        self.token = None

    def session_token(self) -> str:
        r = self.s.post(
            f"{BASE}/security_generateSessionToken",
            headers={"Content-Type": "application/json", "channelkey": "key2",
                     "datatype": "application/json"},
            data=json.dumps({"body": {}}), timeout=90,
        )
        r.raise_for_status()
        self.token = r.headers.get("authorization")
        if not self.token:
            raise RuntimeError("no authorization header returned")
        return self.token

    def call(self, service: str, body: dict | None = None) -> dict:
        if not self.token:
            self.session_token()
        r = self.s.post(
            f"{BASE}/{service}",
            headers={"Content-Type": "application/json", "channelkey": "key2",
                     "datatype": "application/json", "authorization": self.token},
            data=json.dumps({"body": body or {}}), timeout=180,
        )
        r.raise_for_status()
        # Responses are HTML-entity-escaped JSON.
        return json.loads(html.unescape(r.text))


if __name__ == "__main__":
    d = DBIE()
    print("session:", d.session_token())
    print("enc('English') =", encrypt("English"))
    print("roundtrip     =", decrypt(encrypt("English")))
    for svc, body in [
        ("dbie_getReportLink", {"reportId": "951", "lang": encrypt("English")}),
        ("dbie_getDashboardReportLink", {"reportId": "951", "lang": encrypt("English")}),
    ]:
        try:
            out = d.call(svc, body)
            print(f"\n--- {svc} ---")
            print(json.dumps(out, indent=1)[:1200])
        except Exception as e:
            print(f"\n--- {svc} FAILED: {e}")
