from playwright.sync_api import sync_playwright
import os
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        storage_state = "test_case/UI/Test_Katana/cookie_release.json"
        
        context = browser.new_context(storage_state=storage_state, viewport={'width': 1280, 'height': 2000})
        page = context.new_page()
        page.goto("https://release.pear.us/yu-xiao")
        page.wait_for_timeout(5000)
        
        form_name = "Auto test form"
        logger.info(f"Targeting form: {form_name}")
        
        # Strategy: Find a div that has the text and a button, and is relatively small
        # We use a regex for exact-ish match but allow for icons/spacing
        # The row usually has the text and the button as siblings or descendants
        try:
            # Look for the text specifically
            text_el = page.get_by_text(form_name, exact=True).first
            text_el.scroll_into_view_if_needed()
            
            # Find the row container. It's likely an ancestor that doesn't include the whole module.
            # We'll try to find the nearest div that has only one button and this text.
            row = page.locator("div").filter(has=page.get_by_text(form_name, exact=True)).filter(has=page.locator("button")).last
            
            button = row.locator("button").first
            logger.info(f"Found button in row for {form_name}. Clicking it...")
            button.click()
            page.wait_for_timeout(2000)
            
            page.screenshot(path="debug_menu_v5_click.png")
            
            # Check what appeared
            visible_text = page.locator("body").inner_text()
            if "View submissions" in visible_text:
                logger.info("*** SUCCESS! *** Found 'View submissions' in the menu.")
                # Log all visible links/buttons in the modal/popup
                popups = page.locator("role=menu, role=dialog").all()
                for i, p_el in enumerate(popups):
                    if p_el.is_visible():
                        logger.info(f"Popup {i} content: {p_el.inner_text()}")
            else:
                logger.warning("'View submissions' NOT found in menu.")
                # Log what IS there
                items = page.locator("button, a").all()
                visible_items = [it.inner_text().strip() for it in items if it.is_visible()]
                logger.info(f"Visible items after click: {visible_items}")
                
        except Exception as e:
            logger.error(f"Error during V5: {e}")
            page.screenshot(path="debug_error_v5.png")

        browser.close()

if __name__ == "__main__":
    run()
