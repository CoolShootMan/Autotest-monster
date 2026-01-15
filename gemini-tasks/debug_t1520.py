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
        
        async def trace(step):
            count = await page.get_by_role("button", name="Follow").count()
            print(f"Step '{step}': Follow button count: {count}, URL: {page.url}")
            if count > 0:
                print(f"  First Follow visible: {await page.get_by_role('button', name='Follow').first.is_visible()}")
            await page.screenshot(path=f"trace_{step.replace(' ', '_')}.png")

        url = "https://release.pear.us/demi-release"
        print(f"Navigating to {url}...")
        await page.goto(url)
        await page.wait_for_timeout(5000)
        await trace("Store Initial")

        print("Clicking Logo...")
        logo = page.get_by_role("img", name="Logo")
        if await logo.count() > 0:
            await logo.first.click()
            await page.wait_for_timeout(3000)
            await trace("After Logo")
        else:
            print("Logo NOT found!")

        # Check for About modal content
        modal = page.locator("div[role='dialog']").filter(has_text=re.compile("About", re.I)).first
        if await modal.is_visible():
            print("About modal found. Listing all buttons inside:")
            modal_btns = await modal.get_by_role("button").all()
            for i, btn in enumerate(modal_btns):
                text = (await btn.inner_text()).strip()
                aria = await btn.get_attribute("aria-label")
                print(f"  Modal Button {i}: Text: '{text}', Aria: '{aria}', Visible: {await btn.is_visible()}")
                if "Follow" in text or (aria and "follow" in aria.lower()):
                    print(f"  FOUND POTENTIAL TARGET: Button {i}")
            
            # Try to click 'Follow' EXACTLY
            follow_exact = modal.get_by_role("button", name="Follow", exact=True).first
            if await follow_exact.is_visible():
                print("Clicking EXACT 'Follow'...")
                await follow_exact.click(force=True)
            else:
                # Try partial
                follow_partial = modal.get_by_role("button", name="Follow", exact=False).first
                if await follow_partial.is_visible():
                    print(f"EXACT 'Follow' not found, clicking partial: '{await follow_partial.inner_text()}'")
                    await follow_partial.click(force=True)

            await page.wait_for_timeout(3000)
            await trace("After Modal Action")
        else:
            print("About modal NOT found after Logo click.")
            # Maybe it didn't open or I need a longer wait?
            await page.screenshot(path="trace_no_modal.png")
            
        # Check current state
        following_btn = page.get_by_role("button", name=re.compile("Following|Keep following", re.I)).first
        print(f"Following/Keep following visible: {await following_btn.is_visible()}")
        
        # Unfollow
        if await following_btn.is_visible():
            print("Clicking Following to trigger unfollow...")
            await following_btn.scroll_into_view_if_needed()
            await following_btn.click(force=True)
            await page.wait_for_timeout(1000)
            
            # Look for Unfollow Anyway
            unfollow_confirm = page.get_by_role("button", name="Unfollow Anyway").first
            if await unfollow_confirm.is_visible():
                print("Clicking Unfollow Anyway...")
                await unfollow_confirm.click(force=True)
                await page.wait_for_timeout(2000)
                await page.screenshot(path="debug_after_unfollow.png")

        # Now check for re-follow
        re_follow_btn = page.get_by_role("button", name="Follow").first
        print(f"Re-follow (Follow) button visible: {await re_follow_btn.is_visible()}")
        if await re_follow_btn.is_visible():
            box = await re_follow_btn.bounding_box()
            print(f"Re-follow button location: {box}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
