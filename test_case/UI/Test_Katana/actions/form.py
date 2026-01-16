
import re
from loguru import logger
from playwright.sync_api import Page

def verify_submission_details(page: Page, v: dict):
    page.get_by_role("heading", name=v["name"]).wait_for(state="visible", timeout=5000)
    logger.info("Submission details page verified.")

def verify_message_content(page: Page, v: dict):
    # Check for specific text content
    target_text = v["text"]
    try:
        # Try direct locator first
        page.get_by_text(target_text, exact=False).wait_for(state="visible", timeout=3000)
        logger.info(f"Verified content (direct): {target_text[:30]}...")
    except:
        # Fallback to checking body text (handles text split by internal tags)
        logger.warning(f"Direct verification failed for '{target_text[:30]}...', checking body text...")
        page.wait_for_timeout(1000)
        body_text = page.locator("body").inner_text()
        if target_text in body_text:
            logger.info(f"Verified content (body search): {target_text[:30]}...")
        else:
            logger.error(f"Content verification failed. Pattern not found in body text.")
            page.screenshot(path=f"fail_verify_message.png")
            raise Exception(f"Content verification failed")

def click_form_more_menu(page: Page, v: dict):
    form_name = v.get("form_name")
    logger.info(f"Clicking More menu for form: {form_name}")
    try:
        # Confirmed locator strategy from v5 diagnostic
        # Find the row container that has the form name and at least one button
        container = page.locator("div").filter(has=page.get_by_text(form_name, exact=True)).filter(has=page.get_by_role("button")).last
        more_btn = container.get_by_role("button").first
        
        more_btn.scroll_into_view_if_needed()
        more_btn.click()
        logger.info(f"More menu for {form_name} clicked.")
        
        # Check for "View submissions" visibility (for logging)
        page.wait_for_timeout(1000)
    except Exception as e:
        logger.warning(f"Failed to find More menu for {form_name}: {e}. Trying broad search...")
        # Fallback: find any button near the text
        try:
            text_el = page.get_by_text(form_name, exact=True).first
            box = text_el.bounding_box()
            if box:
                # Find buttons around the same Y coordinate
                page.get_by_role("button").filter(has=page.locator(f"xpath=//ancestor::div[abs(number(@y)-{box['y']})<50]")).first.click()
                logger.info("Clicked first button near form text as fallback.")
            else: raise Exception("No bounding box")
        except:
            page.screenshot(path=f"fail_form_more_{form_name}.png")
            raise

def click_submission_details_back(page: Page, v: dict):
    try:
        page.locator("div").filter(has_text=re.compile(r"^Submission details$")).get_by_role("button").first.click()
        logger.info("Clicked back from submission details via header button.")
    except:
        page.keyboard.press("Escape")
        logger.info("Used Escape key to close submission details as fallback.")

def click_contact_form(page: Page, v: dict):
    page.locator("div").filter(has_text="Auto test form").last.click()
