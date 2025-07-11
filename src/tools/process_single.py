import os
import re
import logging
from dotenv import load_dotenv

load_dotenv()

from src.tools.search_google import search_mpn
from src.tools.agent_check_page import fetch_page_text, ask_ollama
from src.tools.datasheet_scraper import find_pdf_link, download_pdf
from src.tools.vendor_rules import parse_murata_mpn
from src.parse_pdf.vendor_registry import extract_dimensions_from_pdf, detect_vendor

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def process_single_mpn_full_pipeline(mpn: str) -> dict:
    pdf_path = os.path.join("downloads", f"{mpn}.pdf")
    final_data = {
        "mpn": mpn,
        "length": None, "width": None, "thickness": None,
        "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None,
        "packaging": None, "package_code": None, "shape_name": None, "pitch": None
    }

    if os.path.exists(pdf_path):
        logging.info(f"✅ PDF already exists and is valid for MPN {mpn}")
    else:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logging.warning(f"Deleted invalid/corrupt PDF for {mpn}")

        logging.info(f"Searching for datasheet for {mpn}...")
        preferred_domains = [
            "murata.com", "tdk.com", "mouser.com", "digikey.com",
            "samsungsem.com", "kemet.com", "panasonic.com"
        ]
        query = f'"{mpn}" datasheet filetype:pdf ' + " ".join([f"site:{d}" for d in preferred_domains])
        urls = search_mpn(query)[:10]
        if not urls:
            logging.error(f"No search results for {mpn}")
            return final_data

        for url in urls:
            logging.info(f"Checking URL: {url}")
            html = fetch_page_text(url)
            if html == "DOWNLOAD_SUCCESS":
                break
            elif not html:
                continue

            pdf_url = find_pdf_link(html, base_url=url, mpn=mpn)
            if pdf_url:
                if download_pdf(pdf_url, mpn, referer=url):
                    break
            else:
                logging.info("Trying LLM fallback...")
                response = ask_ollama(mpn, html)
                logging.info(f"Agent says: {response}")
                pdf_links = re.findall(r'https?://\S+\.pdf', response)
                for candidate_url in pdf_links:
                    if download_pdf(candidate_url, mpn, referer=url):
                        break
                else:
                    continue
                break

        if not os.path.exists(pdf_path) or not is_valid_pdf(pdf_path):
            logging.error(f"❌ Failed to acquire valid PDF for MPN {mpn}")
            return final_data

    # ------------------------ Parsing stage ------------------------
    vendor = detect_vendor(mpn)
    final_data.update(parse_murata_mpn(mpn))

    if vendor == "murata":
        logging.info("Attempting PDF parsing with MurataParser...")
        try:
            parsed = extract_dimensions_from_pdf(mpn)
            for k, v in parsed.items():
                if v is not None:
                    final_data[k] = v
        except Exception as e:
            logging.error(f"MurataParser failed: {e}")

    logging.info(f"✅ Final extracted data for {mpn}: {final_data}")
    return final_data
