import asyncio
from playwright.async_api import async_playwright
import json
import re

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state="test_case/UI/Test_Katana/cookie_release.json")
        page = await context.new_page()
        
        url = "https://release.pear.us/demi-release"
        print(f"Navigating to {url}...")
        await page.goto(url)
        await page.wait_for_timeout(5000)

        # 1. Find the initial Follow button
        # Try finding it in the header/About modal if necessary, or just on page
        # Based on previous logs, it's visible.
        follow_btn = page.get_by_role("button", name="Follow", exact=True).first
        
        if await follow_btn.is_visible():
            print("Found 'Follow' button.")
            print(f"Outer HTML: {await follow_btn.evaluate('el => el.outerHTML')}")
            
            print("Clicking 'Follow'...")
            await follow_btn.click()
            await page.wait_for_timeout(3000)
            
            # 2. Now find what replaced it.
            # It might be a button with text "Following" or an icon.
            # Let's dump all buttons that are visible in the vicinity or just all visible buttons again but filtered.
            
            print("Searching for 'Following' indicator...")
            
            # Check for text "Following"
            following_text = page.get_by_role("button", name="Following").first
            if await following_text.is_visible():
                print("Found button with name 'Following':")
                print(await following_text.evaluate('el => el.outerHTML'))
            else:
                print("Button with name 'Following' NOT found.")
                
            # Dump all visible buttons to find the icon
            print("Dumping ALL visible buttons to find the icon:")
            btns = await page.get_by_role("button").all()
            for i, btn in enumerate(btns):
                if await btn.is_visible():
                    html = await btn.evaluate('el => el.outerHTML')
                    text = await btn.inner_text()
                    # Filter for buttons that look like the follow button (e.g. have specific classes or no text)
                    # We print a manageable amount
                    print(f"Btn {i}: Text='{text}'")
                    print(html)
                    print("-" * 20)
                    
        else:
            print("'Follow' button NOT found initially. Already following?")
            # If already following, we need to find the "Following" button directly
            print("Dumping ALL visible buttons to find 'Following' state:")
            btns = await page.get_by_role("button").all()
            for i, btn in enumerate(btns):
                if await btn.is_visible():
                    html = await btn.evaluate('el => el.outerHTML')
                    text = await btn.inner_text()
                    print(f"Btn {i}: Text='{text}'")
                    print(html)
                    print("-" * 20)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
