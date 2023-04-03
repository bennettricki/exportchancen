import re
import requests
import os

def scrape_proxies(url, proxies):
    try:
        response = requests.get(url, proxies=proxies, timeout=30)

        if response.status_code != 200:
            print(f"Error: {url} returned status code {response.status_code}")
            return []

        proxies_list = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})', response.text)
        return proxies_list

    except Exception as e:
        print(f"Error: {url} - {str(e)}")
        return []


def main():
    tunnel_proxy = os.environ["IPROYAL"]
    proxies = {'http': tunnel_proxy, 'https': tunnel_proxy}

    urls = {
        "https": os.environ["HTTPS_URL"],
        "http": os.environ["HTTP_URL"],
        "socks4": os.environ["SOCKS4_URL"],
        "socks5": os.environ["SOCKS5_URL"]
    }

    total_proxies = 0

    for proxy_type, url in urls.items():
        scraped_proxies = scrape_proxies(url, proxies)
        print(f"Scraped {len(scraped_proxies)} {proxy_type.upper()} proxies from {url}")

        with open(f"{proxy_type}.txt", "w") as f:
            for proxy in scraped_proxies:
                f.write(f"{proxy[0]}:{proxy[1]}\n")

        total_proxies += len(scraped_proxies)

    print(f"Scraped a total of {total_proxies} proxies")

if __name__ == "__main__":
    main()
