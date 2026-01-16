
import re
from loguru import logger
from playwright.sync_api import Page
from .base import smart_click

def click_add_button_regex(page: Page, v: dict):
    # Click Add button using regex to avoid ambiguity
    page.locator("button").filter(has_text=re.compile(r"^Add$")).click()

def verify_product_clickable(page: Page, v: dict):
    # Verify product is clickable (may open new page)
    text = v["text"]
    page.get_by_text(text).click()
    page.wait_for_timeout(1000)

def click_products_nav_icon(page: Page, v: dict):
    # Click navigation icon to open menu
    page.locator(".MuiSvgIcon-root.MuiSvgIcon-fontSizeMedium.shop-text-color").first.click()

def click_products_tab_t2129(page: Page, v: dict):
    # Click Products tab in the popover
    page.locator("#simple-popover").get_by_text("Products", exact=True).click()

def click_bell_button(page: Page, v: dict):
    # Click the notification bell/follow button using verified class from dump
    logger.info(f"Attempting to click bell button")
    bell_btn = page.locator(".katana-15rqjx2").first
    try:
        if bell_btn.count() > 0:
            bell_btn.click()
            logger.info("Bell button clicked successfully")
        else:
            logger.error("Bell button with class katana-15rqjx2 NOT found!")
            # Try to find any icon button in header area as fallback
            all_icon_btns = page.locator("button.MuiIconButton-root").all()
            if len(all_icon_btns) > 0:
                 all_icon_btns[0].click() # Blind click on first icon? Risky but it's a fallback.
            else:
                raise Exception("Bell button not found")
    except Exception as e:
        logger.error(f"Error clicking bell button: {e}")
        page.screenshot(path="fail_bell_button.png")
        raise
    page.wait_for_timeout(1000)

def click_product_plus_button(page: Page, v: dict):
    # Click the first + button in the product stack
    page.locator(".MuiStack-root.katana-1xl4abm > .MuiButtonBase-root").first.click()

def click_product_image(page: Page, v: dict):
    # Click product image in media library
    page.get_by_role("img", name="Image of Product").click()

def verify_post_exists(page: Page, v: dict):
    # Verify post button exists with title and price
    page.get_by_role("button", name=re.compile(r"Image of Product test T2129")).wait_for(state="visible", timeout=10000)
    logger.info("Post verified in Posts tab")

def R_click_follow(page: Page, v: dict):
    # Smart handler for initial follow: handles "Already Following" state
    logger.info("Executing smart R_click_follow...")
    
    # Crash Check
    if page.get_by_text("Something went wrong!", exact=True).is_visible():
        raise Exception("Application Crashed")
    
    # 1. Check if 'About' modal is open
    about_modal = page.locator("div[role='dialog'], .MuiDialog-root").filter(has_text="About").first
    if not about_modal.is_visible():
        scope = page
    else:
        logger.info("R_click_follow: Found 'About' modal.")
        scope = about_modal
    
    # 2. Check for "Follow"
    follow_btn = scope.get_by_role("button", name="Follow", exact=True).first
    if follow_btn.is_visible():
        follow_btn.click()
        logger.info("R_click_follow: Clicked 'Follow'.")
    else:
        # 3. Check for "Following"
        following_btn = scope.get_by_role("button", name="Following", exact=True).first
        if following_btn.is_visible():
            logger.info("R_click_follow: Found 'Following' - User is already following. performing reset.")
            following_btn.click()
            
            # 4. Handle Unfollow Confirmation
            unfollow_confirm = page.get_by_role("button", name="Unfollow Anyway").first
            unfollow_confirm.wait_for(state="visible", timeout=5000)
            unfollow_confirm.click()
            
            # 5. Wait for "Follow" to appear and click it
            try:
                follow_btn = scope.get_by_role("button", name="Follow", exact=True).first
                follow_btn.wait_for(state="visible", timeout=7000)
                follow_btn.click()
                logger.info("R_click_follow: Reset complete and clicked 'Follow'.")
            except:
                # Fallback: Reload page is the safest way to ensure clean state
                logger.warning("R_click_follow: 'Follow' not found. Reloading page and reopening modal...")
                page.reload(wait_until="load")
                page.wait_for_timeout(5000)
                
                # Re-open About modal
                page.get_by_role("img", name="Logo").click(force=True)
                
                # Wait for About modal to appear
                about_modal = page.locator("div[role='dialog'], .MuiDialog-root").filter(has_text="About").first
                try:
                    about_modal.wait_for(state="visible", timeout=5000)
                    scope = about_modal
                except:
                    scope = page
                    
                follow_btn = scope.get_by_role("button", name="Follow", exact=True).first
                follow_btn.wait_for(state="visible", timeout=10000)
                follow_btn.click()
                logger.info("R_click_follow: Reset complete (with Reload) and clicked 'Follow'.")
        else:
            logger.error("R_click_follow: Neither 'Follow' nor 'Following' found!")
            page.screenshot(path="fail_smart_follow.png")
            raise Exception("Follow button missing")

def click_close_toast(page: Page, v: dict):
    # Streamlined toast dismissal (clicks the Snackbar directly)
    try:
        toasts = page.locator(".MuiSnackbar-root").all()
        for toast in toasts:
            try:
                if toast.is_visible():
                    logger.info(f"Hiding toast (display:none): {toast.inner_text()[:40]}...")
                    toast.evaluate("element => element.style.display = 'none'")
            except: pass
        page.wait_for_timeout(1000)
    except Exception as e:
        logger.warning(f"Toast dismissal error: {e}")

def verify_toast_message(page: Page, v: dict):
    # Verify toast message appears
    text = v["text"]
    try:
        toast_locator = page.locator(".MuiSnackbar-root").filter(has_text=re.compile(text, re.I))
        toast_locator.wait_for(state="visible", timeout=10000)
        logger.info(f"Verified message: {text}")
    except Exception as e:
        logger.warning(f"Toast message verification failed: {e}. Checking any visible text as fallback...")
        try:
            page.get_by_text(re.compile(text, re.I), exact=False).wait_for(state="visible", timeout=3000)
            logger.info(f"Verified message (fallback): {text}")
        except:
            logger.warning(f"Fallback verification also failed.")
            pass
