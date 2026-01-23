
from loguru import logger
from playwright.sync_api import Page, expect

def verify_invitation_link_clipboard(page: Page, v: dict):
    """
    Verifies the invitation link copying function.
    Based on inspection, the page has a 'Copy' button that triggers a toast.
    """
    logger.info("Executing verify_invitation_link_clipboard...")
    
    # 1. Wait for page stability
    page.wait_for_load_state("networkidle")
    
    # 2. Find the Copy button. 
    # Selector based on subagent observation: button:has-text("Copy")
    try:
        copy_btn = page.locator('button:has-text("Copy")').first
        copy_btn.wait_for(state="visible", timeout=10000)
        copy_btn.click()
        logger.info("Clicked 'Copy' button on Collabs page.")
    except Exception as e:
        logger.warning(f"Failed to find or click primary 'Copy' button: {e}. Trying fallback...")
        # Fallback to any button that looks like a copy trigger
        try:
            page.get_by_role("button", name="Copy").first.click()
        except:
            # If still fails, maybe need to open Manage dialog?
            logger.info("Trying 'Manage' -> 'Copy Icon' flow if main button not found.")
            try:
                page.get_by_role("button", name="Manage").click()
                page.wait_for_timeout(1000)
                page.locator("button[aria-label='CopyOutlineIcon']").first.click()
            except:
                page.screenshot(path="fail_collabs_copy.png")
                raise Exception("Could not find a copy trigger on Collabs page.")

    # 3. Verification happens via assertion_type: element_visible_by_text in YAML
    # But we can add an internal wait here for the toast to be sure
    page.wait_for_timeout(1000)
