from playwright.sync_api import sync_playwright
from loguru import logger

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        storage_state="test_case/UI/Test_Katana/cookie_release.json",
        **p.devices['iPhone 12 Pro']
    )
    page = context.new_page()
    
    logger.info("1. Opening shop page...")
    page.goto("https://release.pear.us/yu-xiao", wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    logger.info("2. Checking the refined anchor locator...")
    # The user provided: .MuiStack-root.katana-10mg3g5 
    items = page.locator(".MuiStack-root.katana-10mg3g5 > div")
    count = items.count()
    logger.info(f"   Found {count} top-level divs in .MuiStack-root.katana-10mg3g5")
    
    if count > 0:
        logger.info("3. Testing class-based locator: .MuiStack-root.katana-10mg3g5 .katana-14rbssj")
        anchor_items = page.locator(".MuiStack-root.katana-10mg3g5 .katana-14rbssj")
        item_count = anchor_items.count()
        logger.info(f"   Found {item_count} items with class .katana-14rbssj")
        
        if item_count > 0:
            last_text = anchor_items.last.inner_text().splitlines()[0]
            logger.info(f"   Last item text: '{last_text}'")
            logger.info("   Clicking the LAST item...")
            anchor_items.last.click()
            page.wait_for_timeout(3000)
        
        page.wait_for_timeout(3000)
        logger.info(f"   Current URL after click: {page.url}")
        page.screenshot(path="gemini-tasks/after_refined_anchor_click.png")
        
        # Check if product cards are visible
        cards = page.locator(".MuiBox-root")
        logger.info(f"   Visible MuiBox-root count (approx product cards): {cards.count()}")
        
    logger.info("Done!")
    browser.close()
