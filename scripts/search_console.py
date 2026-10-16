"""Verify montehorton.net with Google, make the owner an owner, and submit the sitemap.

Runs in GitHub Actions after each Pages deploy. First run: fetches a verification
file token and writes google<token>.html (the workflow commits it, which triggers a
new deploy). Next run: the file is live, so it verifies, adds the owner email, adds
the Search Console property and submits sitemap.xml. Later runs just resubmit.
"""
import json, os, sys, glob, time, urllib.parse
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

SITE = "https://montehorton.net/"
SITEMAP = SITE + "sitemap.xml"
SCOPES = ["https://www.googleapis.com/auth/siteverification",
          "https://www.googleapis.com/auth/webmasters"]

creds = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GSC_SA_KEY"]), scopes=SCOPES)
creds.refresh(Request())
H = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
owner = os.environ.get("GSC_OWNER_EMAIL", "").strip()
site_obj = {"type": "SITE", "identifier": SITE}

def die(r, what):
    sys.exit(f"{what} failed: HTTP {r.status_code} {r.text}")

# 1. Make sure the verification file exists in the repo.
r = requests.post("https://www.googleapis.com/siteVerification/v1/token", headers=H,
                  json={"site": site_obj, "verificationMethod": "FILE"})
if r.status_code != 200: die(r, "Get verification token")
fname = r.json()["token"]          # e.g. google1234abcd.html
if not os.path.exists(fname):
    with open(fname, "w") as f:
        f.write(f"google-site-verification: {fname}")
    print(f"Wrote {fname}; it will be committed and deployed, and the next run verifies.")
    sys.exit(0)

# 2. Verify (idempotent) and make the owner an owner too.
time.sleep(20)
body = {"site": site_obj}
if owner:
    body["owners"] = [owner]
r = requests.post("https://www.googleapis.com/siteVerification/v1/webResource",
                  params={"verificationMethod": "FILE"}, headers=H, json=body)
if r.status_code != 200: die(r, "Verify site")
print("Verified. Owners:", r.json().get("owners"))

# 3. Add the property to Search Console and submit the sitemap.
enc = urllib.parse.quote(SITE, safe="")
r = requests.put(f"https://www.googleapis.com/webmasters/v3/sites/{enc}", headers=H)
if r.status_code not in (200, 204): die(r, "Add Search Console property")
r = requests.put(f"https://www.googleapis.com/webmasters/v3/sites/{enc}/sitemaps/"
                 + urllib.parse.quote(SITEMAP, safe=""), headers=H)
if r.status_code not in (200, 204): die(r, "Submit sitemap")
print("Sitemap submitted:", SITEMAP)
