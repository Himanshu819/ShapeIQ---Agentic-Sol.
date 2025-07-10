# # main.py

# from src.tools.search_google import search_mpn
# from src.tools.agent_check_page import fetch_page_text,ask_ollama # Updated fetch_page_text with Selenium fallback
# from src.tools.datasheet_scraper import find_pdf_link, download_pdf, is_valid_pdf # Corrected import for is_valid_pdf
# from src.tools.vendor_rules import parse_murata_mpn
# from src.parse_pdf.vendor_registry import extract_dimensions_from_pdf
# import csv
# import os
# import re
# import logging

# # Configure logging for better visibility
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# def main():
#     mpn = input("Enter the MPN: ").strip()
#     pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#     pdf_downloaded = False

#     # Step 1: Check if PDF already exists locally and is valid
#     if os.path.exists(pdf_path_downloaded):
#         # Corrected call: Use is_valid_pdf as a standalone function
#         if is_valid_pdf(pdf_path_downloaded):
#             logging.info(f"✅ PDF already exists and is valid for MPN {mpn}, skipping online search and download.")
#             pdf_downloaded = True
#         else:
#             logging.warning(f"⚠️ Existing PDF for MPN {mpn} is invalid. Deleting and attempting re-download.")
#             os.remove(pdf_path_downloaded)
#             # pdf_downloaded remains False, so it will proceed to online search
    
#     if not pdf_downloaded: # Only proceed to online search if PDF wasn't found or was invalid
#         logging.info("PDF not found locally or was invalid. Initiating online search and download attempts...")
        
#         # --- Enhanced Search Query Logic ---
#         preferred_domains = [
#             "mouser.com", "digikey.com", 
#             "industrial.panasonic.com", "murata.com", "samsungsem.com", "infineon.com"
#         ]
        
#         search_query_base = f'"{mpn}" datasheet filetype:pdf'
#         targeted_search_query = search_query_base + " " + " OR ".join([f"site:{d}" for d in preferred_domains])
        
#         urls = search_mpn(targeted_search_query)[:5] 
#         if not urls: 
#             urls = search_mpn(search_query_base)[:10] 
        
#         blacklisted_domains = ['arrow.com', 'avnet.com', 'datasheetarchive.com', 'alldatasheet.com'] 
#         urls = [url for url in urls if not any(domain in url for domain in blacklisted_domains)]

#         for url in urls:
#             logging.info(f"\nChecking URL: {url}")

#             # Attempt 1: Direct PDF link detection from search result URL
#             if ".pdf" in url.lower(): 
#                 logging.info("✓ Direct PDF link detected in search result URL. Attempting direct download.")
#                 # Pass the download_dir and mpn to fetch_page_text as it might trigger Selenium download
#                 # fetch_page_text can now return "DOWNLOAD_SUCCESS" or HTML content
#                 html_or_success_signal = fetch_page_text(url, mpn=mpn, download_dir="downloads", use_selenium_force=True)
                
#                 if html_or_success_signal == "DOWNLOAD_SUCCESS":
#                     pdf_downloaded = True
#                     pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                     logging.info(f"Selenium handled PDF download directly for {mpn}. Skipping further attempts for this URL.")
#                     break # Break from URL loop, PDF is downloaded
#                 elif not html_or_success_signal: # If fetch_page_text returned None (failed to get HTML or download)
#                     logging.info("Skipped: Could not fetch page content (might be blocked or empty) via Selenium fallback for direct PDF link.")
#                     continue # Try next URL if fetching fails
#                 else: # fetch_page_text returned HTML, indicating it could not directly download the PDF
#                      html = html_or_success_signal # Use the returned HTML if it's not a success signal
#                      logging.info(f"Received HTML from {url} after initial direct PDF check failed. Proceeding with HTML parsing.")

#             else: # If URL is not a direct PDF link, proceed to fetch HTML
#                 html = fetch_page_text(url, mpn=mpn, download_dir="downloads") # Call fetch_page_text (might trigger Selenium download)
                
#                 if html == "DOWNLOAD_SUCCESS":
#                     pdf_downloaded = True
#                     pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                     logging.info(f"Selenium handled PDF download directly for {mpn}. Skipping further attempts for this URL.")
#                     break # Break from URL loop, PDF is downloaded
#                 elif not html: # If fetch_page_text returned None (failed to get HTML or download)
#                     logging.info("Skipped: Could not fetch page content (might be blocked or empty) via Selenium fallback.")
#                     continue # Try next URL if fetching fails
#                 # If html is not None and not "DOWNLOAD_SUCCESS", then it's actual HTML content.

#             # Attempt 3: Try PDF link extraction via BeautifulSoup scraper from fetched HTML
#             # Only if PDF not yet downloaded by fetch_page_text's internal Selenium click
#             if not pdf_downloaded:
#                 pdf_url_from_scraper = find_pdf_link(html, url, mpn)
#                 if pdf_url_from_scraper:
#                     logging.info(f"Attempting download via scraper-identified link: {pdf_url_from_scraper}")
#                     success = download_pdf(pdf_url_from_scraper, mpn, referer=url)
#                     if success:
#                         pdf_downloaded = True
#                         pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                         break
#                     else:
#                         logging.warning(f"[WARN] Scraper-identified PDF download failed for {pdf_url_from_scraper}. Trying LLM fallback for current page.")
                        
#                 # Attempt 4: Fallback - Use LLM agent to analyze page and extract PDF link
#                 if not pdf_downloaded:
#                     logging.info("Using LLM to analyze page as a final resort for this URL...")
#                     agent_response = ask_ollama(mpn, html)
#                     logging.info(f"Agent says: {agent_response}")

#                     pdf_links_from_llm = re.findall(r'(https?://\S+\.pdf)', agent_response)
                    
#                     if pdf_links_from_llm:
#                         llm_identified_pdf_url = pdf_links_from_llm[0].strip() 
#                         logging.info(f"Agent found PDF URL: {llm_identified_pdf_url}, attempting download...")
#                         success = download_pdf(llm_identified_pdf_url, mpn, referer=url)
#                         if success:
#                             pdf_downloaded = True
#                             pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                             break
#                         else:
#                             logging.warning(f"[WARN] LLM-identified PDF download failed for {llm_identified_pdf_url}. Moving to next URL.")
#                     else:
#                         logging.info("No PDF link identified by LLM for this page.")
            
#         if not pdf_downloaded:
#             logging.error("❌ No PDF found in top search results or after all attempts. Cannot proceed with parsing.")
#             return

#     # --- PDF is now downloaded (or already existed and validated) ---
    
#     logging.info("\nExtracting mechanical dimensions and other data from PDF and vendor rules...")
    
#     final_data = {
#         "mpn": mpn,
#         "length": None, "width": None, "thickness": None, 
#         "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None, 
#         "packaging": None, "package_code": None, "shape_name": None 
#     }

#     dims_from_mpn_rules = parse_murata_mpn(mpn) 
#     final_data.update(dims_from_mpn_rules) 

#     if not all([final_data.get("length"), final_data.get("width"), final_data.get("thickness")]):
#         logging.info("⚠️ Vendor rules incomplete for body dimensions. Falling back to PDF content parsing...")
#         try:
#             parsed_data_from_pdf = extract_dimensions_from_pdf(mpn) 
            
#             for key, value in parsed_data_from_pdf.items():
#                 if value is not None: 
#                     final_data[key] = value
            
#         except Exception as e:
#             logging.error(f"ERROR] PDF content parsing failed for {mpn}: {e}. Ensure PDF path is correct and parser is implemented for this vendor.")
#     else:
#         logging.info("✔️ Vendor rule extraction sufficient for body dimensions. Attempting secondary PDF parsing for additional details.")
#         try:
#             detailed_pdf_parse = extract_dimensions_from_pdf(mpn)
#             for key, value in detailed_pdf_parse.items():
#                 if value is not None and final_data.get(key) is None: 
#                     final_data[key] = value
#                 elif value is not None and key in ['pin_length', 'pin_width', 'pin_pitch', 'pin_count', 'package_code', 'shape_name'] :
#                     final_data[key] = value

#         except Exception as e:
#             logging.error(f"ERROR] Secondary PDF content parsing for pins/shape failed for {mpn}: {e}")
            
#     logging.info(f"Final extracted data for {mpn}: {final_data}")

#     output_dir = "output"
#     os.makedirs(output_dir, exist_ok=True)
#     csv_path = os.path.join(output_dir, "mechanical_data.csv")

#     write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0

#     fieldnames = [
#         "mpn", 
#         "length", "width", "thickness", 
#         "pin_length", "pin_width", "pin_pitch", "pin_count", 
#         "shape_name", 
#         "package_code",
#         "pitch",        
#         "packaging"     
#     ] 

#     with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         if write_header:
#             writer.writeheader()
#         writer.writerow(final_data)
        
#     logging.info(f"✅ Mechanical data written to: {csv_path}")

# if __name__ == "__main__":
#     main()

# # main.py
# import csv
# import os
# import re
# import logging

# from src.tools.search_google import search_mpn
# from src.tools.fetch_page import fetch_page_text
# from src.tools.llm_agent import ask_ollama
# from src.tools.datasheet_scraper import find_pdf_link, download_pdf, is_valid_pdf
# from src.tools.vendor_rules import parse_murata_mpn
# from src.parse_pdf.vendor_registry import extract_dimensions_from_pdf, detect_vendor # Import detect_vendor

# # Configure logging for better visibility
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# def process_single_mpn_full_pipeline(mpn: str) -> dict:
#     """
#     Encapsulates the full logic for processing a single MPN, from download to parsing.
#     This function is called by both main.py and pipeline.py.
#     """
#     pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#     pdf_downloaded = False

#     # Step 1: Check if PDF already exists locally and is valid
#     if os.path.exists(pdf_path_downloaded):
#         if is_valid_pdf(pdf_path_downloaded):
#             logging.info(f"✅ PDF already exists and is valid for MPN {mpn}, skipping online search and download.")
#             pdf_downloaded = True
#         else:
#             logging.warning(f"⚠️ Existing PDF for MPN {mpn} is invalid. Deleting and attempting re-download.")
#             os.remove(pdf_path_downloaded)
    
#     if not pdf_downloaded:
#         logging.info("PDF not found locally or was invalid. Initiating online search and download attempts...")
        
#         preferred_domains = [
#             "mouser.com", "digikey.com", 
#             "industrial.panasonic.com", "murata.com", "samsungsem.com", "infineon.com"
#         ]
        
#         search_query_base = f'"{mpn}" datasheet filetype:pdf'
#         targeted_search_query = search_query_base + " " + " OR ".join([f"site:{d}" for d in preferred_domains])
        
#         urls = search_mpn(targeted_search_query)[:5] 
#         if not urls: 
#             urls = search_mpn(search_query_base)[:10] 
        
#         blacklisted_domains = ['arrow.com', 'avnet.com', 'datasheetarchive.com', 'alldatasheet.com'] 
#         urls = [url for url in urls if not any(domain in url for domain in blacklisted_domains)]

#         for url in urls:
#             logging.info(f"\nChecking URL: {url}")

#             # Attempt 1: Direct PDF link detection from search result URL, or force Selenium for it
#             if ".pdf" in url.lower(): 
#                 logging.info("✓ Direct PDF link detected in search result URL. Attempting direct download (via Selenium if needed).")
#                 # fetch_page_text can return "DOWNLOAD_SUCCESS" (if Selenium clicked a download) or HTML content
#                 html_or_success_signal = fetch_page_text(url, mpn=mpn, download_dir="downloads", use_selenium_force=True)
#             else: # URL is not a direct PDF link, proceed to fetch HTML content
#                 html_or_success_signal = fetch_page_text(url, mpn=mpn, download_dir="downloads") 
            
#             if html_or_success_signal == "DOWNLOAD_SUCCESS":
#                 pdf_downloaded = True
#                 pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                 logging.info(f"Selenium handled PDF download directly for {mpn}. Skipping further attempts for this URL.")
#                 break 
#             elif not html_or_success_signal: # If fetch_page_text returned None (failed to get HTML or download)
#                 logging.info("Skipped: Could not fetch page content (might be blocked or empty) via Selenium fallback.")
#                 continue # Try next URL if fetching fails

#             html = html_or_success_signal # Use the returned HTML if it's not a success signal

#             # Attempt 3: Try PDF link extraction via BeautifulSoup scraper from fetched HTML
#             if not pdf_downloaded: # Only if PDF not already downloaded by fetch_page_text's internal Selenium click
#                 pdf_url_from_scraper = find_pdf_link(html, url, mpn)
#                 if pdf_url_from_scraper:
#                     logging.info(f"Attempting download via scraper-identified link: {pdf_url_from_scraper}")
#                     success = download_pdf(pdf_url_from_scraper, mpn, referer=url)
#                     if success:
#                         pdf_downloaded = True
#                         pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                         break
#                     else:
#                         logging.warning(f"[WARN] Scraper-identified PDF download failed for {pdf_url_from_scraper}. Trying LLM fallback for current page.")
                        
#                 # Attempt 4: Fallback - Use LLM agent to analyze page and extract PDF link
#                 if not pdf_downloaded:
#                     logging.info("Using LLM to analyze page as a final resort for this URL...")
#                     agent_response = ask_ollama(mpn, html)
#                     logging.info(f"Agent says: {agent_response}")

#                     pdf_links_from_llm = re.findall(r'(https?://\S+\.pdf)', agent_response)
                    
#                     if pdf_links_from_llm:
#                         llm_identified_pdf_url = pdf_links_from_llm[0].strip() 
#                         logging.info(f"Agent found PDF URL: {llm_identified_pdf_url}, attempting download...")
#                         success = download_pdf(llm_identified_pdf_url, mpn, referer=url)
#                         if success:
#                             pdf_downloaded = True
#                             pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                             break
#                         else:
#                             logging.warning(f"[WARN] LLM-identified PDF download failed for {llm_identified_pdf_url}. Moving to next URL.")
#                     else:
#                         logging.info("No PDF link identified by LLM for this page.")
            
#         if not pdf_downloaded:
#             logging.error(f"❌ No PDF found for {mpn} in top search results or after all attempts. Cannot proceed with parsing.")
#             return {
#                 "mpn": mpn,
#                 "length": None, "width": None, "thickness": None,
#                 "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None,
#                 "packaging": None, "package_code": None, "shape_name": None,
#                 "pitch": None # Ensure consistency for failed results
#             } # Return empty/None data for failed MPN

#     # --- PDF is now downloaded (or already existed and validated) ---
    
#     logging.info(f"Extracting mechanical dimensions and other data from PDF for {mpn}...")
    
#     final_data = {
#         "mpn": mpn,
#         "length": None, "width": None, "thickness": None, 
#         "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None, 
#         "packaging": None, "package_code": None, "shape_name": None,
#         "pitch": None
#     }

#     dims_from_mpn_rules = parse_murata_mpn(mpn) 
#     final_data.update(dims_from_mpn_rules) 

#     vendor = detect_vendor(mpn)
#     if vendor == "murata": # Only attempt detailed PDF parsing for Murata with MurataParser
#         logging.info("Attempting detailed PDF parsing using MurataParser.")
#         try:
#             parsed_data_from_pdf = extract_dimensions_from_pdf(mpn) 
            
#             for key, value in parsed_data_from_pdf.items():
#                 if value is not None: 
#                     final_data[key] = value
            
#         except Exception as e:
#             logging.error(f"ERROR] PDF content parsing (MurataParser) failed for {mpn}: {e}. Relying on MPN-rule data.")
#     else:
#         logging.warning(f"No specific PDF parser (e.g., MurataParser) implemented for {mpn}'s vendor: {vendor}. Relying solely on MPN rule data.")

#     logging.info(f"Final extracted data for {mpn}: {final_data}")
#     return final_data


# def main(): # This main function will now be simplified to just run the pipeline
#     logging.info("Starting single MPN processing via main.py.")
#     mpn = input("Enter the MPN: ").strip()
#     result = process_single_mpn_full_pipeline(mpn)

#     output_dir = "output"
#     os.makedirs(output_dir, exist_ok=True)
#     csv_path = os.path.join(output_dir, "mechanical_data.csv")

#     write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0

#     fieldnames = [
#         "mpn", 
#         "length", "width", "thickness", 
#         "pin_length", "pin_width", "pin_pitch", "pin_count", 
#         "shape_name", 
#         "package_code",
#         "pitch",        
#         "packaging"     
#     ] 

#     with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         if write_header:
#             writer.writeheader()
#         writer.writerow(result) # Write the single result
        
#     logging.info(f"✅ Mechanical data written to: {csv_path}")


# if __name__ == "__main__":
#     main()

# main.py
import csv
import os
import re
import logging

from src.tools.search_google import search_mpn
from src.tools.agent_check_page import fetch_page_text, ask_ollama
from src.tools.datasheet_scraper import find_pdf_link, download_pdf, is_valid_pdf
from src.tools.vendor_rules import parse_murata_mpn
from src.parse_pdf.vendor_registry import extract_dimensions_from_pdf, detect_vendor # Import detect_vendor

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_single_mpn_full_pipeline(mpn: str) -> dict:
    """
    Encapsulates the full logic for processing a single MPN, from download to parsing.
    This function is called by both main.py and pipeline.py.
    """
    pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
    pdf_downloaded = False

    # Step 1: Check if PDF already exists locally and is valid
    if os.path.exists(pdf_path_downloaded):
        if is_valid_pdf(pdf_path_downloaded):
            logging.info(f"✅ PDF already exists and is valid for MPN {mpn}, skipping online search and download.")
            pdf_downloaded = True
        else:
            logging.warning(f"⚠️ Existing PDF for MPN {mpn} is invalid. Deleting and attempting re-download.")
            os.remove(pdf_path_downloaded)
    
    if not pdf_downloaded:
        logging.info("PDF not found locally or was invalid. Initiating online search and download attempts...")
        
        preferred_domains = [
            "mouser.com", "digikey.com", 
            "industrial.panasonic.com", "murata.com", "samsungsem.com", "infineon.com"
        ]
        
        search_query_base = f'"{mpn}" datasheet filetype:pdf'
        targeted_search_query = search_query_base + " " + " OR ".join([f"site:{d}" for d in preferred_domains])
        
        urls = search_mpn(targeted_search_query)[:5] 
        if not urls: 
            urls = search_mpn(search_query_base)[:10] 
        
        blacklisted_domains = ['arrow.com', 'avnet.com', 'datasheetarchive.com', 'alldatasheet.com'] 
        urls = [url for url in urls if not any(domain in url for domain in blacklisted_domains)]

        for url in urls:
            logging.info(f"\nChecking URL: {url}")

            # Attempt 1: Direct PDF link detection from search result URL, or force Selenium for it
            if ".pdf" in url.lower(): 
                logging.info("✓ Direct PDF link detected in search result URL. Attempting direct download (via Selenium if needed).")
                # fetch_page_text can return "DOWNLOAD_SUCCESS" (if Selenium clicked a download) or HTML content
                html_or_success_signal = fetch_page_text(url, mpn=mpn, download_dir="downloads", use_selenium_force=True)
            else: # URL is not a direct PDF link, proceed to fetch HTML content
                html_or_success_signal = fetch_page_text(url, mpn=mpn, download_dir="downloads") 
            
            if html_or_success_signal == "DOWNLOAD_SUCCESS":
                pdf_downloaded = True
                pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
                logging.info(f"Selenium handled PDF download directly for {mpn}. Skipping further attempts for this URL.")
                break 
            elif not html_or_success_signal: # If fetch_page_text returned None (failed to get HTML or download)
                logging.info("Skipped: Could not fetch page content (might be blocked or empty) via Selenium fallback.")
                continue # Try next URL if fetching fails

            html = html_or_success_signal # Use the returned HTML if it's not a success signal

            # Attempt 3: Try PDF link extraction via BeautifulSoup scraper from fetched HTML
            if not pdf_downloaded: # Only if PDF not already downloaded by fetch_page_text's internal Selenium click
                pdf_url_from_scraper = find_pdf_link(html, url, mpn)
                if pdf_url_from_scraper:
                    logging.info(f"Attempting download via scraper-identified link: {pdf_url_from_scraper}")
                    success = download_pdf(pdf_url_from_scraper, mpn, referer=url)
                    if success:
                        pdf_downloaded = True
                        pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
                        break
                    else:
                        logging.warning(f"[WARN] Scraper-identified PDF download failed for {pdf_url_from_scraper}. Trying LLM fallback for current page.")
                        
                # Attempt 4: Fallback - Use LLM agent to analyze page and extract PDF link
                if not pdf_downloaded:
                    logging.info("Using LLM to analyze page as a final resort for this URL...")
                    agent_response = ask_ollama(mpn, html)
                    logging.info(f"Agent says: {agent_response}")

                    pdf_links_from_llm = re.findall(r'(https?://\S+\.pdf)', agent_response)
                    
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
                "pitch": None # Ensure consistency for failed results
            } # Return empty/None data for failed MPN

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
    if vendor == "murata": # Only attempt detailed PDF parsing for Murata with MurataParser
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


def main(): # This main function will now be simplified to just run the pipeline
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
        writer.writerow(result) # Write the single result
        
    logging.info(f"✅ Mechanical data written to: {csv_path}")


if __name__ == "__main__":
    main()