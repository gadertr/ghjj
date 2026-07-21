import asyncio
import httpx
import re
import argparse
import os

TIMEOUT = 10
TEST_URL = "http://www.google.com"
CONCURRENT_TESTS = 100

async def check_proxy(proxy_url):
    proxy_url = proxy_url.strip()
    if not proxy_url: return None
    
    # اگر پروتکل نداشت، پیش‌فرض http اضافه کن
    if not re.match(r'^(http|https|socks4|socks5)://', proxy_url):
        proxy_url = "http://" + proxy_url

    try:
        async with httpx.AsyncClient(proxies={"all://": proxy_url}, timeout=TIMEOUT, verify=False) as client:
            response = await client.get(TEST_URL)
            if response.status_code == 200:
                return proxy_url
    except:
        pass
    return None

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manual', type=str, help='Pasted proxies')
    parser.add_argument('--links', type=str, help='Subscription links')
    parser.add_argument('--file', type=str, help='File path in repo')
    args = parser.parse_args()

    raw_data = []

    # ۱. دریافت از کپی-پیست
    if args.manual:
        raw_data.append(args.manual)

    # ۲. دریافت از لینک‌های ساب
    if args.links:
        links = args.links.split(',')
        async with httpx.AsyncClient() as client:
            for link in links:
                try:
                    resp = await client.get(link.strip())
                    raw_data.append(resp.text)
                except:
                    print(f"Error fetching link: {link}")

    # ۳. دریافت از فایل داخل ریپازیتوری
    if args.file and os.path.exists(args.file):
        with open(args.file, 'r') as f:
            raw_data.append(f.read())

    # استخراج پروکسی‌ها با Regex
    all_text = "\n".join(raw_data)
    # پیدا کردن الگوهای http://ip:port یا ip:port خالی
    pattern = r'((?:socks4|socks5|http|https)://[\w\.-]+:\d+|[\d\.]+:\d+)'
    proxies = list(set(re.findall(pattern, all_text)))
    
    print(f"Total proxies found: {len(proxies)}")
    print("Testing starts...")

    tasks = [check_proxy(p) for p in proxies]
    results = await asyncio.gather(*tasks)

    valid_proxies = [r for r in results if r]
    
    with open("valid_proxies.txt", "w") as f:
        for p in valid_proxies:
            f.write(p + "\n")

    print(f"Done! Valid proxies: {len(valid_proxies)}")

if __name__ == "__main__":
    asyncio.run(main())
