#!/usr/bin/env python3
"""Refresh the embedded ccfddl snapshot inside the deadline page.

usage: python3 update_snapshot.py PAGE.html [allconf.json]
Without the second argument the data is downloaded from ccfddl's GitHub Pages branch.
"""
import datetime, json, re, sys, urllib.request

SRC = "https://raw.githubusercontent.com/ccfddl/ccfddl.github.io/page/conference/allconf.json"
path = sys.argv[1]
html = open(path, encoding="utf-8").read()

if len(sys.argv) > 2:
    allconf = json.load(open(sys.argv[2], encoding="utf-8"))
else:
    with urllib.request.urlopen(SRC, timeout=60) as r:
        allconf = json.loads(r.read().decode("utf-8"))
if not isinstance(allconf, list) or len(allconf) < 100:
    sys.exit("unexpected ccfddl data; snapshot left unchanged")

gist = json.loads(re.search(r'<script type="application/json" id="gist-data">(.*?)</script>', html, re.S).group(1))
norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
alias = json.loads(re.search(r'<script type="application/json" id="alias-data">(.*?)</script>', html, re.S).group(1))
keys = {r[7].split("/")[-1].lower() for r in gist} | {str(v).lower() for v in alias.values()}
titles = {norm(r[0].split(" (")[0]) for r in gist}

year = datetime.date.today().year
keep = []
for e in allconf:
    if str(e.get("dblp", "")).lower() in keys or norm(e.get("title", "")) in titles:
        e = dict(e)
        e["confs"] = [
            {k: v for k, v in c.items() if k not in ("opening", "opening_is_derived")}
            for c in e.get("confs", []) if int(c.get("year", 0)) >= year - 2
        ]
        keep.append(e)

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
payload = json.dumps({"fetched": now, "confs": keep}, ensure_ascii=False, separators=(",", ":"))
payload = payload.replace("</", "<\\/")
new, n = re.subn(
    r'(<script type="application/json" id="snapshot">).*?(</script>)',
    lambda m: m.group(1) + payload + m.group(2), html, count=1, flags=re.S)
if n != 1:
    sys.exit("snapshot block not found")
open(path, "w", encoding="utf-8").write(new)
print(f"snapshot updated: {len(keep)} conferences, {now}")
