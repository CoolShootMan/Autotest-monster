import asyncio
from playwright.async_api import async_playwright
import json
import re

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Load storage state
        context = await browser.new_context(storage_state="test_case/UI/Test_Katana/cookie_release.json")
        page = await context.new_page()
        
        url = "https://release.pear.us/demi-release"
        print(f"Navigating to {url}...")
        await page.goto(url)
        await page.wait_for_timeout(5000)

        print("-" * 50)
        print("Dumping all Buttons:")
        print("-" * 50)
        
        # Get all buttons and print their outerHTML
        buttons = await page.get_by_role("button").all()
        for i, btn in enumerate(buttons):
            visible = await btn.is_visible()
            text = await btn.inner_text()
            html = await btn.evaluate("el => el.outerHTML")
            print(f"Button {i} (Visible: {visible}, Text: '{text}'):\n{html}\n")
            
        print("-" * 50)
        print("Dumping 'About' Modal Buttons (if visible):")
        print("-" * 50)
        # Check for About modal content just in case
        modal = page.locator("div[role='dialog']").filter(has_text=re.compile("About", re.I)).first
        if await modal.is_visible():
             modal_btns = await modal.get_by_role("button").all()
             for i, btn in enumerate(modal_btns):
                visible = await btn.is_visible()
                text = await btn.inner_text()
                html = await btn.evaluate("el => el.outerHTML")
                print(f"Modal Button {i} (Visible: {visible}, Text: '{text}'):\n{html}\n")
        else:
            print("Modal not found.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
