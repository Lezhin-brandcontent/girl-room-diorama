"""레진 메인(비로그인) 작품 중 무작위 N개: 표지(tall)+썸네일 저장, books.json 작성."""
import re, sys, json, random, urllib.request, os, io
from PIL import Image
home, outdir, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36", "Referer": "https://www.lezhin.com/"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read()
u = open(home, encoding="utf-8").read().replace('\\"', '"')
objs = {}
for m in re.finditer(r'\{"id":"\d+","idLezhinObject":(\d+),"lezhinObjectType":"comic".*?"updatedAt":\d+\}', u):
    try: o = json.loads(m.group(0))
    except Exception: continue
    if o.get("mediaMap", {}).get("tall") and o.get("mediaMap", {}).get("thumbnail"):
        objs[o["alias"]] = o
pool = list(objs.values()); random.seed(); random.shuffle(pool)
os.makedirs(outdir, exist_ok=True)
books = []
for o in pool:
    if len(books) >= N: break
    page = get(f"https://www.lezhin.com/ko/comic/{o['alias']}").decode("utf-8", "ignore")
    if '\\"isAdult\\":false' not in page and '"isAdult":false' not in page:
        print("skip (adult or unknown):", o["alias"]); continue
    cid, upd = o["idLezhinObject"], o["updatedAt"]
    for kind, w, name in (("talls", 360, "tall"), ("thumbnails", 640, "thumb")):
        raw = get(f"https://ccdn.lezhin.com/v2/comics/{cid}/images/{kind}/1.webp?updated={upd}&width={w}")
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im.save(os.path.join(outdir, f"{o['alias']}_{name}.jpg"), quality=86)
        if name == "tall": size = im.size
    books.append({"alias": o["alias"], "title": o["title"], "authors": [a["name"] for a in o.get("authors", [])],
                  "genres": o.get("genres", []), "url": f"https://www.lezhin.com/ko/comic/{o['alias']}", "tallSize": size})
    print("ok", o["alias"], size)
json.dump(books, open(os.path.join(outdir, "books.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total", len(books), "of pool", len(pool))
