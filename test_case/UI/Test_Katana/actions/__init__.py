
from .base import (
    open_url, 
    smart_click, 
    smart_fill, 
    smart_check, 
    smart_swipe, 
    smart_sleep,
    smart_press,
    smart_upload,
    smart_screenshot,
    wait_for_selector,
    wait_for_url,
    save_html,
    click_modal_close
)
from .module import click_module_edit_button, click_module_paragraph, click_add_new_product
from .product import (
    click_add_button_regex, verify_product_clickable, click_products_nav_icon,
    click_products_tab_t2129, click_bell_button, click_product_plus_button,
    click_product_image, verify_post_exists, R_click_follow, 
    click_close_toast, verify_toast_message
)
from .form import (
    verify_submission_details, verify_message_content, click_form_more_menu,
    click_submission_details_back, click_contact_form
)
from .layout import (
    verify_top_aligned_layout, verify_waterfall_layout,
    goto_storefront, publish_button_click, verify_navigation_after_publish,
    click_mui_svg_icon, click_products_text, wait_for_product_cards
)

# Registry for exact match keys
ACTIONS = {
    "open": open_url,
    # Generic overrides
    "click_modal_close": click_modal_close,
    "R_click": smart_click,
    "fill": smart_fill,
    "check": smart_check,
    "swipe": smart_swipe,
    "sleep": smart_sleep,
    "press": smart_press,
    "upload": smart_upload,
    "screenshot": smart_screenshot,
    
    # Module specific
    "click_module_edit_button": click_module_edit_button,
    "click_module_paragraph": click_module_paragraph,
    "click_add_new_product": click_add_new_product,
    
    # Product/Social specific
    "click_add_button_regex": click_add_button_regex,
    "click_add_button_regex_final": click_add_button_regex,
    "verify_product_clickable": verify_product_clickable,
    "click_products_nav_icon": click_products_nav_icon,
    "click_products_tab_t2129": click_products_tab_t2129,
    "click_bell_button": click_bell_button,
    "click_bell_button_reopen": click_bell_button, # Same handler
    "click_product_plus_button": click_product_plus_button,
    "click_product_image": click_product_image,
    "verify_post_exists": verify_post_exists,
    "R_click_follow": R_click_follow,
    
    # Form specific
    "verify_submission_details": verify_submission_details,
    "verify_message_content": verify_message_content,
    "verify_email_content": verify_message_content, # Reuse
    "verify_phone_content": verify_message_content, # Reuse
    "click_form_more_menu": click_form_more_menu,
    "click_submission_details_back": click_submission_details_back,
    "click_contact_form": click_contact_form,

    # Layout specific
    "verify_top_aligned_layout": verify_top_aligned_layout,
    "verify_waterfall_layout": verify_waterfall_layout,
    "verify_follow_message": verify_toast_message,
    "verify_unfollow_message": verify_toast_message,
    "verify_refollow_message": verify_toast_message,

    # T3370 Layout Specific
    "goto_storefront_top_aligned": goto_storefront,
    "goto_storefront_waterfall": goto_storefront,
    "publish_button_click_top_aligned": publish_button_click,
    "publish_button_click_waterfall": publish_button_click,
    "verify_navigation_after_publish_top_aligned": verify_navigation_after_publish,
    "verify_navigation_after_publish_waterfall": verify_navigation_after_publish,
    "click_mui_svg_icon_top_aligned": click_mui_svg_icon,
    "click_mui_svg_icon_waterfall": click_mui_svg_icon,
    "click_products_text_top_aligned": click_products_text,
    "click_products_text_waterfall": click_products_text,
    "wait_for_product_cards_top_aligned": wait_for_product_cards,
    "wait_for_product_cards_waterfall": wait_for_product_cards,
    "check_label_top_aligned": smart_check,
    "check_label_waterfall": smart_check,
}

def get_action(name):
    """
    Get action function by name.
    Supports exact match from ACTIONS registry,
    and fallback to smart handlers for prefixes.
    """
    # 1. Exact match
    if name in ACTIONS:
        return ACTIONS[name]
    
    # 2. Prefix mapping
    if name.startswith("R_click"):
        return smart_click
    elif name.startswith("fill"):
        return smart_fill
    elif name.startswith("check"):
        return smart_check
    elif name.startswith("swipe"):
        return smart_swipe
    elif name.startswith("sleep"):
        return smart_sleep
    elif name.startswith("press"):
        return smart_press
    elif name.startswith("upload") or name.startswith("wait_for_upload"):
        return smart_upload
    elif name.startswith("screenshot"):
        return smart_screenshot
    elif name.startswith("save_html") or name.startswith("save_full_html"):
        return save_html
    elif name.startswith("wait_for_selector"):
        return wait_for_selector
    elif name.startswith("wait_for_url") or name.startswith("verify_navigation"):
        return wait_for_url
    elif name.startswith("open"):
        return open_url
    
    # Special prefixes that map to specific functions
    if name.startswith("click_close_toast"):
        return click_close_toast
        
    # Add other prefix handlers here as we migrate them
    
    return None
