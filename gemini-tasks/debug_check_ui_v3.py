from playwright.sync_api import sync_playwright
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        storage_state = "test_case/UI/Test_Katana/cookie_release.json"
        
        context = browser.new_context(storage_state=storage_state, viewport={'width': 1280, 'height': 3000})
        page = context.new_page()
        page.goto("https://release.pear.us/yu-xiao")
        page.wait_for_timeout(5000)
        
        form_name = "Auto test form"
        form_locator = page.get_by_text(form_name, exact=True).first
        
        if form_locator.count() > 0:
            box = form_locator.bounding_box()
            logger.info(f"Found '{form_name}' at {box}")
            
            # Take a larger screenshot area
            screenshot_path = "debug_form_area_v3.png"
            page.screenshot(path=screenshot_path, clip={
                'x': 0,
                'y': max(0, box['y'] - 300),
                'width': 1280,
                'height': 1000
            })
            logger.info(f"Saved area screenshot to {screenshot_path}")
            
            # Find elements near the form
            elements = page.locator("button, a, [role='button'], [role='menuitem']").all()
            for i, el in enumerate(elements):
                try:
                    bbox = el.bounding_box()
                    if bbox and abs(bbox['y'] - box['y']) < 400:
                        text = el.inner_text().strip()
                        label = el.get_attribute('aria-label') or ""
                        role = el.get_attribute('role') or ""
                        logger.info(f"  [{i}] Role: {role}, Label: {label}, Text: {text} at y={bbox['y']}")
                        
                        # Click if it's a "More action" or "Edit" button
                        if "More" in label or "More" in text:
                            logger.info(f"Clicking potential menu button {i}...")
                            el.scroll_into_view_if_needed()
                            el.click()
                            page.wait_for_timeout(2000)
                            page.screenshot(path=f"debug_result_click_{i}.png")
                            
                            # Check for View Submissions in the popup
                            subs_links = page.get_by_text("submissions", exact=False).all()
                            for sl in subs_links:
                                if sl.is_visible():
                                    logger.info(f"!!! SUCCESS !!! Found visible 'submissions' text in element: {sl.inner_text()}")
                            
                            # Log all visible links/buttons now
                            visible_stuff = [b.inner_text().strip() for b in page.locator("button, a").all() if b.is_visible()]
                            logger.info(f"Visible elements after click {i}: {visible_stuff}")
                            
                            page.keyboard.press("Escape")
                            page.wait_for_timeout(1000)
                except: pass
        else:
            logger.error(f"Form '{form_name}' not found.")

        browser.close()

if __name__ == "__main__":
    run()
