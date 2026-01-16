
import re
import os
import time
from loguru import logger
from playwright.sync_api import Page, expect
from page.home import *

def open_url(page: Page, v: str):
    logger.info(f">>> Current Step: open")
    page_open(page, url=v)

def smart_sleep(page: Page, v: int):
    page.wait_for_timeout(v)

def smart_swipe(page: Page, v: dict):
    page_swipe(page, v.get("x", 0), v.get("y", 0))

def smart_press(page: Page, v: dict):
    page_element_input_role_press(page=page, role=v["role"], key=v["key"])

def smart_check(page: Page, v: dict):
    target_el = None
    if "role" in v:
        target_el = page.get_by_role(role=v["role"], name=v.get("name"), exact=v.get("exact", False))
    elif "label" in v:
        target_el = page.get_by_label(v["label"])
    elif "placeholder" in v:
        target_el = page.get_by_placeholder(v["placeholder"])
    
    if target_el:
        target_el.check(force=True)
        logger.info(f"Checked element: {v.get('name') or v.get('label') or v.get('placeholder')}")

def smart_upload(page: Page, v: dict):
    # Handle both upload trigger and wait_for_upload
    if "file_path" in v:
        with page.expect_file_chooser() as fc_info:
            page.get_by_text(v.get("text"), exact=True).click()
        fc = fc_info.value
        fc.set_files(v.get("file_path"))
        logger.info(f"Uploaded file via chooser: {v.get('file_path')}")
    elif "timeout" in v:
        # wait_for_upload_and_ui_update logic
        page.wait_for_event("response", lambda response: "/upload" in response.url and response.status == 200)
        page.wait_for_timeout(v.get("timeout", 2000))

def smart_screenshot(page: Page, v: dict):
    screenshot_name = v.get("name", "screenshot.png")
    page.screenshot(path=os.path.join("test-result", screenshot_name))

def save_html(page: Page, v: dict):
    html_name = v.get("name", "page.html")
    with open(os.path.join("test-result", html_name), "w", encoding="utf-8") as f:
        f.write(page.content())

def wait_for_selector(page: Page, v: dict):
    timeout = v.get("timeout", 5000)
    state = v.get("state", "visible") if "state" in v else None
    if state:
        page.wait_for_selector(v["selector"], state=state, timeout=timeout)
    else:
        page.wait_for_selector(v["selector"], timeout=timeout)

def wait_for_url(page: Page, v: dict):
    timeout = v.get("timeout", 10000)
    if "url" in v:
        page.wait_for_url(v["url"], timeout=timeout)
    elif "url_regex" in v:
        page.wait_for_url(re.compile(v["url_regex"]), timeout=timeout)

def smart_fill(page: Page, v: dict):
    k = "fill" # Placeholder for logging
    target_value = v.get("value")
    target_name = v.get("name")
    target_role = v.get("role", "textbox")
    target_exact = v.get("exact", False)
    target_locator = v.get("locator")
    target_placeholder = v.get("placeholder")
    
    try:
        # 1. Try explicit placeholder if provided
        if target_placeholder:
            try:
                page.get_by_placeholder(target_placeholder).fill(target_value, timeout=5000)
                logger.info(f"Filled by placeholder: {target_placeholder}")
                return
            except Exception as e:
                logger.debug(f"Placeholder fill failed: {e}")
                if not target_locator and not target_name: raise

        # 2. Try explicit locator if provided
        if target_locator:
            try:
                page.locator(target_locator).fill(target_value, timeout=5000)
                logger.info(f"Filled by locator: {target_locator}")
                return
            except Exception as e:
                logger.debug(f"Locator fill failed: {e}")
                if not target_name: raise

        # 3. Fallback to name/role/label logic
        if target_name or target_role:
            # Systematically try locators from specific to general
            try:
                # 1. Direct role + name
                page.get_by_role(role=target_role, name=target_name, exact=target_exact).fill(target_value, timeout=5000)
                page.keyboard.press("Tab")
                logger.info(f"Filled by role+name: {target_name} = {target_value}")
            except:
                try:
                    # 2. Get by label text
                    page.get_by_label(target_name, exact=target_exact).first.fill(target_value, timeout=5000)
                    page.keyboard.press("Tab")
                    logger.info(f"Filled by label: {target_name} = {target_value}")
                except:
                    try:
                        # 3. Get by placeholder (using name text as placeholder fallback)
                        page.get_by_placeholder(target_name, exact=target_exact).first.fill(target_value, timeout=5000)
                        page.keyboard.press("Tab")
                        logger.info(f"Filled by placeholder fallback: {target_name} = {target_value}")
                    except:
                        try:
                            # 4. Case-insensitive role match
                            page.get_by_role(role=target_role, name=re.compile(target_name, re.I)).first.fill(target_value, timeout=5000)
                            page.keyboard.press("Tab")
                            logger.info(f"Filled by role+regex: {target_name} = {target_value}")
                        except:
                            # 5. Target input by associated label text anywhere nearby
                            try:
                                # Find label element
                                label_el = page.locator("label").filter(has_text=re.compile(target_name, re.I)).first
                                if label_el.is_visible():
                                    # If it has a 'for' attribute, find it
                                    for_id = label_el.get_attribute("for")
                                    if for_id:
                                        page.locator(f"#{for_id}").fill(target_value)
                                    else:
                                        # Otherwise it might be an ancestor of the input, or just near it
                                        # Try input inside or following the label
                                        input_in_label = label_el.locator("input, textarea").first
                                        if input_in_label.is_visible():
                                            input_in_label.fill(target_value)
                                        else:
                                            # Try next sibling
                                            page.locator("label").filter(has_text=re.compile(target_name, re.I)).locator("xpath=./following::input | ./following::textarea").first.fill(target_value)
                                else: raise Exception("Label not visible")
                            except:
                                # 6. Final attempt: find any input that has this text as its aria-label or placeholder
                                page.locator(f"input[placeholder*='{target_name}'], textarea[placeholder*='{target_name}'], input[aria-label*='{target_name}']").first.fill(target_value)
        else:
            logger.warning(f"Unknown fill format: {v}")
    except Exception as e:
        logger.error(f"Fill failed ({target_name}): {e}")
        page.screenshot(path=f"fail_fill.png")
        raise

def smart_click(page: Page, v: dict):
    # Support "test_ui.py" specialized fallback keys passed as v (legacy) 
    # but initially we assume v contains keys like role, name, etc.
    
    k = "R_click" # Placeholder
    
    if page.is_closed():
        logger.error(f"Page is closed. Cannot proceed with click")
        raise Exception("PageClosed")
    
    # Crash Check
    if page.get_by_text("Something went wrong!", exact=True).is_visible():
        logger.error(f"Application Crashed (Detected at start of click)!")
        page.screenshot(path=f"crash_click.png")
        raise Exception("Application Crashed")
        
    try:
        # Optional debug screenshot
        # page.screenshot(path="debug_before_click.png")
        pass
    except: pass
    
    logger.info(f"Click started for target: {v.get('name')}")
    clicked_in_modal = False
    for _ in range(3): 
        try:
            # Target all potential modal containers
            modals = page.locator("div[role='dialog'], .MuiDialog-root, [role='presentation'] .MuiPaper-root").all()
            
            # If multiple modals, find the one that contains our target
            best_modal = None
            target_role = v.get("role")
            target_name = v.get("name") or v.get("text") # Support text-only targets
            target_exact = v.get("exact", False)
            target_index = v.get("index", 0)
            
            for m in modals:
                try:
                    # CRITICAL: Exclude snackbars from being treated as business modals (Ancestry check)
                    if m.locator("xpath=ancestor-or-self::*[contains(@class, 'MuiSnackbar-root')]").count() > 0:
                        continue
                    if m.get_attribute("class") and "MuiSnackbar-root" in m.get_attribute("class"):
                        continue

                    if m.is_visible():
                        # Check if target is inside THIS modal
                        if target_role:
                            target_check = m.get_by_role(role=target_role, name=target_name, exact=target_exact).first
                            if target_check.is_visible():
                                best_modal = m
                                logger.info(f"Found modal containing target '{target_name}'")
                                break
                        
                        # Fallback text check
                        if target_name and m.get_by_text(target_name, exact=target_exact).first.is_visible():
                            best_modal = m
                            logger.info(f"Found modal containing target text '{target_name}'")
                            break
                except: pass
            
            # If no specific modal found with target, use the first visible one (legacy behavior)
            if not best_modal and modals:
                for m in modals:
                    try:
                        if m.is_visible() and "MuiSnackbar-root" not in (m.get_attribute("class") or ""):
                            best_modal = m
                            break
                    except: pass

            if best_modal and best_modal.is_visible():
                logger.info("Modal detected. Waiting for content...")
                page.wait_for_timeout(1000)
                
                # --- Modal Click Core ---
                if target_role:
                    target_candidates = best_modal.get_by_role(role=target_role, name=target_name, exact=target_exact).all()
                else:
                    target_candidates = best_modal.get_by_text(target_name, exact=target_exact).all()
                
                if len(target_candidates) > 0:
                    # Handle index (including negative ones like -1)
                    idx = target_index if target_index >= 0 else len(target_candidates) + target_index
                    if 0 <= idx < len(target_candidates):
                        target_in_modal = target_candidates[idx]
                        try:
                            target_in_modal.wait_for(state="visible", timeout=5000)
                            target_in_modal.click(force=True)
                            logger.info(f"Target '{target_name}' (index: {target_index}) clicked inside modal.")
                            clicked_in_modal = True
                            break
                        except: pass

                # Fallback within modal if indexed click failed
                for c in target_candidates:
                    if c.is_visible():
                        c.click(force=True)
                        logger.info(f"Target '{target_name}' (first visible fallback) clicked inside modal.")
                        clicked_in_modal = True
                        break
                
                if clicked_in_modal: break

                # If not the target, maybe it's the 'About' header just being annoying (blocking other things)
                about_header = page.get_by_text("About", exact=True).first
                if about_header.is_visible():
                    logger.info("About modal detected but target not found in it. Dismissing.")
                    # Close it
                    close_btn = best_modal.get_by_role("button").first
                    if not close_btn or not close_btn.is_visible():
                            close_btn = best_modal.get_by_role("button").filter(has_text=re.compile(r"^$", re.I)).first
                    
                    if close_btn.is_visible():
                        close_btn.click(force=True)
                        logger.info("Dismissed 'About' modal")
                        page.wait_for_timeout(1000)
                        continue # Check again if it's gone
            
            break # No more modals, proceed
        except Exception as e:
            logger.debug(f"Modal handling attempt failed: {e}")
            break
    
    if clicked_in_modal:
        return

    # If not clicked in modal, try normal click
    page.wait_for_timeout(500) # Final safety wait
    try:
        # Prioritize visible targets to avoid hidden modal elements
        target_role = v.get("role")
        target_name = v.get("name") or v.get("text")
        target_exact = v.get("exact", False)
        target_index = v.get("index", 0)
        
        candidates = []
        if target_role:
            candidates = page.get_by_role(target_role, name=target_name, exact=target_exact).all()
        else:
            candidates = page.get_by_text(target_name, exact=target_exact).all()

        clicked_visible = False
        if len(candidates) > 0:
            # Target specific index if visible (respecting negative indices)
            try:
                idx = target_index if target_index >= 0 else len(candidates) + target_index
                if 0 <= idx < len(candidates) and candidates[idx].is_visible():
                    candidates[idx].click(force=True)
                    logger.info(f"R_click: Clicked target '{target_name}' (index: {target_index}) directly.")
                    clicked_visible = True
            except: pass
        
        if not clicked_visible:
            # Fallback: click first visible candidate
            for c in candidates:
                    if c.is_visible():
                        c.click(force=True)
                        logger.info(f"R_click: Clicked first visible candidate '{target_name}' instead of index {target_index}.")
                        clicked_visible = True
                        break
        
        if not clicked_visible:
            # Specific fallback for T1520 'Following' button which might be an icon
            found_icon = False
            if target_name == "Following":
                logger.info("Visible 'Following' text button not found. Trying to find 'Following' icon...")
                # Try common following state icons (MUI)
                for icon_name in ["PersonIcon", "HowToRegIcon", "CheckIcon", "PersonAddIcon"]:
                    icon_btn = page.locator("button").filter(has=page.locator(f"svg[data-testid='{icon_name}']")).first
                    if icon_btn.is_visible():
                        icon_btn.click(force=True)
                        logger.info(f"Clicked 'Following' icon button (icon: {icon_name}).")
                        found_icon = True
                        break
            
            if not found_icon:
                logger.warning(f"R_click fallback: No visible target '{target_name}' found. Trying legacy click...")
                page_element_role_click(page=page, role=v.get("role"), name=v.get("name"), index=v.get("index"), exact=v.get("exact", False), force=True)
    
    except Exception as e:
        logger.error(f"Click failed ({v.get('name')}): {e}")
        try: page.screenshot(path=f"fail_click.png")
        except: pass
        raise

def click_modal_close(page: Page, v: dict):
    logger.info("Attempting to close modal...")
    try:
        # Try finding a common close button
        close_btn = page.locator("div[role='dialog'] button[aria-label='close'], .MuiDialog-root button.close").first
        if close_btn.is_visible():
            close_btn.click()
            logger.info("Clicked modal close button.")
        else:
            # Fallback to Escape
            page.keyboard.press("Escape")
            logger.info("Pressed Escape to close modal (fallback).")
        page.wait_for_timeout(1000)
    except Exception as e:
        logger.warning(f"Failed to close modal: {e}")
