import asyncio
import os
from playwright.async_api import async_playwright

async def main():
    os.makedirs("docs/images", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        
        try:
            # Dashboard
            print("Capturing Dashboard...")
            await page.goto("http://frontend:5173/")
            await page.wait_for_selector("h1", timeout=15000)
            await asyncio.sleep(2) # Wait for charts and animations
            await page.screenshot(path="docs/images/dashboard.png")
            
            # Competitors
            print("Capturing Competitors...")
            await page.goto("http://frontend:5173/competitors")
            await page.wait_for_selector("h1", timeout=15000)
            await asyncio.sleep(1)
            await page.screenshot(path="docs/images/competitors.png")
            
            # Reports
            print("Capturing Reports...")
            await page.goto("http://frontend:5173/reports")
            await page.wait_for_selector("h1", timeout=15000)
            await asyncio.sleep(1)
            await page.screenshot(path="docs/images/reports.png")
            
            print("Done capturing new screenshots!")
        except Exception as e:
            print(f"Error capturing screenshots: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
