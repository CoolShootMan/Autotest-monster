from playwright.sync_api import sync_playwright
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        storage_state = "test_case/UI/Test_Katana/cookie_release.json"
        
        if not os.path.exists(storage_state):
             logger.error(f"Storage state file {storage_state} NOT found!")
             return

        context = browser.new_context(storage_state=storage_state, viewport={'width': 1280, 'height': 2000})
        page = context.new_page()
        
        url = "https://release.pear.us/yu-xiao"
        logger.info(f"Navigating to {url}...")
        
        try:
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_timeout(5000) # Give it a bit more time
            
            page.screenshot(path="debug_t4264_open.png")
            logger.info("Saved screenshot to debug_t4264_open.png")
            
            # Check for Customize button
            customize_btn = page.get_by_role("button", name="Customize")
            logger.info(f"Customize button count: {customize_btn.count()}")
            if customize_btn.count() > 0:
                logger.info(f"Customize button visibility: {customize_btn.first.is_visible()}")
            
            # Check for other common buttons
            buttons = page.locator("button").all()
            logger.info(f"Found {len(buttons)} total buttons.")
            for i, btn in enumerate(buttons[:20]):
                try:
                    logger.info(f"  Button {i}: text='{btn.inner_text().strip()}', aria-label='{btn.get_attribute('aria-label')}'")
                except: pass
            
            # Check for login button or text
            if "Login" in page.content():
                logger.warning("Found 'Login' text on page. Might not be logged in!")
            
            # Check for "Something went wrong"
            if "Something went wrong" in page.content():
                logger.error("Page crashed with 'Something went wrong'!")

        except Exception as e:
            logger.error(f"Error during navigation: {e}")
            page.screenshot(path="debug_t4264_error.png")

        browser.close()

if __name__ == "__main__":
    run()
