import os
import re
from playwright.sync_api import Page, Locator, expect
from loguru import logger
from page.home import page_element_role_click, page_element_label_click
from ..utils.ai_vision import ai_vision

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
    logger.info(f"Swiping/Scrolling: x={x}, y={y}")
    
    # Check if a drawer is open. If so, try to scroll it.
    drawer = page.locator(".MuiDrawer-root div").filter(has=page.locator("[data-som-id], input")).first
    if drawer.is_visible():
        logger.info("Active drawer detected. Scrolling drawer content...")
        # Common MUI drawer content container often has the overflow
        drawer.evaluate(f"el => el.scrollBy({x}, {y})")
    else:
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
    
    # Timeout for traditional fill - trigger AI faster
    fill_timeout = v.get("timeout", 15000)

    try:
        if target_locator:
            # Direct locator fill
            el = page.locator(target_locator).nth(v.get("index", 0))
            el.fill(str(target_value), timeout=fill_timeout)
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
        logger.error(f"Fill failed ({target_name}): {e}. Attempting AI Self-Healing...")
        try:
            safe_name = re.sub(r'[^\w\-]', '_', str(target_name or 'field'))[:30]
            
            # --- HYBRID SOM UPGRADE ---
            logger.info("AI Healing Step 1: Loading som.js")
            som_js_path = os.path.join(os.path.dirname(__file__), "../utils/som.js")
            with open(som_js_path, "r") as f: som_code = f.read()
            
            logger.info("AI Healing Step 2: Injecting labels")
            mapping = page.evaluate(som_code)
            logger.info(f"AI Healing Step 3: SOM Tagging Complete. Elements: {len(mapping)}")
            
            screenshot_path = f"fail_fill_{safe_name}.png"
            page.screenshot(path=screenshot_path)
            
            # Pass objective context
            test_objective = getattr(page, "_test_description", "UI Filling")
            som_data_meta = {
                "description": test_objective,
                "caseno": getattr(page, "_test_caseno", "Unknown"),
                "history": getattr(page, "_execution_history", [])
            }
            
            instruction = f"The input field/textbox that corresponds to '{target_name or target_locator}'. Use the value '{target_value}'."
            res = ai_vision.find_element_som(screenshot_path, instruction, {**mapping, **som_data_meta})
            
            if res.get("label_id"):
                label_id = res["label_id"]
                diagnosis = res.get("consciousness_diagnosis", "No diagnosis provided.")
                action_type = res.get("suggested_action", "GOAL_CLICK")
                
                logger.info(f"✨ AI 'Junior QA' Found Field ID: {label_id}!")
                logger.info(f"🧠 Diagnosis: {diagnosis}")
                logger.info(f"🚀 Suggested Action: {action_type}")
                
                if action_type == "ABORT_TEST":
                    logger.error(f"🛑 AI decided to ABORT test: {res.get('bug_report', diagnosis)}")
                    raise Exception(f"AI Aborted Test: {res.get('bug_report', diagnosis)}")

                el = page.locator(f'[data-som-id="{label_id}"]').first
                
                # Check if we need to click something first (Recovery)
                if action_type == "RECOVERY_CLICK":
                    logger.info("🔄 Performing recovery click before filling...")
                    el.click()
                    page.wait_for_timeout(2000)
                    # Retry fill
                    return smart_fill(page, v)

                el.fill(str(target_value))
                return
            else:
                logger.warning(f"AI SOM could not find field '{target_name}'. Result: {res}")
        except Exception as ai_err:
            logger.error(f"AI Healing failed: {ai_err}")
            
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

    # Regex Pre-processing
    if target_name and isinstance(target_name, str) and (target_name.startswith("^") or target_name.endswith("$")):
        target_name = re.compile(target_name)
    if target_locator and isinstance(target_locator, str) and (target_locator.startswith("^") or target_locator.endswith("$")):
        target_locator = re.compile(target_locator)

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

    # 4. Legacy Fallback (if page_element_role_click exists)
    else:
        try:
            page_element_role_click(page=page, role=target_role, name=target_name, index=target_index, exact=target_exact, force=force)
            return
        except Exception as e:
             logger.warning(f"Legacy fallback click failed: {e}")

    # 5. --- AI Self-Healing Fallback (The "Brain") ---
    logger.error(f"All traditional methods failed for '{target_name or target_locator}'. Triggering AI Self-Healing...")
    try:
        safe_name = re.sub(r'[^\w\-]', '_', str(target_name or 'target'))[:30]
        
        # --- HYBRID SOM UPGRADE ---
        som_js_path = os.path.join(os.path.dirname(__file__), "../utils/som.js")
        with open(som_js_path, "r") as f: som_code = f.read()
        
        mapping = page.evaluate(som_code)
        screenshot_path = f"ai_healing_{safe_name}.png"
        page.screenshot(path=screenshot_path)
        
        if target_name:
            description = f"The interactive element (button, link, icon, or menu item) for '{target_name}'. Look for visual matches even if the text doesn't match perfectly."
        else:
            description = f"The primary interactive element related to the goal. It might be a button, dropdown or trigger (Context: {target_role or target_locator})."
            
        # Add objective context for Junior QA Consciousness
        test_objective = getattr(page, "_test_description", "Unknown Action")
        som_data_meta = {
            "description": test_objective,
            "caseno": getattr(page, "_test_caseno", "Unknown"),
            "history": getattr(page, "_execution_history", [])
        }
        
        res = ai_vision.find_element_som(screenshot_path, description, {**mapping, **som_data_meta})
        
        if res.get("label_id"):
            label_id = res["label_id"]
            diagnosis = res.get("consciousness_diagnosis", "No diagnosis provided.")
            action_type = res.get("suggested_action", "GOAL_CLICK")
            
            logger.info(f"✨ AI 'Junior QA' Found Target ID: {label_id}!")
            logger.info(f"🧠 Diagnosis: {diagnosis}")
            logger.info(f"🚀 Suggested Action: {action_type}")
            
            if action_type == "ABORT_TEST":
                logger.error(f"🛑 AI decided to ABORT test: {res.get('bug_report', diagnosis)}")
                raise Exception(f"AI Aborted Test: {res.get('bug_report', diagnosis)}")

            el = page.locator(f'[data-som-id="{label_id}"]').first
            
            # Check if this is a 'recovery' action (like closing a blocking modal)
            is_recovery = (action_type == "RECOVERY_CLICK")
            if not is_recovery:
                # Fallback check based on name/role if AI didn't specify
                text = (el.inner_text() or "").lower()
                aria = (el.get_attribute("aria-label") or "").lower()
                if any(k in text or k in aria for k in ["close", "dismiss", "got it", "skip", "ok"]):
                    if target_name and not any(k in target_name.lower() for k in ["close", "dismiss", "got it", "skip", "ok"]):
                        is_recovery = True
            
            el.click()
            page.wait_for_timeout(2000)
            
            if is_recovery:
                logger.info(f"🔄 Recovery action performed. Retrying original click for '{target_name}'...")
                if v.get("_retry_ai", 0) < 1:
                    v["_retry_ai"] = v.get("_retry_ai", 0) + 1
                    return smart_click(page, v)
            return
        else:
            logger.error(f"💀 AI SOM could not locate the element. Logic ends here.")
    except Exception as ai_err:
        logger.error(f"AI Healing Error: {ai_err}")

    # If even AI fails, re-raise original or fail
    if v.get("_retry_ai", 0) > 0:
        return # We already tried
    raise Exception(f"Failed to click '{target_name or target_locator}' after all attempts including AI.")

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
def verify_text_visible(page: Page, v: dict):
    # Verify a specific text is visible on the page
    text = v.get("text")
    timeout = v.get("timeout", 10000)
    logger.info(f"Verifying visibility of text: {text}")
    try:
        page.get_by_text(text, exact=v.get("exact", False)).first.wait_for(state="visible", timeout=timeout)
        logger.info(f"Text '{text}' is visible.")
    except Exception as e:
        logger.error(f"Verification failed: Text '{text}' not visible after {timeout}ms. Error: {e}")
        page.screenshot(path=f"fail_verify_text_{text[:10]}.png")
        raise AssertionError(f"Text '{text}' not found or not visible.")
