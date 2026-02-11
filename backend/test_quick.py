import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def quick_test():
    # Correct URL (using the actual GlobalHouse URL format)
    url = "https://www.globalhouse.co.th/product/กลอนดิจิตอล-C.HITECH-ล็อกนิ้วโคลด์-รุ่น-CK-5-พร้อมดีดตั้ง-1.GP660907-000010"
    print(f"Test URL: {url[:60]}...")
    
    # Check if it's a real product page
    import urllib.request
    try:
        response = urllib.request.urlopen(url, timeout=10)
        print(f"Status: {response.status}")
        html = response.read().decode('utf-8')
        if 'ไม่พบสินค้า' in html:
            print("❌ Product not found on GlobalHouse")
        elif 'กำลังช็อปที่' in html:
            print("✓ Valid GlobalHouse product page")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(quick_test())
