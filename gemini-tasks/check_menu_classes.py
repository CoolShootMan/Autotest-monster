from playwright.sync_api import sync_playwright
from loguru import logger

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        storage_state="test_case/UI/Test_Katana/cookie_release.json",
        **p.devices['iPhone 12 Pro']
    )
    page = context.new_page()
    
    logger.info("Opening shop page...")
    page.goto("https://release.pear.us/yu-xiao", wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    # Try multiple ways to find the menu items
    logger.info("Checking for .katana-14rbssj elements:")
    items = page.locator(".katana-14rbssj").all()
    logger.info(f"Found {len(items)} items with .katana-14rbssj")
    
    if len(items) > 0:
        for i, item in enumerate(items):
            try:
                text = item.inner_text().splitlines()[0]
                parent = item.evaluate("el => el.parentElement.className")
                grandparent = item.evaluate("el => el.parentElement.parentElement.className")
                logger.info(f"Item {i}: text='{text}', parent='{parent}', grandparent='{grandparent}'")
            except:
                pass
    
    browser.close()
