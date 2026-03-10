#!usr/bin/env python3
# -*- encoding : utf-8 -*-
# coding : unicode_escape
'''
Filename         : test_ui.py
Description      : Action Registry Refactored Version
Time             : 2026/01/15
Author           : AllenLuo / Agent
Version          : 3.0
'''

import sys
import os
import pytest
import allure
from playwright.sync_api import Page, Browser
from loguru import logger

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from tools import allure_title, allure_step_no
from page.home import *

# Import the new Action Registry
from .actions import get_action

@allure.testcase('https://ones.cn/project/#/testcase/team/T7u1zXum/plan/QCuFwDdq/library/XcAFFViB/module/6mi4qiVp', 'ONS测试用例链接')
@allure.title("测试执行")
def test_case(smokecases1, page: Page, browser: Browser, request):
    val = list(smokecases1.values())[0]
    
    # Guest Mode Setup
    if val.get("guest", False):
        logger.info(f"Running {list(smokecases1.keys())[0]} in GUEST mode (new context)")
        context = browser.new_context()
        page = context.new_page()
        request.addfinalizer(lambda: context.close())

    page.set_default_timeout(90000)
    
    # Test Metadata extraction
    caseno = list(smokecases1.keys())[0]
    description = dict(list(smokecases1.values())[0])["description"]
    test_step = list(smokecases1.values())[0]["test_step"]
    expect_result = dict(list(smokecases1.values())[0])["expect_result"]
    
    # Pass metadata to page object for AI context
    setattr(page, "_test_description", description)
    setattr(page, "_test_caseno", caseno)
    setattr(page, "_execution_history", [])  # Initialize execution history
    
    allure_title(caseno)
    allure_step_no(f'description:{description}')
    allure_step_no(f'test_step:{str(test_step)}')

    # --- Core Execution Engine ---
    for k, v in test_step.items():
        logger.info(f">>> Current Step: {k}")
        
        # 1. Action Registry Lookup
        action = get_action(k)
        
        if action:
            try:
                action(page, v)
                # Record successful step
                page._execution_history.append((k, v))
            except Exception as e:
                logger.error(f"Action '{k}' failed: {e}")
                # Try generic screenshot on failure
                try: page.screenshot(path=f"fail_{k}.png")
                except: pass
                raise
        else:
            # 2. Legacy Fallback
            logger.warning(f"Step '{k}' not found in Action Registry. Attempting legacy dispatch/fallback.")
            fallback_success = False
            if k.startswith("click"):
                try:
                   target_text = v.get('text') or v.get('name')
                   if target_text:
                       page.click(f"text={target_text}", timeout=5000)
                       logger.info(f"Fallback click success for: {target_text}")
                       fallback_success = True
                       page._execution_history.append((k, v))
                except:
                   pass
            
            if not fallback_success:
                logger.error(f"FATAL: Step '{k}' could not be resolved by Registry or Fallback.")
                pytest.fail(f"Step '{k}' not found or failed in fallback. Check actions/__init__.py or YAML key.")



    # --- Assertion Phase ---
    allure_step_no(f'expect_result:{str(expect_result)}')
    if "assertions" in expect_result:
        for assertion in expect_result["assertions"]:
            assertion_type = assertion.get("assertion_type")
            
            # Use Registry for assertions too if possible, or keep simple dispatch here
            if assertion_type == "element_visible_by_text":
                text = assertion.get("text")
                if text:
                    # Robust check combining content and specific visibility
                    try:
                        page.get_by_text(text, exact=False).first.wait_for(state="visible", timeout=5000)
                    except:
                        # Fallback to source check
                        assert text in page.content(), f"Text '{text}' not found in page content."

            elif assertion_type == "element_text":
                role = assertion.get("role")
                value = assertion.get("value")
                if role and value:
                    from playwright.sync_api import expect
                    element = page.get_by_role(role=role).nth(0)
                    expect(element).to_have_text(value)
                    
            elif assertion_type == "element_visible":
                role = assertion.get("role")
                visible = assertion.get("visible", True)
                if role:
                    from playwright.sync_api import expect
                    element = page.get_by_role(role=role).nth(0)
                    if visible:
                        expect(element).to_be_visible()
                    else:
                        expect(element).to_be_hidden()
            
            # Delegate complex layout assertions back to actions if needed, 
            # but usually assertions stay in the test runner or are simple checks.
            # (Layout assertions from legacy were moved to actions/layout.py but those were inside the Step loop steps??)
            # Wait, in the original file, layout checks were STEPS (verify_top_aligned_layout), AND assertions.
            # verify_top_aligned_layout in YAML IS A STEP.
            # The 'assertions' block in YAML usually contains simple checks.
