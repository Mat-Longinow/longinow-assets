"""DQ-485: screenshots of the Integrations badge row, + picker modal and Active section (real component, mock bridge).
Start the harness first: `npx vite --config scripts/dq485-shots/vite.config.ts` (from brain-iq/), then `python3 shoot.py`.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    br = p.chromium.launch()
    page = br.new_page(viewport={"width": 640, "height": 760}, device_scale_factor=2)
    page.goto("http://localhost:5485/")
    page.wait_for_selector("[data-testid=badge-row]")
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "1-desktop-badge-row-closed.png"))
    page.locator("[aria-label='Add integration']").click()
    page.wait_for_timeout(400)
    page.locator(".ant-modal .ant-select-selector").click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(OUT / "2-desktop-add-modal-dropdown.png"))
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    page.locator(".ant-collapse-header", has_text="Active").click()
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT / "3-desktop-active-open.png"))
    br.close()
