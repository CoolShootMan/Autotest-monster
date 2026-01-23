
import re
from loguru import logger
from playwright.sync_api import Page

def click_module_edit_button(page: Page, v: dict):
    # Click edit button on specific module using regex filter
    module_name = v.get("module_name")
    logger.info(f"Attempting to find edit button for module: {module_name}")
    try:
        # Try specific module name if provided
        module_div = page.locator("div").filter(has_text=re.compile(f"{module_name}", re.I)).filter(has_text="Add new").last
        module_div.get_by_role("button").nth(2).click(timeout=10000)
        logger.info(f"Successfully clicked edit button for {module_name}")
    except Exception as e:
        logger.warning(f"Failed to find edit button for {module_name} with primary locator: {e}. Trying fallback...")
        try:
            # Broad fallback: look for the second button in a div that contains the module name
            page.locator("div").filter(has_text=re.compile(f"{module_name}", re.I)).get_by_role("button").nth(2).click(timeout=5000)
            logger.info(f"Successfully clicked edit button for {module_name} (fallback)")
        except:
            logger.error(f"Failed to find edit button for {module_name} (FATAL).")
            raise

def click_module_paragraph(page: Page, v: dict):
    # Click on module paragraph
    page.get_by_role("paragraph").filter(has_text=v["text"]).click()

def click_add_new_product(page: Page, v: dict):
    # Click "Add new" button within specific module
    module_name = v.get("module_name")
    page.locator("div").filter(has_text=re.compile(f"^{module_name}Add new$")).get_by_role("button").first.click()
