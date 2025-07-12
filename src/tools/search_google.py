import os
import requests
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("SERPER_API_KEY")
SEARCH_URL = "https://google.serper.dev/search"
def search_mpn(mpn):
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": f"{mpn} datasheet"
    }
    res = requests.post(SEARCH_URL, headers=headers, json=payload)
    if res.status_code != 200:
        raise Exception("Search failed:", res.text)
    data = res.json()
    blocked_domains = ["mouser.com", "digikey.com"]
    links = []
    for r in data.get("organic", []):
        link = r.get("link", "")
        if not any(domain in link for domain in blocked_domains):
            links.append(link)
    return links
# TEST
if __name__ == "__main__":
    mpn = input("Enter MPN: ")
    links = search_mpn(mpn)
    for link in links:
        print(link)