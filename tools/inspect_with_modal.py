import asyncio
from playwright.async_api import async_playwright
import json
import re

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="test_case/UI/Test_Katana/cookie_release.json", viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        url = "https://release.pear.us/yu-xiao"
        print(f"Navigating to {url}...")
        await page.goto(url)
        await page.wait_for_timeout(3000)
        
        print("Clicking Explore...")
        await page.get_by_role("button", name="Explore").click()
        await page.wait_for_timeout(2000)
        
        print("Clicking Store Link...")
        await page.get_by_role("link", name="avatar Demi-release's Store").click()
        await page.wait_for_timeout(3000)

        # Click Logo to open About modal
        print("Clicking Logo to open About modal...")
        await page.get_by_role("img", name="Logo").click()
        await page.wait_for_timeout(2000)

        # Now check for Follow/Following
        print("Checking for Follow/Following inside modal details...")
        
        following_btn = page.get_by_role("button", name="Following", exact=True).first
        if await following_btn.is_visible():
            print("Found 'Following' button inside modal!")
            print(f"Outer HTML: {await following_btn.evaluate('el => el.outerHTML')}")
        else:
             print("'Following' button (exact=True) NOT found inside modal.")
             
        follow_btn = page.get_by_role("button", name="Follow", exact=True).first
        if await follow_btn.is_visible():
            print("Found 'Follow' button inside modal!")
            print(f"Outer HTML: {await follow_btn.evaluate('el => el.outerHTML')}")
        else:
            print("'Follow' button (exact=True) NOT found inside modal.")

        # Dump modal buttons
        modal = page.locator("div[role='dialog']").filter(has_text=re.compile("About", re.I)).first
        if await modal.is_visible():
            print("Dumping all modal buttons:")
            btns = await modal.get_by_role("button").all()
            for btn in btns:
                print(await btn.evaluate('el => el.outerHTML'))
        else:
            print("About modal not detected.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
