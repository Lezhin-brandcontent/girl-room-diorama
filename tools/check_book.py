import time
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(args=["--use-gl=angle","--enable-webgl","--ignore-gpu-blocklist"])
    ctx=b.new_context(viewport={"width":1440,"height":900}); pg=ctx.new_page()
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type=="error" and errs.append(m.text))
    ctx.route("https://www.bomtoon.com/**", lambda r: r.fulfill(body="ok"))
    pg.goto("http://127.0.0.1:8765/diorama.html"); pg.wait_for_function("Object.keys(window.__props||{}).length>0", timeout=60000)
    time.sleep(2.5); pg.screenshot(path="bedshot/b_home.png")
    pg.evaluate("__activate('diary')"); time.sleep(1.2); pg.mouse.move(20,20); pg.screenshot(path="bedshot/b_mid.png")
    time.sleep(1.6); pg.screenshot(path="bedshot/b_open.png")
    print("btn", pg.evaluate("siteBtn.style.display"), pg.evaluate("siteBtn.href"), pg.evaluate("siteBtn.textContent"))
    with ctx.expect_page() as np_: pg.click("#siteBtn")
    print("opened", np_.value.url)
    pg.keyboard.press("Escape"); time.sleep(1.5); pg.screenshot(path="bedshot/b_closed.png")
    pg.evaluate("__activate('diary')"); time.sleep(2.8); pg.mouse.move(20,20); pg.screenshot(path="bedshot/b_open2.png")
    print("errors", errs); b.close()
