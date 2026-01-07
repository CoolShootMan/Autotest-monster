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
    
    logger.info("2. Navigating to Products using robust anchor...")
    anchor_list = page.locator(".MuiStack-root.katana-10mg3g5 .katana-14rbssj")
    anchor_list.last.click(force=True)
    page.wait_for_timeout(3000)
    
    logger.info("3. Inspecting potential product card selectors...")
    
    selectors = [
        ".MuiBox-root",
        'a[href*="/p/product/"]',
        ".MuiStack-root",
        '[data-index]' # Let's see if data-index came back
    ]
    
    for sel in selectors:
        elements = page.locator(sel).all()
        visible_count = 0
        heights = []
        for el in elements:
            if el.is_visible():
                bbox = el.bounding_box()
                if bbox and bbox['height'] > 50: # Only count things taller than 50px
                    visible_count += 1
                    heights.append(bbox['height'])
        
        logger.info(f"   Selector '{sel}': {len(elements)} total, {visible_count} visible (>50px)")
        if visible_count > 0:
            logger.info(f"      Heights: {set(heights[:5])}...")
            # Dump info about the first one
            first_el = [el for el in elements if el.is_visible() and (el.bounding_box() or {}).get('height', 0) > 50][0]
            logger.info(f"      First's classes: {first_el.get_attribute('class')}")
            logger.info(f"      First's tag: {first_el.evaluate('el => el.tagName')}")
    
    page.screenshot(path="gemini-tasks/inspect_products.png")
    browser.close()
