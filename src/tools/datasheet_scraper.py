# # src/tools/datasheet_scraper.py
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin
# import requests
# import os


# def find_pdf_link(html, base_url, mpn=None):
#     """
#     Return the single best PDF link, or None.
#     """
#     soup = BeautifulSoup(html, "html.parser")
#     candidates = []

#     for a in soup.find_all('a', href=True):
#         raw_href = a['href'].strip()
#         # Resolve relative to absolute
#         full_url = urljoin(base_url, raw_href)
#         text = a.get_text().lower()

#         # Filter only PDF links
#         if '.pdf' not in full_url.lower():
#             continue

#         # Score for relevancy
#         score = 0
#         if 'datasheet' in text:
#             score += 5
#         if mpn and mpn.lower() in full_url.lower():
#             score += 3
#         if 'spec' in text:
#             score += 1

#         candidates.append((full_url, score))

#     # Pick highest score
#     if candidates:
#         candidates.sort(key=lambda x: x[1], reverse=True)
#         best_url = candidates[0][0].strip()
#         print(f"[INFO] Selected PDF link: {best_url}")
#         return best_url

#     print("[INFO] No PDF candidates found.")
#     return None


# def download_pdf(pdf_url, mpn, referer=None):
#     if not pdf_url.lower().startswith(('http://','https://')):
#         print(f"[ERROR] Invalid PDF URL: {pdf_url}")
#         return False

#     headers = {"User-Agent":"Mozilla/5.0"}
#     if referer:
#         headers["Referer"] = referer

#     try:
#         r = requests.get(pdf_url, headers=headers, stream=True, timeout=20, allow_redirects=True)
#         ct = r.headers.get("Content-Type","").lower()
#         if r.status_code == 200 and ('pdf' in ct or pdf_url.lower().endswith('.pdf')):
#             os.makedirs("data\datasheets", exist_ok=True)
#             with open(f"downloads/{mpn}.pdf","wb") as f:
#                 for chunk in r.iter_content(1024):
#                     f.write(chunk)
#             print(f"[SUCCESS] Saved downloads/{mpn}.pdf")
#             return True

#         print(f"[ERROR] Download returned {r.status_code}, Content-Type={ct}")
#         return False

#     except Exception as e:
#         print(f"[EXCEPTION] {e}")
#         return False


# src/tools/datasheet_scraper.py
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import os
import fitz # PyMuPDF - New import for PDF validation
import logging

def is_valid_pdf(filepath: str) -> bool:
    """
    Checks if a file is a valid, non-empty, and text-readable PDF.
    Returns True if valid, False otherwise.
    """
    if not os.path.exists(filepath):
        logging.error(f"PDF validation: File not found at {filepath}")
        return False
    if os.path.getsize(filepath) < 1000: # Heuristic: Very small files are suspicious
        logging.warning(f"PDF validation: File {filepath} is too small ({os.path.getsize(filepath)} bytes). Likely invalid.")
        return False
    
    try:
        doc = fitz.open(filepath)
        if doc.page_count == 0:
            logging.warning(f"PDF validation: {filepath} has no pages.")
            return False
        
        # Try to extract some text from the first few pages to ensure it's not just an image
        sample_text = ""
        for i in range(min(doc.page_count, 3)): # Check first 3 pages
            sample_text += doc.load_page(i).get_text()
        
        if len(sample_text.strip()) > 50: # Arbitrary threshold for "some content"
            logging.info(f"PDF validation: {filepath} appears to be valid and has sufficient text content.")
            return True
        else:
            logging.warning(f"PDF validation: {filepath} appears valid by structure but has very little text content. Might be image-only.")
            return False # Consider it invalid for automated text parsing
        
    except Exception as e:
        logging.error(f"PDF validation failed for {filepath}: {e}")
        return False
    finally:
        if 'doc' in locals() and doc: # Ensure doc is closed if it was opened
            doc.close()


def find_pdf_link(html, base_url, mpn=None):
    """
    Return the single best PDF link from the page content, or None.
    Prioritizes links containing 'datasheet', 'spec', 'pdf', 'download', 'document' 
    in their text or URL, or matching the MPN in the URL.
    Handles relative URLs and sorts by relevance score.
    """
    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    for a in soup.find_all('a', href=True):
        raw_href = a['href'].strip()
        full_url = urljoin(base_url, raw_href) # Resolve relative links to absolute

        # Filter only links that likely point to a PDF (anywhere in the URL string)
        if '.pdf' not in full_url.lower():
            continue

        text = a.get_text(strip=True).lower()
        score = 0

        # Scoring logic for relevancy - more comprehensive
        if "datasheet" in text:
            score += 10 # High score for explicit "datasheet" text
        if "pdf" in text:
            score += 8
        if mpn and mpn.lower() in full_url.lower(): # MPN in URL is a strong indicator
            score += 7
        if "spec" in text or "specification" in text:
            score += 6
        if "download" in text:
            score += 5
        if "document" in text:
            score += 4
        
        candidates.append((full_url, score))

    # Pick the highest scoring link
    if candidates:
        # Sort by score (desc), then by length of URL (shorter URLs often better direct links)
        candidates.sort(key=lambda x: (x[1], -len(x[0])), reverse=True)
        best_url = candidates[0][0].strip()
        logging.info(f"[INFO] Selected PDF link: {best_url} (Score: {candidates[0][1]})")
        return best_url

    logging.info("[INFO] No PDF candidates found on this page after scoring.")
    return None


def download_pdf(pdf_url, mpn, referer=None):
    """
    Downloads the PDF from the given URL and saves it to the downloads folder.
    Includes PDF content validation after download.
    Returns True on success, False on failure.
    """
    if not pdf_url.lower().startswith(('http://','https://')):
        logging.error(f"Invalid PDF URL (not absolute): {pdf_url}")
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", # Prioritize PDF content type
        "Connection": "keep-alive"
    }
    if referer:
        headers["Referer"] = referer # Pass the page URL as referer

    download_dir = "downloads"
    os.makedirs(download_dir, exist_ok=True)
    filepath = os.path.join(download_dir, f"{mpn}.pdf")

    try:
        r = requests.get(pdf_url, headers=headers, stream=True, timeout=20, allow_redirects=True)
        ct = r.headers.get("Content-Type", "").lower()

        if r.status_code == 200 and ('pdf' in ct or '.pdf' in pdf_url.lower()):
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            # --- PDF Content Validation ---
            if is_valid_pdf(filepath):
                logging.info(f"✅ PDF downloaded and saved to: {filepath}")
                return True
            else:
                logging.error(f"Downloaded file is NOT a valid PDF or is empty. Deleting invalid file: {filepath}")
                os.remove(filepath) # Delete the invalid file
                return False

        else:
            logging.error(f"Download failed. Status: {r.status_code}, Content-Type: {ct} for URL: {pdf_url}")
            if r.status_code == 200 and 'html' in ct:
                logging.debug(f"Received HTML content instead of PDF. First 200 chars: {r.text[:200]}")
            return False

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download PDF due to request error for {pdf_url}: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during PDF download for {pdf_url}: {e}")
        return False