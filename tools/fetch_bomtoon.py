import re, json, sys, io, time, urllib.request
from PIL import Image
OUT = sys.argv[1]   # 사용: python fetch_bomtoon.py <출력폴더> <저장한 main.html>
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
def nd(html):
    return json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1))
s = open(sys.argv[2] if len(sys.argv) > 2 else "bomtoon/main.html", encoding="utf-8").read()   # 봄툰 소설 메인 HTML (curl 로 저장)
m = nd(s)["props"]["pageProps"]["main"]
seen, works = set(), []
for key in ("newest", "weekDay"):
    for w in m[key]:
        if w.get("isAdult") is not False or w["alias"] in seen: continue
        th = {t["type"]: t["imagePath"] for t in w.get("thumbnails") or []}
        if "VERTICAL" not in th: continue
        seen.add(w["alias"]); works.append((w, th["VERTICAL"]))
works = works[:12]
res = []
for w, img in works:
    url = f"https://www.bomtoon.com/detail/{w['alias']}"
    syn, adult = "", None
    try:
        d = nd(get(url).decode("utf-8"))
        syns, ads = [], []
        def walk(o):
            if isinstance(o, dict):
                if o.get("alias") == w["alias"]:
                    if isinstance(o.get("synopsis"), str): syns.append(o["synopsis"])
                    if "isAdult" in o: ads.append(o["isAdult"])
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(d)
        syn = max(syns, key=len) if syns else ""
        adult = ads[0] if ads else None
    except Exception as e:
        print("detail fail", w["alias"], e)
    if adult: print("skip adult", w["alias"]); continue
    im = Image.open(io.BytesIO(get(img))).convert("RGB")
    im.thumbnail((480, 720)); im.save(f"{OUT}/{w['alias']}.jpg", quality=88)
    res.append({"alias": w["alias"], "title": w["title"], "author": w.get("author") or w.get("creators") or "",
                "synopsis": syn.strip(), "url": url, "isAdult": False, "w": im.width, "h": im.height})
    print(w["alias"], im.size, adult, len(syn))
    time.sleep(0.4)
json.dump(res, open(f"{OUT}/novels.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
