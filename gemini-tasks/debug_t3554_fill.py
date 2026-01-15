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
        
        url = "https://release.pear.us/yu-xiao"
        logger.info(f"Navigating to {url}...")
        
        try:
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_timeout(5000)
            
            # Click Module button
            module_btn = page.get_by_role("button", name="Module", exact=True).first
            if module_btn.is_visible():
                module_btn.click()
                logger.info("Clicked 'Module' button.")
                page.wait_for_timeout(3000)
                
                page.screenshot(path="debug_t3554_module_clicked.png")
                logger.info("Saved screenshot to debug_t3554_module_clicked.png")
                
                # Inspect inputs, textareas, labels
                logger.info("Inspecting elements in the 'Module' dialog:")
                
                inputs = page.locator("input").all()
                for i, el in enumerate(inputs):
                    logger.info(f"Input {i}: placeholder='{el.get_attribute('placeholder')}', aria-label='{el.get_attribute('aria-label')}', name='{el.get_attribute('name')}', role='{el.get_attribute('role')}', type='{el.get_attribute('type')}'")
                
                textareas = page.locator("textarea").all()
                for i, el in enumerate(textareas):
                    logger.info(f"Textarea {i}: placeholder='{el.get_attribute('placeholder')}', aria-label='{el.get_attribute('aria-label')}', name='{el.get_attribute('name')}'")
                
                labels = page.locator("label").all()
                for i, el in enumerate(labels):
                    logger.info(f"Label {i}: text='{el.inner_text().strip()}', for='{el.get_attribute('for')}'")
                
                # Check for "Enter title of the module" text anywhere
                hits = page.get_by_text("Enter title of the module", exact=False).all()
                logger.info(f"Found {len(hits)} occurrences of 'Enter title of the module' text.")
                for i, hit in enumerate(hits):
                     logger.info(f"  Hit {i}: HTML={hit.evaluate('el => el.outerHTML')}")

            else:
                logger.error("'Module' button not visible!")
                page.screenshot(path="debug_t3554_no_module_btn.png")

        except Exception as e:
            logger.error(f"Error: {e}")
            page.screenshot(path="debug_t3554_error.png")

        browser.close()

if __name__ == "__main__":
    run()
