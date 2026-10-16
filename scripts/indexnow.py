"""Tell IndexNow engines (Bing and others) about every URL in sitemap.xml."""
import json, os, re, sys, time, urllib.request

HOST = "montehorton.net"
key = os.environ["INDEXNOW_KEY"]
urls = re.findall(r"<loc>\s*(.*?)\s*</loc>", open("sitemap.xml").read())
if not urls:
    sys.exit("No URLs found in sitemap.xml")

time.sleep(30)  # give the CDN a moment to serve the fresh deploy and key file
body = json.dumps({
    "host": HOST,
    "key": key,
    "keyLocation": f"https://{HOST}/{key}.txt",
    "urlList": urls,
}).encode()
req = urllib.request.Request(
    "https://api.indexnow.org/indexnow",
    data=body,
    headers={"Content-Type": "application/json; charset=utf-8"},
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"IndexNow: HTTP {r.status} for {len(urls)} URL(s)")
except urllib.error.HTTPError as e:
    # 200/202 = accepted. 403 = key file not reachable yet. 422 = URL/host mismatch.
    print(f"IndexNow: HTTP {e.code} {e.read().decode(errors='ignore')}")
    sys.exit(1 if e.code not in (200, 202) else 0)
