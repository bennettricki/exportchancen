import requests
import concurrent.futures
from collections import defaultdict
import time
from bs4 import BeautifulSoup
import json
import re
import os

def fetch_proxies(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.strip().split('\n')
    except requests.RequestException:
        print(f"Failed to fetch proxies from {url}")
        return []

def check_proxy(proxy, proxy_type):
    try:
        proxies = {proxy_type: f"{proxy_type}://{proxy}"}
        response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
        if response.status_code == 200:
            return proxy, proxy_type
    except:
        pass
    return None

def check_risk_level(proxy, proxy_type):
    try:
        ip = proxy.split(':')[0]
        proxies = {proxy_type: f"{proxy_type}://{proxy}"}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:126.0) Gecko/20100101 Firefox/126.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://fraudguard.io/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'TE': 'trailers'
        }
        response = requests.get(f'https://fraudguard.io/?ip={ip}', headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            pre_code = soup.find('pre').find('code')
            if pre_code:
                json_str = pre_code.string
                # Remove any leading/trailing whitespace and newlines
                json_str = re.sub(r'^\s+|\s+$', '', json_str, flags=re.MULTILINE)
                data = json.loads(json_str)
                risk_level = int(data.get('risk_level', 6))
                return proxy, proxy_type, risk_level
    except Exception as e:
        print(f"Error checking risk level for {proxy}: {str(e)}")
    return None

def main():
    urls = {
        'http': ['https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt'],
        'socks4': ['https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt'],
        'socks5': ['https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt']
    }

    all_proxies = defaultdict(set)

    # Fetch proxies
    for proxy_type, url_list in urls.items():
        for url in url_list:
            proxies = fetch_proxies(url)
            all_proxies[proxy_type].update(proxies)
        print(f"Total {proxy_type} proxies scraped: {len(all_proxies[proxy_type])}")

    working_proxies = []

    # Check proxies
    total_proxies = sum(len(proxies) for proxies in all_proxies.values())
    print(f"\nChecking {total_proxies} proxies...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_proxy = {executor.submit(check_proxy, proxy, proxy_type): (proxy, proxy_type) 
                           for proxy_type, proxies in all_proxies.items() 
                           for proxy in proxies}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_proxy)):
            result = future.result()
            if result:
                working_proxies.append(result)
            print(f"\rChecking proxies: {i+1}/{total_proxies}", end="", flush=True)

    print(f"\n\nTotal working proxies: {len(working_proxies)}")

    # Remove duplicates
    working_proxies = list(set(working_proxies))

    # Check risk level
    low_risk_proxies = defaultdict(list)
    total_working = len(working_proxies)

    print(f"\nChecking risk levels for {total_working} working proxies...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        future_to_proxy = {executor.submit(check_risk_level, proxy, proxy_type): (proxy, proxy_type) for proxy, proxy_type in working_proxies}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_proxy)):
            result = future.result()
            if result:
                proxy, proxy_type, risk_level = result
                print(f"\rChecking risk levels: {i+1}/{total_working} (Current: {proxy}, Risk Level: {risk_level})", end="", flush=True)
                if risk_level <= 3:
                    low_risk_proxies[proxy_type].append(proxy)
                else:
                    print(f"\nProxy {proxy} has risk level {risk_level}, not saving.")
            else:
                print(f"\rChecking risk levels: {i+1}/{total_working} (Failed to check)", end="", flush=True)

    print("\n")
    
    # Create Proxies folder if it doesn't exist
    os.makedirs('Proxies', exist_ok=True)

    # Save to files
    for proxy_type, proxies in low_risk_proxies.items():
        filename = f"Proxies/{proxy_type}.txt"
        with open(filename, 'w') as f:
            for proxy in proxies:
                f.write(f"{proxy}\n")
        print(f"Saved {len(proxies)} low risk {proxy_type} proxies to {filename}")

    if sum(len(proxies) for proxies in low_risk_proxies.values()) == 0:
        print("No low-risk proxies found. You may want to adjust the risk level threshold.")

if __name__ == "__main__":
    main()
