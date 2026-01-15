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

        # 1. Check if already following
        following_btn = page.get_by_role("button", name="Following", exact=True).first
        if await following_btn.is_visible():
            print("Found 'Following' button (Already Following). Resetting...")
            await following_btn.click()
            await page.get_by_role("button", name="Unfollow Anyway").click()
            await page.wait_for_timeout(2000)
            print("Unfollowed. Now looking for 'Follow'...")
        
        # 2. Find the Follow button
        follow_btn = page.get_by_role("button", name="Follow", exact=True).first
        
        if await follow_btn.is_visible():
            box = await follow_btn.bounding_box()
            center_x = box["x"] + box["width"] / 2
            center_y = box["y"] + box["height"] / 2
            print(f"Found 'Follow' button at: {box}")
            
            print("Clicking 'Follow'...")
            await follow_btn.click()
            await page.wait_for_timeout(5000) # Wait for state change to "Following"
            
            # Inspect what is at that location now
            print(f"Inspecting element at ({center_x}, {center_y})...")
            
            # Use evaluate handle to get element at point
            handle = await page.evaluate_handle(f"document.elementFromPoint({center_x}, {center_y})")
            if handle:
                tag = await handle.evaluate("el => el.tagName")
                html = await handle.evaluate("el => el.outerHTML")
                text = await handle.evaluate("el => el.innerText")
                print(f"Element at point: Tag='{tag}', Text='{text}'")
                print(f"HTML:\n{html}")
                
                # Check for buttons in the vicinity
                print("-" * 20)
                print("Dumping buttons with 'Follow' related icons or aria-labels:")
                btns = await page.get_by_role("button").all()
                for i, btn in enumerate(btns):
                    if await btn.is_visible():
                        html = await btn.evaluate('el => el.outerHTML')
                        aria = await btn.get_attribute("aria-label") or ""
                        if "Follow" in html or "Follow" in aria or "Check" in html or "Person" in html:
                            print(f"Potential Match Btn {i}:\n{html}\n")

            else:
                print("No element found at point (maybe covered or gone).")

        else:
            print("'Follow' button NOT found even after reset attempt.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
