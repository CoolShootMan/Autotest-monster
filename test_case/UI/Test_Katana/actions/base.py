import os
import re
from playwright.sync_api import Page, Locator, expect
from loguru import logger
from page.home import page_element_role_click, page_element_label_click

def open_url(page: Page, v):
    logger.info(f">>> Current Step: open")
    url = v.get("open") if isinstance(v, dict) else v
    if url:
        from page.home import page_open
        page_open(page, url)

def swipe_avoid_plus(page: Page, v: dict):
    # Specialized action to scroll past specific UI elements
    x = v.get("x", 0)
    y = v.get("y", 300)
    page.mouse.wheel(x, y)
    page.wait_for_timeout(1000)

def smart_swipe(page: Page, v: dict):
    swipe_avoid_plus(page, v)

def smart_sleep(page: Page, v):
    ms = (v.get("sleep") or v.get("ms") or 1000) if isinstance(v, dict) else v
    page.wait_for_timeout(float(ms))

def smart_press(page: Page, v):
    key = (v.get("press") or v.get("key")) if isinstance(v, dict) else v
    if key:
        page.keyboard.press(key)

def smart_screenshot(page: Page, v: dict):
    name = v.get("name", "screenshot")
    page.screenshot(path=f"{name}.png")

def wait_for_selector(page: Page, v: dict):
    selector = v.get("selector") or v.get("locator")
    timeout = v.get("timeout", 30000)
    if selector:
        page.wait_for_selector(selector, timeout=timeout)

def wait_for_url(page: Page, v: dict):
    url = v.get("url") or v.get("verify_navigation")
    timeout = v.get("timeout", 30000)
    if url:
        if isinstance(url, str) and "*" in url:
            url = re.compile(url.replace("*", ".*"))
        page.wait_for_url(url, timeout=timeout)

def save_html(page: Page, v: dict):
    name = v.get("name", "page")
    with open(f"{name}.html", "w", encoding="utf-8") as f:
        f.write(page.content())

def smart_fill(page: Page, v: dict):
    target_name = v.get("name") or v.get("text") or v.get("label") or v.get("placeholder")
    target_value = v.get("value", "")
    target_locator = v.get("locator")
    
    logger.info(f"Filling field '{target_name or target_locator}' with value '{target_value}'")
    
    try:
        if target_locator:
            # Direct locator fill
            el = page.locator(target_locator).nth(v.get("index", 0))
            el.fill(str(target_value))
            logger.info(f"Filled by locator: {target_locator} (index: {v.get('index', 0)})")
        elif "role" in v:
            # Semantic fill
            page.get_by_role(v["role"], name=target_name, exact=v.get("exact", False)).nth(v.get("index", 0)).fill(str(target_value))
            logger.info(f"Filled by role+name: {target_name} = {target_value} (index: {v.get('index', 0)})")
        else:
            # Text/Placeholder fallback
            candidates = [
                page.get_by_label(target_name, exact=False),
                page.get_by_placeholder(target_name, exact=False),
                page.locator(f"input[name*='{target_name}'], textarea[name*='{target_name}']"),
                page.locator(f"input[placeholder*='{target_name}'], textarea[placeholder*='{target_name}']")
            ]
            target_id = v.get("index", 0)
            filled = False
            for c in candidates:
                target_el = c.nth(target_id)
                if target_el.is_visible():
                    target_el.fill(str(target_value))
                    logger.info(f"Filled by text/attr match: {target_name} (index: {target_id})")
                    filled = True
                    break
            if not filled:
                 # Last resort: generic placeholder
                 page.locator(f"input[placeholder*='{target_name}'], textarea[placeholder*='{target_name}'], input[aria-label*='{target_name}']").nth(target_id).fill(str(target_value))
        
        # Add small delay to avoid overwhelming the UI
        page.wait_for_timeout(300)
    except Exception as e:
        logger.error(f"Fill failed ({target_name}): {e}")
        try: page.screenshot(path=f"fail_fill.png")
        except: pass
        raise

def smart_check(page: Page, v: dict):
    target_name = v.get("name") or v.get("text") or v.get("label")
    target_locator = v.get("locator")
    target_role = v.get("role", "checkbox")
    checked = v.get("checked", True)
    
    logger.info(f"Checking '{target_name or target_locator}' to state: {checked}")
    if target_locator:
        page.locator(target_locator).nth(v.get("index", 0)).set_checked(checked)
    else:
        try:
            page.get_by_role(target_role, name=target_name).nth(v.get("index", 0)).set_checked(checked)
        except:
            page.get_by_label(target_name).nth(v.get("index", 0)).set_checked(checked)

def smart_upload(page: Page, v: dict):
    if "file_path" in v:
        file_path = v.get("file_path")
        if not os.path.exists(file_path):
             logger.error(f"File not found: {file_path}")
             raise FileNotFoundError(file_path)

        target_index = v.get("index", 0)
        try:
            if "locator" in v:
                el = page.locator(v["locator"]).nth(target_index)
                # Try setting files directly first (stable for hidden inputs)
                try:
                    el.set_input_files(file_path, timeout=3000)
                    logger.info(f"Uploaded file via set_input_files on locator: {v['locator']}")
                    return
                except:
                    # Fallback to click + chooser
                    with page.expect_file_chooser(timeout=5000) as fc_info:
                        el.click()
                    fc = fc_info.value
                    fc.set_files(file_path)
            else:
                target_name = v.get("text") or v.get("name") or v.get("label") or v.get("placeholder")
                # Try semantic search + chooser
                with page.expect_file_chooser(timeout=5000) as fc_info:
                    el = None
                    if target_name:
                        el = page.get_by_label(target_name).nth(target_index)
                        if not el.is_visible():
                            el = page.get_by_text(target_name, exact=True).nth(target_index)
                    
                    if not el:
                         raise Exception(f"Upload target not found: {target_name}")
                    
                    el.click()
                fc = fc_info.value
                fc.set_files(file_path)
            logger.info(f"Uploaded file: {file_path}")
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise

def smart_click(page: Page, v: dict):
    # Crash Check
    if page.get_by_text("Something went wrong!", exact=True).is_visible():
        logger.error(f"Application Crashed (Detected at start of click)!")
        page.screenshot(path=f"crash_click.png")
        raise Exception("Application Crashed")
        
    target_name = v.get("name") or v.get("text") or v.get("label") or v.get("placeholder")
    target_locator = v.get("locator")
    target_role = v.get("role")
    target_exact = v.get("exact", False)
    target_index = v.get("index", 0)
    force = v.get("force", False) # Default to False for better event triggering
    
    # Validation
    if not target_name and not target_locator and not target_role:
        logger.warning(f"No target specified for smart_click in step. Skipping.")
        return

    logger.info(f"Click started for target: {target_name or target_locator or target_role}")

    # 1. Targeted Locator (if provided) - Highest priority
    if target_locator:
        try:
            el = page.locator(target_locator).nth(target_index)
            el.click(force=force, timeout=5000)
            logger.info(f"Clicked target locator: {target_locator} (index: {target_index})")
            return
        except Exception as e:
            logger.debug(f"Direct locator click failed: {e}")

    # 2. Page-wide Semantic Search (Role/Text)
    try:
        el = None
        if target_role:
            el = page.get_by_role(role=target_role, name=target_name, exact=target_exact).nth(target_index)
        elif target_name:
            el = page.get_by_text(target_name, exact=target_exact).nth(target_index)
        
        if el:
            el.click(force=force, timeout=5000)
            logger.info(f"Clicked target '{target_name or 'unnamed'}' (index: {target_index}) via semantic search.")
            return
    except Exception as e:
        logger.debug(f"Standard click failed: {e}")

    # 3. Modal/Popover Fallback
    try:
        modals = page.locator("div[role='dialog'], .MuiDialog-root, .MuiPopover-root, .MuiModal-root, [role='presentation']").all()
        for m in reversed(modals):
            if m.is_visible():
                if target_role:
                    target_el = m.get_by_role(role=target_role, name=target_name, exact=target_exact).first
                else:
                    target_el = m.get_by_text(target_name, exact=target_exact).first
                
                if target_el.is_visible():
                    target_el.click(force=force)
                    logger.info("Clicked target inside visible modal/popover fallback.")
                    return
    except: pass

    # 4. Final Legacy Fallback
    logger.warning(f"R_click fallback triggered for '{target_name or target_locator}'")
    if target_locator:
        page.locator(target_locator).first.click(force=force)
    else:
        page_element_role_click(page=page, role=target_role, name=target_name, index=target_index, exact=target_exact, force=force)

def click_modal_close(page: Page, v: dict):
    logger.info("Attempting to close modal...")
    try:
        close_btn = page.locator("div[role='dialog'] button[aria-label='close'], .MuiDialog-root button.close").first
        if close_btn.is_visible():
            close_btn.click()
            logger.info("Clicked modal close button.")
        else:
            modal_visible = page.locator("div[role='dialog'], .MuiDialog-root, .MuiModal-root").first.is_visible()
            if modal_visible:
                page.keyboard.press("Escape")
                logger.info("Pressed Escape to close visible modal (fallback).")
            else:
                logger.info("No modal detected to close.")
        page.wait_for_timeout(1000)
    except Exception as e:
        logger.warning(f"Failed to close modal: {e}")
