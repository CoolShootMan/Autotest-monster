import asyncio
import os
import base64
from playwright.async_api import async_playwright
from core.ai_vision import AIVisionService

async def demo_self_healing():
    print("🚀 Starting Self-Healing Demo...")
    
    # Initialize AI Vision Service
    ai_service = AIVisionService()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Headed to see the magic
        # Load cookies for authenticated state
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            storage_state="d:/new test/Autotest-monster/test_case/UI/Test_Katana/cookie_release.json"
        )
        page = await context.new_page()
        
        print("🌐 Navigating to Release Page...")
        for attempt in range(3):
            try:
                await page.goto("https://release.pear.us/yu-xiao", timeout=60000)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(5) # Buffer for UI
                break
            except Exception as e:
                print(f"⚠️ Navigation attempt {attempt+1} failed: {e}. Retrying...")
                if attempt == 2: raise
        
        # 2. Attempt "Broken" Action
        target_description = "The 'Module' button in the navigation bar"
        broken_selector = "#non-existent-module-id-123"
        
        print(f"💥 Attempting to click '{target_description}' with BROKEN selector: {broken_selector}")
        try:
            await page.click(broken_selector, timeout=3000)
            print("❌ Unexpected success! The broken selector worked (it shouldn't).")
        except Exception as e:
            print("✅ Caught expected failure (TimeoutError). Initiating Self-Healing...")
            
            # 3. Capture Screenshot for AI
            screenshot_path = "healing_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"📸 Screenshot captured: {screenshot_path}")
            
            # 4. Call AI Vision
            print("🤖 Asking Gemini 1.5 Pro to locate the element...")
            result = ai_service.find_element(screenshot_path, target_description)
            
            if result.get("coordinates"):
                coords = result["coordinates"]
                print(f"✨ AI Found Element! Coordinates: {coords}")
                print(f"🧠 Analysis: {result.get('thought_process')}")
                
                # 5. Execute "Healed" Action
                print(f"🩹 Healing action: Clicking at ({coords['x']}, {coords['y']})...")
                
                # Visual indicator (red dot)
                await page.evaluate(f"""
                    const dot = document.createElement('div');
                    dot.style.position = 'absolute';
                    dot.style.left = '{coords['x']}px';
                    dot.style.top = '{coords['y']}px';
                    dot.style.width = '10px';
                    dot.style.height = '10px';
                    dot.style.backgroundColor = 'red';
                    dot.style.borderRadius = '50%';
                    dot.style.zIndex = '9999';
                    document.body.appendChild(dot);
                """)
                await asyncio.sleep(1) # Let user see the dot
                
                await page.mouse.click(coords["x"], coords["y"])
                
                # Verify Success (Check if modal opened or something changed)
                print("🎉 Click executed! Checking result...")
                await asyncio.sleep(3) # Wait for UI reaction
                
                # Simple check: take another screenshot or logs
                await page.screenshot(path="success_after_healing.png")
                print("✅ Self-Healing cycle complete. Check 'success_after_healing.png'.")
                
            else:
                print("💀 AI could not locate the element.")
                print(f"Error info: {result}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(demo_self_healing())
