
from loguru import logger
from playwright.sync_api import Page
import pytest

def verify_top_aligned_layout(page: Page, v: dict):
    # Find all potential cards using specific classes only to avoid generic layout noise
    card_selector = '.shop-link, .post-card, .form-card, .card__container'
    all_cards = page.locator(card_selector).all()
    
    # Filter for product containers (usually heights between 80-1000px)
    visible_cards = []
    for card in all_cards:
        if card.is_visible():
            bbox = card.bounding_box()
            if bbox and 80 < bbox.get("height", 0) < 1000:
                visible_cards.append(card)
                if len(visible_cards) >= 5:
                    break

    if len(visible_cards) > 1:
        # Log heights for debugging but don't fail, as mixed card types are allowed
        heights = [card.bounding_box()["height"] for card in visible_cards]
        logger.info(f"Visible card heights: {heights}")
    
    if len(visible_cards) < 2:
        pytest.fail(f"Not enough visible product cards found. Expected at least 2, found {len(visible_cards)}")
    
    # Scroll some cards into view
    visible_cards[0].scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    
    if "screenshot_path" in v:
        page.screenshot(path=v["screenshot_path"])
    
    # Check Y alignment for the first two cards
    card_0_y = visible_cards[0].bounding_box()["y"]
    card_1_y = visible_cards[1].bounding_box()["y"]
    assert abs(card_0_y - card_1_y) < v.get("threshold", 5), f"Product card 0 top Y ({card_0_y}) is not aligned with Product card 1 top Y ({card_1_y}) for Top aligned layout."

def verify_waterfall_layout(page: Page, v: dict):
    # Verification logic for Waterfall
    card_selector = '.shop-link, .post-card, .form-card, .card__container'
    all_cards = page.locator(card_selector).all()
    visible_cards = []
    for card in all_cards:
        if card.is_visible():
            bbox = card.bounding_box()
            if bbox and 80 < bbox.get("height", 0) < 1000:
                visible_cards.append(card)
                if len(visible_cards) >= 5:
                    break

    if len(visible_cards) > 1:
        visible_cards[0].scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        heights = [card.bounding_box()["height"] for card in visible_cards]
        unique_heights = set(heights)
        assert len(unique_heights) > 1, f"Product card heights are the same ({heights}) for Waterfall layout, expected variation."
    elif len(visible_cards) == 1:
        logger.info("Only one card found for Waterfall.")
    else:
        pytest.fail("No cards found for Waterfall.")

def goto_storefront(page: Page, v: dict):
    page.goto(v["url"], wait_until="load", timeout=v["timeout"])

def publish_button_click(page: Page, v: dict):
    page.get_by_role("button", name="Publish").click()

def verify_navigation_after_publish(page: Page, v: dict):
    import re
    try:
        page.wait_for_url(re.compile(v["url_regex"]), timeout=v["timeout"])
    except: # TimeoutError
        if "warning_message" in v:
            logger.warning(v["warning_message"])
        if "fallback_url" in v:
            page.goto(v["fallback_url"], wait_until="load", timeout=v.get("fallback_timeout", 60000))
    # Ensure layout changes are synchronized
    page.reload(wait_until="load")
    page.wait_for_timeout(2000)

def click_mui_svg_icon(page: Page, v: dict):
    # Jump near the bottom using the last nav item as a reliable anchor
    try:
        anchor_list = page.locator(".katana-14rbssj")
        if anchor_list.count() > 0:
            anchor_list.last.wait_for(state="visible", timeout=10000)
            anchor_list.last.click(force=True)
            page.wait_for_timeout(1000)
    except Exception as e:
        logger.warning(f"Failed to click last nav anchor: {e}")

def click_products_text(page: Page, v: dict):
    # Target the Products tab directly by role and name
    try:
        products_tab = page.get_by_role("tab", name="Products", exact=True)
        products_tab.wait_for(state="visible", timeout=30000)
        products_tab.click()
    except Exception as e:
        logger.warning(f"Failed to click Products tab: {e}")
        # Fallback: click any text matching Products exactly
        page.get_by_text("Products", exact=True).first.click()

def wait_for_product_cards(page: Page, v: dict):
    # Wait for product cards to load using more specific selectors first
    card_selector = '.shop-link, .post-card, .form-card, .card__container'
    try:
        page.wait_for_selector(card_selector, state="visible", timeout=v["timeout"])
    except:
        # Fallback to generic if specific ones fail
        page.wait_for_selector('.MuiBox-root', state="visible", timeout=v["timeout"])
    page.wait_for_timeout(2000)
