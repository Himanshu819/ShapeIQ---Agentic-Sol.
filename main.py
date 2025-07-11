# import csv
# import os
# import re
# import logging

# from src.tools.agent_check_page import fetch_page_text, ask_ollama
# from src.tools.vendor_rules import parse_murata_mpn
# from src.parse_pdf.vendor_registry import extract_dimensions_from_pdf, detect_vendor
# from src.tools.search_google import search_mpn
# from src.tools.datasheet_scraper import find_pdf_link, download_pdf

# from dotenv import load_dotenv
# load_dotenv()

# # Configure logging for better visibility
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Define fieldnames globally for reuse as it's a constant list of headers for the CSV
# FIELDNAMES = [
#     "mpn",
#     "length", "width", "thickness",
#     "pin_length", "pin_width", "pin_pitch", "pin_count",
#     "shape_name",
#     "package_code",
#     "pitch",
#     "packaging"
# ]

# def process_single_mpn_full_pipeline(mpn):
#     """
#     Executes the full pipeline for a single MPN:
#     1. Checks for existing PDF or downloads it.
#     2. Extracts mechanical data using vendor rules first, then falls back to PDF parsing.
#     3. Merges the extracted data.
#     """
#     safe_mpn = re.sub(r'[\\/*?:"<>|]', '_', mpn)
#     pdf_path = f"downloads/{safe_mpn}.pdf"
#     pdf_downloaded = False

#     # Step 1: Check if PDF already exists or download it
#     if os.path.exists(pdf_path):
#         logging.info(f"✅ PDF already exists for MPN {mpn}, skipping download.")
#         pdf_downloaded = True
#     else:
#         # Step 2: Search and Download if not present
#         urls = search_mpn(mpn)[:10] # Limit to top 10 search results for efficiency

#         for url in urls:
#             logging.info(f"Checking URL: {url}")

#             # 1) Direct PDF detection (anywhere in the URL)
#             if ".pdf" in url.lower():
#                 logging.info("Direct PDF link detected in search result.")
#                 pdf_downloaded = download_pdf(url, mpn, referer=url)
#                 if pdf_downloaded:
#                     break # Exit loop if PDF is downloaded

#             # 2) Fetch HTML from URL
#             html = fetch_page_text(url)
#             if not html:
#                 logging.info("Skipped: Could not fetch page.")
#                 continue

#             # 3) Try PDF link extraction via scraper
#             pdf_url = find_pdf_link(html, url, mpn)
#             if pdf_url:
#                 pdf_url = pdf_url.strip()
#                 if pdf_url.lower().startswith(("http://", "https://")):
#                     logging.info(f"Attempting download from: {pdf_url}")
#                     pdf_downloaded = download_pdf(pdf_url, mpn, referer=url)
#                     if pdf_downloaded:
#                         break # Exit loop if PDF is downloaded
#                 else:
#                     logging.error(f"Invalid PDF URL (not absolute): {pdf_url}")
#             else:
#                 logging.info("No PDF link candidate found on this page.")

#             # 4) Fallback: Use LLM agent to analyze and extract PDF
#             if not pdf_downloaded: # Only use LLM if PDF not found yet
#                 logging.info("Using LLM to analyze page...")
#                 response = ask_ollama(mpn, html)
#                 logging.info(f"Agent says: {response}")

#                 if "http" in response and ".pdf" in response:
#                     start = response.find("http")
#                     end = response.find(".pdf", start) + 4
#                     pdf_url = response[start:end].strip()
#                     if pdf_url.lower().startswith(("http://", "https://")):
#                         logging.info("Agent found PDF URL, attempting download...")
#                         pdf_downloaded = download_pdf(pdf_url, mpn, referer=url)
#                         if pdf_downloaded:
#                             break # Exit loop if PDF is downloaded
#                     else:
#                         logging.error(f"Agent returned invalid URL: {pdf_url}")

#         if not pdf_downloaded:
#             logging.info("No PDF found in top search results.")
#             return {} # Return empty if PDF could not be downloaded

#     # If PDF was downloaded (or already existed), proceed with extraction
#     # STEP 3: Extract mechanical data from vendor rules
#     logging.info("Extracting mechanical dimensions using vendor rules...")
#     dims_vendor = parse_murata_mpn(mpn)

#     # Check if vendor rule extraction provided sufficient data (length, width, thickness)
#     if all([dims_vendor.get("length"), dims_vendor.get("width"), dims_vendor.get("thickness")]):
#         logging.info("✔️ Vendor rule extraction sufficient. Skipping PDF parsing.")
#         dims_pdf = {} # No need to parse PDF if vendor rules are complete
#     else:
#         logging.info("Vendor rules incomplete. Falling back to PDF parsing.")
#         # Detect vendor for PDF parsing (if needed, though extract_dimensions_from_pdf might handle it internally)
#         vendor = detect_vendor(pdf_path) # Retained for potential future use or internal logic in vendor_registry
#         # Corrected: extract_dimensions_from_pdf() expects pdf_path
#         dims_pdf = extract_dimensions_from_pdf(pdf_path)


#     # STEP 4: Merge results, prioritizing vendor data where available
#     final_data = {
#         "mpn": mpn,
#         "length": dims_vendor.get("length") or dims_pdf.get("length"),
#         "width": dims_vendor.get("width") or dims_pdf.get("width"),
#         "thickness": dims_vendor.get("thickness") or dims_pdf.get("thickness"),
#         "pin_length": dims_pdf.get("pin_length"), # Only from PDF
#         "pin_width": dims_pdf.get("pin_width"),   # Only from PDF
#         "pin_pitch": dims_pdf.get("pin_pitch"),   # Only from PDF
#         "pin_count": dims_pdf.get("pin_count"),   # Only from PDF
#         "shape_name": dims_pdf.get("shape_name"), # Only from PDF
#         "package_code": dims_pdf.get("package_code"), # Only from PDF
#         "pitch": dims_vendor.get("pitch") or dims_pdf.get("pitch"), # Prefer vendor pitch, fallback to PDF
#         "packaging": dims_vendor.get("packaging") or dims_pdf.get("packaging") # Prefer vendor packaging, fallback to PDF
#     }
#     return final_data


# def main():
#     """
#     Main function to run the MPN processing pipeline.
#     Prompts the user for an MPN, processes it, and writes results to a CSV.
#     """
#     logging.info("Starting single MPN processing via main.py.")
#     mpn = input("Enter the MPN: ").strip()

#     # Create 'downloads' and 'output' directories if they don't exist
#     os.makedirs("downloads", exist_ok=True)
#     output_dir = "output"
#     os.makedirs(output_dir, exist_ok=True)

#     result = process_single_mpn_full_pipeline(mpn)

#     csv_path = os.path.join(output_dir, "mechanical_data.csv")

#     # Ensure result is not empty before attempting to write to CSV
#     if result:
#         write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0

#         with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=FIELDNAMES) # Use the global FIELDNAMES

#             if write_header:
#                 writer.writeheader() # Write header only if needed

#             writer.writerow(result) # Write the data row

#         logging.info(f"✅ Mechanical data written to: {csv_path}")
#     else:
#         logging.warning(f"No dimensions extracted for MPN: {mpn}. Skipping CSV write.")


# if __name__ == "__main__":
#     main()


# main.py
import csv
import os
import re
import logging

from src.tools.search_google import search_mpn
from src.tools.agent_check_page import fetch_page_text,ask_ollama
from src.tools.datasheet_scraper import find_pdf_link, download_pdf
from src.tools.vendor_rules import parse_murata_mpn
from src.parse_pdf.vendor_registry import extract_dimensions_from_pdf, detect_vendor 

from dotenv import load_dotenv
load_dotenv()

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_single_mpn_full_pipeline(mpn: str) -> dict: # Added type hint for mpn
    """
    Encapsulates the full logic for processing a single MPN, from download to parsing.
    This function is called by both main.py and pipeline.py.
    """
    pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
    pdf_downloaded = False

    # Step 1: Check if PDF already exists locally and is valid
    if os.path.exists(pdf_path_downloaded):
        logging.info(f"✅ PDF already exists and is valid for MPN {mpn}, skipping online search and download.")
        pdf_downloaded = True
        
    if not pdf_downloaded:
        logging.info("PDF not found locally or was invalid. Initiating online search and download attempts...")
        
        # search_mpn now handles blacklisting Mouser/Digi-Key internally
        urls = search_mpn(f'"{mpn}" datasheet')[:10] 
        
        if not urls: 
            logging.error(f"❌ No search results found for {mpn} in top search results. Cannot proceed.")
            return {
                "mpn": mpn, "length": None, "width": None, "thickness": None,
                "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None,
                "packaging": None, "package_code": None, "shape_name": None,
                "pitch": None 
            }

        for url in urls:
            logging.info(f"\nChecking URL: {url}")

            # Attempt 1: Direct PDF link detection from search result URL
            if ".pdf" in url.lower(): 
                logging.info("✓ Direct PDF link detected in search result URL. Attempting direct download.")
                success = download_pdf(url, mpn, referer=url)
                if success:
                    pdf_downloaded = True
                    pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
                    break
                else:
                    logging.warning(f"[WARN] Direct PDF download from URL failed for {url}. Trying to fetch page content for analysis.")
                    
            # Attempt 2: Fetch HTML from URL
            html = fetch_page_text(url)
            if not html:
                logging.info("Skipped: Could not fetch page content.")
                continue

            # Attempt 3: Try PDF link extraction via scraper
            pdf_url = find_pdf_link(html, url, mpn)
            if pdf_url:
                pdf_url = pdf_url.strip()
                if pdf_url.lower().startswith(("http://", "https://")):
                    logging.info(f"Attempting download from: {pdf_url}")
                    success = download_pdf(pdf_url, mpn, referer=url)
                    if success:
                        pdf_downloaded = True
                        pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
                        break
                    else:
                        logging.warning(f"[WARN] Scraper-identified PDF download failed for {pdf_url}. Trying LLM fallback for current page.")
                else:
                    logging.error(f"Invalid PDF URL (not absolute): {pdf_url}")
            else:
                logging.info("No PDF link candidate found on this page.")

            # 4) Fallback: Use LLM agent to analyze and extract PDF
            if not pdf_downloaded:
                logging.info("Using LLM to analyze page as a final resort for this URL...")
                response = ask_ollama(mpn, html)
                logging.info(f"Agent says: {response}")

                pdf_links_from_llm = re.findall(r'(https?://\S+\.pdf)', response)
                
                if pdf_links_from_llm:
                    llm_identified_pdf_url = pdf_links_from_llm[0].strip() 
                    logging.info(f"Agent found PDF URL: {llm_identified_pdf_url}, attempting download...")
                    success = download_pdf(llm_identified_pdf_url, mpn, referer=url)
                    if success:
                        pdf_downloaded = True
                        pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
                        break
                    else:
                        logging.warning(f"[WARN] LLM-identified PDF download failed for {llm_identified_pdf_url}. Moving to next URL.")
                else:
                    logging.info("No PDF link identified by LLM for this page.")
            
        if not pdf_downloaded:
            logging.error(f"❌ No PDF found for {mpn} in top search results or after all attempts. Cannot proceed with parsing.")
            return {
                "mpn": mpn,
                "length": None, "width": None, "thickness": None,
                "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None,
                "packaging": None, "package_code": None, "shape_name": None,
                "pitch": None 
            } 

    # --- PDF is now downloaded (or already existed and validated) ---
    
    logging.info(f"Extracting mechanical dimensions and other data from PDF for {mpn}...")
    
    final_data = {
        "mpn": mpn,
        "length": None, "width": None, "thickness": None, 
        "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None, 
        "packaging": None, "package_code": None, "shape_name": None,
        "pitch": None
    }

    dims_from_mpn_rules = parse_murata_mpn(mpn) 
    final_data.update(dims_from_mpn_rules) 

    vendor = detect_vendor(mpn)
    if vendor == "murata": 
        logging.info("Attempting detailed PDF parsing using MurataParser.")
        try:
            parsed_data_from_pdf = extract_dimensions_from_pdf(mpn) 
            
            for key, value in parsed_data_from_pdf.items():
                if value is not None: 
                    final_data[key] = value
            
        except Exception as e:
            logging.error(f"ERROR] PDF content parsing (MurataParser) failed for {mpn}: {e}. Relying on MPN-rule data.")
    else:
        logging.warning(f"No specific PDF parser (e.g., MurataParser) implemented for {mpn}'s vendor: {vendor}. Relying solely on MPN rule data.")

    logging.info(f"Final extracted data for {mpn}: {final_data}")
    return final_data


def main(): 
    logging.info("Starting single MPN processing via main.py.")
    mpn = input("Enter the MPN: ").strip()
    result = process_single_mpn_full_pipeline(mpn)

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, "mechanical_data.csv")

    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0

    fieldnames = [
        "mpn", 
        "length", "width", "thickness", 
        "pin_length", "pin_width", "pin_pitch", "pin_count", 
        "shape_name", 
        "package_code",
        "pitch",        
        "packaging"     
    ] 

    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(result) 
        
    logging.info(f"✅ Mechanical data written to: {csv_path}")

    # --- Explicitly print all output fields ---
    print("\n--- Extracted Data Summary ---")
    for field in fieldnames:
        # Use .get(field) to safely access values, as some might be None
        print(f"{field.replace('_', ' ').title()}: {result.get(field)}")
    print("----------------------------")


if __name__ == "__main__":
    main()