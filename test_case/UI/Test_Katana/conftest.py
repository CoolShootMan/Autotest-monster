#!usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
Filename         : conftest.py
Description      :
Time             : 2023/12/14 14:24:12
Author           : AllenLuo
Version          : 2.0
'''
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Ensure BASE_DIR is absolute and correct if it was failing
if not os.path.exists(os.path.join(BASE_DIR, "test_case")):
    # Fallback to a safer calculation if 4 levels isn't right for some reason
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
import shutil
from loguru import logger
import warnings
from typing import Any, Callable, Dict, Generator, List, Optional
import allure
import yaml
import pytest
from playwright.sync_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Error,
    Page,
    Playwright,
    sync_playwright,
)
from slugify import slugify
import re

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "rep_" + rep.when, rep)

    if rep.when == "call":
        try:
            smokecases1 = item.funcargs['smokecases1']
            test_case_name = list(smokecases1.keys())[0] # e.g., testT3370
            match = re.search(r'T\d+', test_case_name)
            if not match:
                return
            test_case_id = match.group(0)

            status = "skipped" # Default status
            if rep.passed:
                status = "passed"
            elif rep.failed:
                status = "failed"
            
            logger.info(f"TEST_STATUS: {test_case_id} - {status}")
        except Exception:
            pass # Ignore errors if the fixture is not present




def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="release", help="Test environment: release, staging, or local")
    parser.addoption("--storage-state", action="store", default=None, help="Path to the storage state file")
    # Standard Playwright options (if not added by plugin or for custom usage)
    # Re-adding them here to prevent 'unrecognized argument' errors if plugin doesn't add them at this stage or logical conflict.
    # It is safer to add them if the code in this file explicitly calls getoption for them.
    # Note: If pytest-playwright is installed, it might add them. But duplications are usually ignored or handle-able. 
    # However, to be safe against the error we just saw:

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, playwright):
    iphone_12 = playwright.devices['iPhone 12 Pro']
    return {
        **browser_context_args,
        **iphone_12,
    }


@pytest.fixture(scope="session")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    page = context.new_page()
    yield page

def _build_artifact_test_folder(
    pytestconfig: Any, request: pytest.FixtureRequest, folder_or_file_name: str
) -> str:
    output_dir = pytestconfig.getoption("--output")
    return os.path.join(output_dir, slugify(request.node.nodeid), folder_or_file_name)

@pytest.fixture(scope="session")
def context(
    browser: Browser,
    browser_context_args: Dict,
    pytestconfig: Any,
    request: pytest.FixtureRequest,
) -> Generator[BrowserContext, None, None]:
    pages: List[Page] = []
    storage_state = pytestconfig.getoption("--storage-state")
    # 只在指定了 storage-state 时才传入,否则创建访客上下文
    if storage_state:
        context = browser.new_context(storage_state=storage_state, **browser_context_args)
    else:
        context = browser.new_context(**browser_context_args)
    context.on("page", lambda page: pages.append(page))
    tracing_option = pytestconfig.getoption("--tracing")
    capture_trace = tracing_option in ["on", "retain-on-failure"]
    if capture_trace:
        context.tracing.start(
            name=slugify(request.node.nodeid),
            screenshots=True,
            snapshots=True,
            sources=True,
        )

    yield context
    failed = request.node.rep_setup.failed or request.node.rep_call.failed if hasattr(request.node, 'rep_setup') and hasattr(request.node, 'rep_call') else True

    if capture_trace:
        retain_trace = tracing_option == "on" or (
            failed and tracing_option == "retain-on-failure"
        )
        if retain_trace:
            trace_path = _build_artifact_test_folder(pytestconfig, request, "trace.zip")
            context.tracing.stop(path=trace_path)
        else:
            context.tracing.stop()

    screenshot_option = pytestconfig.getoption("--screenshot")
    capture_screenshot = screenshot_option == "on" or (
        failed and screenshot_option == "only-on-failure"
    )
    if capture_screenshot:
        for index, page in enumerate(pages):
            human_readable_status = "failed" if failed else "finished"
            screenshot_path = _build_artifact_test_folder(
                pytestconfig, request, f"test-{human_readable_status}-{index+1}.png"
            )
            try:
                page.screenshot(timeout=5000, path=screenshot_path)
            except Error:
                pass

    context.close()

    video_option = pytestconfig.getoption("--video")
    preserve_video = video_option == "on" or (
        failed and video_option == "retain-on-failure"
    )
    if preserve_video:
        for page in pages:
            human_readable_status = "failed" if failed else "finished"
            video = page.video
            if not video:
                continue
            try:
                video_path = video.path()
                file_name = f"{slugify(request.node.nodeid)}.webm"
                video.save_as(path=_build_artifact_test_folder(pytestconfig, request, file_name))
                allure.attach.file(_build_artifact_test_folder(pytestconfig, request, file_name), name=request.node.name, attachment_type=allure.attachment_type.WEBM)

            except Error:
                # Silent catch empty videos.
                pass

@pytest.fixture(scope="session")
def smokecases1_data(pytestconfig):
    env = pytestconfig.getoption("--env")
    if env == "release":
        filename = "Katana_curator_smoke.yaml"
    else:
        filename = f"Katana_curator_smoke_{env}.yaml"
    
    test_case_path = os.path.join(BASE_DIR, "test_case", "UI", "Test_Katana", filename)
    logger.info(f"Loading test cases from: {test_case_path}")
    
    if not os.path.exists(test_case_path):
        logger.error(f"Configuration file not found: {test_case_path}")
        pytest.fail(f"Config file {filename} not found for environment '{env}'")

    with open(test_case_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file.read())

def pytest_generate_tests(metafunc):
    if "smokecases1" in metafunc.fixturenames:
        # Load data once per session via a helper or direct read
        # Note: We can't use fixtures easily inside hook-like generators without request
        # So we read the config during generation
        env = metafunc.config.getoption("--env")
        if env == "release":
            filename = "Katana_curator_smoke.yaml"
        else:
            filename = f"Katana_curator_smoke_{env}.yaml"
        
        path = os.path.join(BASE_DIR, "test_case", "UI", "Test_Katana", filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
                cases = [{k: v} for k, v in raw_data.items()]
                ids = [k for k in raw_data.keys()]
                metafunc.parametrize("smokecases1", cases, ids=ids)
        else:
            metafunc.parametrize("smokecases1", [])

@pytest.fixture()
def smokecases1(request):
    """ Parameterized test case (kept for compatibility with existing tests) """
    return request.param