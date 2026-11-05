"""제이미샵(레진·봄툰 공식 굿즈샵) 굿즈 상품: 사진 저장 + goods.json 작성.
사용: python tools/fetch_jmee.py web/diorama/goods [최대개수=12]

로그인해야 열리는 상품(대부분 성인 작품)은 뺀다. 보드에서 눌렀는데 로그인 화면이 뜨면 안 되니까.
이 판정은 서버가 아니라 페이지 스크립트가 로그인으로 넘기는 방식이라, 실제 브라우저(Playwright)로 열어 봐야 알 수 있다."""
import html, io, json, os, re, sys, urllib.parse, urllib.request
from PIL import Image
from playwright.sync_api import sync_playwright

outdir = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 12
PER_WORK = 2   # 한 작품 굿즈가 보드를 독차지하지 않게 (신상이 한 작품에 몰리는 경우가 많음)
SHOP = "https://j-meeshop.com"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}


def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20).read()


def parse(page):
    """목록 페이지 → 상품(번호, 사진, 이름, 가격). 상품 하나 = anchorBoxId_<번호> 로 시작하는 블록"""
    out = []
    for blk in page.split('<li id="anchorBoxId_')[1:]:
        no = re.match(r"\d+", blk).group(0)
        img = re.search(r'<img src="([^"]+/web/product/[^"]+)"', blk)
        name = re.search(r'class="name[^"]*".*?<a[^>]*>(.*?)</a>', blk, re.S)   # class="name " 처럼 공백이 붙어 있음
        price = re.search(r'([\d,]+)원', re.sub(r"<[^>]+>", " ", blk))
        brand = re.search(r'rel="브랜드".*?class="m_item">(.*?)</span>\s*</li>', blk, re.S)   # 브랜드 = 작품명
        if not (img and name):
            continue
        title = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", name.group(1)))).replace("상품명 :", "").strip()
        work = html.unescape(re.sub(r"<[^>]+>", "", brand.group(1))).strip() if brand else ""
        out.append({"no": no, "url": f"{SHOP}/product/detail.html?product_no={no}",   # 한글 섞인 긴 주소 대신 카페24 표준 주소
                    "img": urllib.parse.urljoin(SHOP, img.group(1)), "title": title, "work": work,
                    "price": (price.group(1) + "원") if price else ""})
    return out


os.makedirs(outdir, exist_ok=True)
for f in os.listdir(outdir):   # 이전에 받은 사진 정리 (목록이 바뀌면 안 쓰는 파일이 남으니까)
    if f.endswith(".jpg"):
        os.remove(os.path.join(outdir, f))

goods, seen, per = [], set(), {}
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page()
    for page_no in range(1, 30):   # 전체 상품(cate_no=59) 최신순으로 넘기며 공개 상품만 모음
        items = parse(get(f"{SHOP}/product/list.html?cate_no=59&page={page_no}").decode("utf-8", "ignore"))
        if not items:
            break
        for it in items:
            if len(goods) >= N:
                break
            if it["no"] in seen:
                continue
            seen.add(it["no"])
            if per.get(it["work"], 0) >= PER_WORK:
                continue
            pg.goto(it["url"], wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(1200)
            if "login" in pg.url:
                print("skip (login):", it["title"]); continue
            im = Image.open(io.BytesIO(get(it["img"]))).convert("RGB")
            im.thumbnail((480, 640))
            im.save(os.path.join(outdir, f"{it['no']}.jpg"), quality=86)
            per[it["work"]] = per.get(it["work"], 0) + 1
            # "징크스 [일반/예약판매] 데이트 아크릴 스탠드" → 상품명만 (작품명·판매 방식 떼기)
            name = it["title"]
            if it["work"] and name.startswith(it["work"]):
                name = name[len(it["work"]):].strip()
            name = re.sub(r"^\[[^\]]*\]\s*", "", name)
            goods.append({"no": it["no"], "work": it["work"], "name": name, "title": it["title"],
                          "price": it["price"], "url": it["url"], "size": im.size})
            print("ok", it["no"], it["title"])
        if len(goods) >= N:
            break
    br.close()
json.dump(goods, open(os.path.join(outdir, "goods.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total", len(goods), "checked", len(seen))
