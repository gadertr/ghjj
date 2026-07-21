import asyncio
import httpx
import re
import argparse
import os
import base64

TIMEOUT = 15
TEST_URL = "http://httpbin.org/ip"

def decode_if_base64(text):
    try:
        return base64.b64decode(text.strip()).decode('utf-8')
    except:
        return text

async def check_proxy(proxy_url, semaphore, stats):
    proxy_url = proxy_url.strip()
    if not proxy_url: return None
    
    async with semaphore:
        try:
            async with httpx.AsyncClient(proxy=proxy_url, timeout=TIMEOUT, verify=False) as client:
                response = await client.get(TEST_URL)
                if response.status_code == 200:
                    print(f"  [✅ VALID] {proxy_url}")
                    stats['valid'] += 1
                    return proxy_url
                else:
                    print(f"  [⚠️ BAD STATUS {response.status_code}] {proxy_url}")
                    stats['bad_status'] += 1
        except httpx.ProxyError as e:
            print(f"  [❌ PROXY ERROR] {proxy_url} -> {type(e).__name__}")
            stats['proxy_error'] += 1
        except httpx.TimeoutException:
            print(f"  [⏱️ TIMEOUT] {proxy_url}")
            stats['timeout'] += 1
        except httpx.ConnectError as e:
            print(f"  [🔌 CONNECT ERROR] {proxy_url} -> {str(e)[:80]}")
            stats['connect_error'] += 1
        except Exception as e:
            print(f"  [❓ UNKNOWN ERROR] {proxy_url} -> {type(e).__name__}: {str(e)[:80]}")
            stats['unknown'] += 1
    return None

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manual', type=str)
    parser.add_argument('--links', type=str)
    parser.add_argument('--file', type=str)
    args = parser.parse_args()

    input_text = ""

    # جمع‌آوری ورودی‌ها
    if args.manual:
        print(f"\n[INPUT] Manual text length: {len(args.manual)} chars")
        input_text += "\n" + args.manual
    
    if args.file and os.path.exists(args.file):
        with open(args.file, 'r') as f:
            content = f.read()
            print(f"[INPUT] File '{args.file}' length: {len(content)} chars")
            input_text += "\n" + content
    
    if args.links:
        async with httpx.AsyncClient(timeout=20) as client:
            for link in args.links.split(','):
                link = link.strip()
                if not link: continue
                try:
                    resp = await client.get(link)
                    content = resp.text
                    print(f"[INPUT] Link '{link}' fetched: {len(content)} chars")
                    decoded = decode_if_base64(content)
                    input_text += "\n" + decoded
                except Exception as e:
                    print(f"[INPUT] Error fetching {link}: {e}")

    # استخراج پروکسی با رگکس قوی
    # این رگکس هم http://ip:port و هم socks4://ip:port و هم ip:port خالی را می‌گیرد
    pattern = r'(?:socks4h?|socks5h?|https?|socks4|socks5)://[\w\.\-:@]+(?::\d+)?|(?<![\w\.])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5}'
    proxies = re.findall(pattern, input_text)
    proxies = list(set(proxies))

    print(f"\n========== SUMMARY ==========")
    print(f"Total proxies extracted: {len(proxies)}")
    
    if not proxies:
        print("❌ NO PROXIES FOUND IN INPUT!")
        print("--- First 500 chars of input for debugging: ---")
        print(input_text[:500])
        print("--- End of preview ---")
        with open("valid_proxies.txt", "w") as f:
            f.write("")
        return

    print(f"First 5 samples: {proxies[:5]}")
    print(f"=============================\n")

    stats = {'valid': 0, 'timeout': 0, 'proxy_error': 0, 'connect_error': 0, 'bad_status': 0, 'unknown': 0}
    semaphore = asyncio.Semaphore(30)
    tasks = [check_proxy(p, semaphore, stats) for p in proxies]
    results = await asyncio.gather(*tasks)

    valid_proxies = [r for r in results if r]
    
    with open("valid_proxies.txt", "w") as f:
        for p in valid_proxies:
            f.write(p + "\n")

    print(f"\n========== FINAL REPORT ==========")
    print(f"✅ Valid:         {stats['valid']}")
    print(f"⏱️ Timeout:       {stats['timeout']}")
    print(f"❌ Proxy Error:   {stats['proxy_error']}")
    print(f"🔌 Connect Error: {stats['connect_error']}")
    print(f"⚠️ Bad Status:    {stats['bad_status']}")
    print(f"❓ Unknown:       {stats['unknown']}")
    print(f"==================================")

if __name__ == "__main__":
    asyncio.run(main())
