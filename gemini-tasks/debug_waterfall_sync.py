from playwright.sync_api import sync_playwright
from loguru import logger
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        storage_state="test_case/UI/Test_Katana/cookie_release.json",
        **p.devices['iPhone 12 Pro']
    )
    page = context.new_page()
    
    logger.info("1. Opening curator page...")
    page.goto("https://release.pear.us/storefront-modules#Storefront", wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    logger.info("2. Checking Waterfall radio button status...")
    waterfall_radio = page.get_by_label("Waterfall")
    is_checked = waterfall_radio.is_checked()
    logger.info(f"   Waterfall checked: {is_checked}")
    
    if not is_checked:
        logger.info("3. Toggling Waterfall layout...")
        waterfall_radio.check()
        page.wait_for_timeout(1000)
        logger.info(f"   Waterfall now checked: {waterfall_radio.is_checked()}")
    
    logger.info("4. Clicking Publish...")
    page.get_by_role("button", name="Publish").click()
    
    logger.info("5. Waiting for redirect to shop page...")
    try:
        page.wait_for_url(re.compile("https://release.pear.us/yu-xiao"), timeout=30000)
        logger.info(f"   Successfully redirected to: {page.url}")
    except Exception as e:
        logger.warning(f"   Redirect failed or timed out: {e}")
        page.goto("https://release.pear.us/yu-xiao", wait_until="networkidle")
    
    page.wait_for_timeout(5000) # Give it extra time
    page.reload(wait_until="networkidle")
    
    logger.info("6. Navigating to Products...")
    anchor_list = page.locator(".list-container .katana-14rbssj")
    if anchor_list.count() > 0:
        anchor_list.last.click(force=True)
        page.wait_for_timeout(3000)
    
    logger.info("7. Comparing card heights...")
    for sel in [".MuiBox-root", ".card__container"]:
        elements = page.locator(sel).all()
        visible_els = [el for el in elements if el.is_visible() and (el.bounding_box() or {}).get('height', 0) > 100]
        heights = [el.bounding_box()['height'] for el in visible_els[:5]]
        logger.info(f"   Selector '{sel}': heights={heights}, unique={len(set(heights))}")
    
    page.screenshot(path="gemini-tasks/waterfall_comparison.png")
    browser.close()
