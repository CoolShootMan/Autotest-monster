from playwright.sync_api import sync_playwright
from loguru import logger

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        storage_state="test_case/UI/Test_Katana/cookie_release.json",
        **p.devices['iPhone 12 Pro']
    )
    page = context.new_page()
    
    page.goto("https://release.pear.us/yu-xiao", wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    anchor_list = page.locator(".MuiStack-root.katana-10mg3g5 .katana-14rbssj")
    anchor_list.last.click(force=True)
    page.wait_for_timeout(3000)
    
    # Find the large boxes
    elements = page.locator(".MuiBox-root").all()
    for el in elements:
        if el.is_visible():
            bbox = el.bounding_box()
            if bbox and bbox['height'] > 100:
                logger.info(f"Dumping large box (height={bbox['height']}):")
                inner_html = el.evaluate("el => el.outerHTML")
                logger.info(f"HTML: {inner_html[:1000]}...")
                break
    
    browser.close()
