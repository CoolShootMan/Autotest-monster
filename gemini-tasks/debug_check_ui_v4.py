from playwright.sync_api import sync_playwright
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        storage_state = "test_case/UI/Test_Katana/cookie_release.json"
        
        context = browser.new_context(storage_state=storage_state, viewport={'width': 1280, 'height': 5000})
        page = context.new_page()
        try:
            logger.info("Navigating to page with 90s timeout...")
            page.goto("https://release.pear.us/yu-xiao", wait_until="load", timeout=90000)
            page.wait_for_timeout(5000)
            
            # Find any text that looks like a form
            form_candidates = page.get_by_text("form", exact=False).all()
            logger.info(f"Found {len(form_candidates)} elements containing 'form'")
            for fc in form_candidates[:10]:
                try: logger.info(f"  Form candidate: {fc.inner_text().strip()[:50]}")
                except: pass

            form_name = "Auto test form"
            form_locator = page.get_by_text(form_name, exact=True).first
            
            if form_locator.count() > 0:
                box = form_locator.bounding_box()
                logger.info(f"Found '{form_name}' at {box}")
                
                # Take a larger screenshot area
                screenshot_path = "debug_form_area_v4.png"
                page.screenshot(path=screenshot_path) # Take full screenshot if possible
                logger.info(f"Saved full page screenshot to {screenshot_path}")
                
                # Find elements near the form
                elements = page.locator("button, a").all()
                for i, el in enumerate(elements):
                    try:
                        bbox = el.bounding_box()
                        if bbox and abs(bbox['y'] - box['y']) < 400:
                            text = el.inner_text().strip()
                            label = el.get_attribute('aria-label') or ""
                            logger.info(f"  [{i}] Label:[{label}] Text:[{text}] at y={bbox['y']}")
                            
                            # Click if it's a "More action" or "Edit" button
                            if "More" in label or "More" in text:
                                logger.info(f"Clicking button {i}...")
                                el.click()
                                page.wait_for_timeout(2000)
                                page.screenshot(path=f"debug_menu_v4_{i}.png")
                                
                                # Check for View Submissions in the popup
                                visible_text = page.locator("body").inner_text()
                                if "View submissions" in visible_text:
                                    logger.info(f"!!! SUCCESS !!! 'View submissions' is visible on page now!")
                                
                                page.keyboard.press("Escape")
                                page.wait_for_timeout(500)
                    except: pass
            else:
                logger.error(f"Form '{form_name}' not found.")
                page.screenshot(path="debug_not_found_v4.png")
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            page.screenshot(path="debug_fatal_v4.png")

        browser.close()

if __name__ == "__main__":
    run()
