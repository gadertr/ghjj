import asyncio
import httpx
import re
import os

# تنظیمات
TIMEOUT = 10  # ثانیه
TEST_URL = "http://www.google.com"
CONCURRENT_TESTS = 50  # تعداد تست همزمان

async def check_proxy(proxy_url):
    """تست دقیق یک پروکسی"""
    proxy_url = proxy_url.strip()
    if not re.match(r'^(http|https|socks4|socks5)://', proxy_url):
        # اگر پروتکل نداشت، پیش‌فرض http فرض می‌شود
        proxy_url = "http://" + proxy_url

    try:
        async with httpx.AsyncClient(proxies=proxy_url, timeout=TIMEOUT) as client:
            response = await client.get(TEST_URL)
            if response.status_code == 200:
                print(f"[✅ VALID] {proxy_url}")
                return proxy_url
    except Exception:
        pass
    return None

async def main():
    print("--- Proxy Checker Professional ---")
    print("1. Import from file (list.txt)")
    print("2. Paste proxies (End with Ctrl+D or Ctrl+Z)")
    print("3. Import from Link (Sub link)")
    
    choice = input("Select choice (1/2/3): ")
    raw_proxies = []

    if choice == '1':
        filename = input("Enter filename (e.g., proxies.txt): ")
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                raw_proxies = f.readlines()
    
    elif choice == '2':
        print("Paste your proxies here (IP:Port or Protocol://IP:Port):")
        while True:
            try:
                line = input()
                if not line: break
                raw_proxies.append(line)
            except EOFError:
                break
                
    elif choice == '3':
        url = input("Enter Subscription Link: ")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                raw_proxies = resp.text.splitlines()
        except Exception as e:
            print(f"Error fetching URL: {e}")

    # استخراج پروکسی‌ها با Regex (تمیز کردن ورودی)
    clean_proxies = []
    for p in raw_proxies:
        found = re.findall(r'((?:socks4|socks5|http|https)://[\w\.:@]+|[\d\.]+\:\d+)', p)
        clean_proxies.extend(found)

    clean_proxies = list(set(clean_proxies)) # حذف تکراری‌ها
    print(f"Total proxies to test: {len(clean_proxies)}")

    # اجرای تست همزمان
    tasks = [check_proxy(p) for p in clean_proxies]
    results = await asyncio.gather(*tasks)

    # ذخیره موارد سالم
    valid_proxies = [r for r in results if r]
    
    with open("valid_proxies.txt", "w") as f:
        for proxy in valid_proxies:
            f.write(proxy + "\n")

    print(f"\n--- Done! ---")
    print(f"Valid proxies saved: {len(valid_proxies)}")
    print("Check 'valid_proxies.txt' for results.")

if __name__ == "__main__":
    asyncio.run(main())
