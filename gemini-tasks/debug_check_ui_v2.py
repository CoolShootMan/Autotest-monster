from playwright.sync_api import sync_playwright
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        storage_state = "test_case/UI/Test_Katana/cookie_release.json"
        
        context = browser.new_context(storage_state=storage_state)
        page = context.new_page()
        page.goto("https://release.pear.us/yu-xiao")
        page.wait_for_timeout(5000)
        
        form_name = "Auto test form"
        form_locator = page.get_by_text(form_name, exact=True).first
        
        if form_locator.count() > 0:
            box = form_locator.bounding_box()
            logger.info(f"Found '{form_name}' at {box}")
            
            # Take a cropped screenshot
            screenshot_path = "debug_form_area.png"
            page.screenshot(path=screenshot_path, clip={
                'x': 0,
                'y': max(0, box['y'] - 200),
                'width': 500, # Focused width
                'height': 600
            })
            logger.info(f"Saved cropped screenshot to {screenshot_path}")
            
            # Capture all elements in this area
            elements = page.locator("button, a, [role='button']").all()
            logger.info(f"Elements near '{form_name}':")
            for i, el in enumerate(elements):
                bbox = el.bounding_box()
                if bbox and abs(bbox['y'] - box['y']) < 300:
                    try:
                        info = f"Tag: {el.evaluate('e => e.tagName')}, Label: {el.get_attribute('aria-label')}, Text: {el.inner_text().strip()}"
                        logger.info(f"  [{i}] {info} at y={bbox['y']}")
                        
                        # If it's a button, click it if it seems relevant
                        if "More action" in (el.get_attribute('aria-label') or ""):
                             logger.info(f"Clicking 'More action' button {i} specifically...")
                             el.click()
                             page.wait_for_timeout(2000)
                             page.screenshot(path=f"debug_menu_after_click_{i}.png")
                             # Check for View Submissions
                             menu_items = page.get_by_text("View submissions", exact=False).all()
                             if menu_items:
                                 logger.info(f"!!! SUCCESS !!! FOUND 'View submissions' after clicking element {i}")
                             page.keyboard.press("Escape")
                             page.wait_for_timeout(500)
                    except: pass
        else:
            logger.error(f"Form '{form_name}' not found.")
            # Take screenshot of whatever is at the bottom where modules usually are
            page.screenshot(path="debug_not_found_bottom.png", clip={'x':0, 'y':5000, 'width':1000, 'height':1000})

        browser.close()

if __name__ == "__main__":
    run()
