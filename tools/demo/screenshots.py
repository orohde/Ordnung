"""Screenshots of a running demo installation (see make_demo.py) with Playwright and Chrome.

    python tools/demo/screenshots.py http://localhost:8472 de OUTDIR [--signature sig.png]
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

USER, PASSWORD = "demo", "demo1234"
MAPPE = {"de": "Steuererklärung 2026", "en": "Tax return 2026"}
QUERY = {"de": "nordlicht", "en": "nordlicht"}
POLICY = {"de": "Versicherungsschein Wohngebäude", "en": "Buildings insurance policy"}
EDIT = {"de": "Heil- und Kostenplan", "en": "Treatment and cost plan"}
EDIT_TEXT = {"de": "Einverstanden, bitte Termin im Dezember", "en": "Agreed, please book a date in December"}


async def shoot(base: str, lang: str, out: Path, signature: Path | None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2,
                                        color_scheme="dark", locale=lang)
        page = await ctx.new_page()
        await page.goto(base)
        await page.evaluate("""async ([u, p, lang]) => {
            await fetch('api/login', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                      body: JSON.stringify({username: u, password: p})});
            localStorage.setItem('ordnung.theme', JSON.stringify('dark'));
            localStorage.setItem('ordnung.lang', JSON.stringify(lang));
            localStorage.setItem('ordnung.previewPos', JSON.stringify('right'));
        }""", [USER, PASSWORD, lang])
        if signature:
            await page.request.put(base + "/api/me/signature", data=signature.read_bytes(),
                                   headers={"Content-Type": "image/png"})
        await page.reload()
        await page.wait_for_timeout(1500)

        async def snap(name: str, wait: int = 1200):
            await page.wait_for_timeout(wait)
            await page.screenshot(path=str(out / f"{name}.png"))
            print("  ", name)

        # 1 archive with tree, list and preview
        await page.evaluate("""async (title) => {
            setAllOpen(true); selectFolder('');
            const d = await api('documents?recursive=true&q=' + encodeURIComponent(title));
            openPreview(d.items[0]);
        }""", POLICY[lang])
        await snap("01-archiv", 2500)
        # 2 full-text search
        await page.evaluate("closePreview()")
        await page.fill("#search", QUERY[lang])
        await page.press("#search", "Enter")
        await snap("02-suche", 1500)
        # 3 collection
        await page.fill("#search", "")
        await page.evaluate("async (m) => { await loadMappen(); selectMappe(m); }", MAPPE[lang])
        await snap("03-mappe", 1500)
        # 4 inbox
        await page.evaluate("location.hash = '#/eingang'")
        await snap("04-posteingang", 2500)
        # 5 senders and rules
        await page.evaluate("location.hash = '#/regeln'")
        await snap("05-absender", 2500)
        # 6 PDF editor with text, tick and signature
        await page.evaluate("location.hash = '#/'")
        await page.wait_for_timeout(800)
        await page.evaluate("""async ([title, text]) => {
            const d = await api('documents?recursive=true&q=' + encodeURIComponent(title));
            await openEditor(d.items[0]);
            Ed.scale = 1.05;
            await edRender();
            await edSigLoad();
            Ed.items.push({id: 92, page: 1, type: 'check', x: 56, y: 442, w: 12, h: 12});
            Ed.items.push({id: 91, page: 1, type: 'text', x: 74, y: 440, size: 12, text});
            if (Ed.sigImg) {
              const w = 160, h = w * Ed.sigImg.naturalHeight / Ed.sigImg.naturalWidth;
              Ed.items.push({id: 93, page: 1, type: 'sign', x: 340, y: 470, w, h});
            }
            Ed.items.forEach(edDrawItem);
            edSelect(Ed.items[Ed.items.length - 1]);
        }""", [EDIT[lang], EDIT_TEXT[lang]])
        await snap("06-editor", 2500)
        await page.evaluate("closeEditor(true)")
        # 7 settings: areas without owner
        await page.evaluate("location.hash = '#/einstellungen/ablage'")
        await page.wait_for_timeout(1500)
        await page.evaluate("document.querySelector('#st-areas').scrollIntoView({block: 'center'})")
        await snap("07-bereiche", 800)
        await ctx.close()

        # 8 phone
        phone = await browser.new_context(viewport={"width": 430, "height": 932}, device_scale_factor=3,
                                          color_scheme="dark", is_mobile=True, has_touch=True, locale=lang)
        page = await phone.new_page()
        await page.goto(base)
        await page.evaluate("""async ([u, p, lang]) => {
            await fetch('api/login', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                      body: JSON.stringify({username: u, password: p})});
            localStorage.setItem('ordnung.theme', JSON.stringify('dark'));
            localStorage.setItem('ordnung.lang', JSON.stringify(lang));
        }""", [USER, PASSWORD, lang])
        await page.reload()
        await page.wait_for_timeout(2000)
        await page.evaluate("selectFolder('')")
        await page.wait_for_timeout(1200)
        await page.screenshot(path=str(out / "08-handy.png"))
        print("   08-handy")
        await page.evaluate("$('tree-panel').classList.add('is-open')")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(out / "09-handy-baum.png"))
        print("   09-handy-baum")
        await browser.close()


if __name__ == "__main__":
    sig = Path(sys.argv[sys.argv.index("--signature") + 1]) if "--signature" in sys.argv else None
    asyncio.run(shoot(sys.argv[1], sys.argv[2], Path(sys.argv[3]), sig))
