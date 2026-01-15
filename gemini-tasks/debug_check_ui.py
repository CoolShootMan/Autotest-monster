from playwright.sync_api import sync_playwright
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use the storage state to maintain login
        storage_state = "test_case/UI/Test_Katana/cookie_release.json"
        if not os.path.exists(storage_state):
            logger.error(f"Storage state file not found: {storage_state}")
            return

        context = browser.new_context(storage_state=storage_state)
        page = context.new_page()
        
        url = "https://release.pear.us/yu-xiao"
        logger.info(f"Navigating to {url}")
        page.goto(url)
        page.wait_for_timeout(5000) # Wait for content to load
        
        page.screenshot(path="debug_logged_in_page.png", full_page=True)
        logger.info("Saved full page screenshot to debug_logged_in_page.png")

        # Check for any "submissions" text already on the page
        subs = page.get_by_text("submissions", exact=False).all()
        logger.info(f"Found {len(subs)} elements with 'submissions' on the page.")
        for i, s in enumerate(subs):
            try:
                logger.info(f"Submissions element {i}: {s.inner_text()} | Visible: {s.is_visible()}")
            except: pass

        # Find all 'More action' buttons
        mores = page.get_by_label("More action").all()
        logger.info(f"Total 'More action' buttons found: {len(mores)}")
        
        for i, m in enumerate(mores):
            try:
                if not m.is_visible():
                    continue
                
                # Get some context text around the button
                # Go up 3 levels to find a container
                container = m.locator("xpath=./ancestor::div[1]")
                context_text = container.inner_text().strip().replace('\n', ' ')[:100]
                logger.info(f"Checking 'More action' button {i} with context: [{context_text}]")
                
                m.click()
                page.wait_for_timeout(1000)
                
                # Check for "View submissions" in the page (likely in a menu popup)
                view_subs = page.get_by_text("View submissions", exact=False)
                if view_subs.count() > 0 and view_subs.first.is_visible():
                    logger.info(f"*** FOUND IT! *** 'View submissions' appeared after clicking button {i}")
                    page.screenshot(path=f"found_submissions_menu_{i}.png")
                    # Log the full text of the menu
                    menu = page.locator("role=menu").first
                    if menu.count() > 0:
                        logger.info(f"Menu content: {menu.inner_text()}")
                
                # Close the menu
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except Exception as e:
                logger.debug(f"Error checking button {i}: {e}")

        browser.close()

if __name__ == "__main__":
    run()
