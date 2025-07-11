# src/tools/datasheet_scraper.py
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import os
def find_pdf_link(html, base_url, mpn=None):
    """
    Return the single best PDF link, or None.
    """
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    for a in soup.find_all('a', href=True):
        raw_href = a['href'].strip()
        # Resolve relative to absolute
        full_url = urljoin(base_url, raw_href)
        text = a.get_text().lower()
        # Filter only PDF links
        if '.pdf' not in full_url.lower():
            continue
        # Score for relevancy
        score = 0
        if 'datasheet' in text:
            score += 5
        if mpn and mpn.lower() in full_url.lower():
            score += 3
        if 'spec' in text:
            score += 1
        candidates.append((full_url, score))
    # Pick highest score
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_url = candidates[0][0].strip()
        print(f"[INFO] Selected PDF link: {best_url}")
        return best_url
    print("[INFO] No PDF candidates found.")
    return None
def download_pdf(pdf_url, mpn, referer=None):
    if not pdf_url.lower().startswith(('http://','https://')):
        print(f"[ERROR] Invalid PDF URL: {pdf_url}")
        return False
    headers = {"User-Agent":"Mozilla/5.0"}
    if referer:
        headers["Referer"] = referer
    try:
        r = requests.get(pdf_url, headers=headers, stream=True, timeout=20, allow_redirects=True)
        ct = r.headers.get("Content-Type","").lower()
        if r.status_code == 200 and ('pdf' in ct or pdf_url.lower().endswith('.pdf')):
            os.makedirs("data\datasheets", exist_ok=True)
            with open(f"downloads/{mpn}.pdf","wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            print(f"[SUCCESS] Saved downloads/{mpn}.pdf")
            return True
        print(f"[ERROR] Download returned {r.status_code}, Content-Type={ct}")
        return False
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return False