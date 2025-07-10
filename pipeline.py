# # pipeline.py
# from src.parsers.vendor_registry import get_parser_for_vendor
# from src.tools.pdf_reader import extract_text_from_pdf

# def process_pdf_for_mpn(mpn: str, vendor: str, pdf_path: str):
#     parser_class = get_parser_for_vendor(vendor)
#     pdf_text = extract_text_from_pdf(pdf_path)
#     parser = parser_class(pdf_text, mpn)
#     result = parser.extract_all()
#     result["mpn"] = mpn
#     return result

# # pipeline.py
# import csv
# import os
# import logging
# from src.tools.search_google import search_mpn
# from src.tools.agent_check_page import fetch_page_text, ask_ollama
# from src.tools.datasheet_scraper import find_pdf_link, download_pdf, is_valid_pdf
# from src.tools.vendor_rules import parse_murata_mpn
# from src.parse_pdf.vendor_registry import extract_dimensions_from_pdf, detect_vendor # Import detect_vendor here

# # Configure logging for better visibility in pipeline
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# def process_single_mpn(mpn: str) -> dict:
#     """
#     Processes a single MPN from download to parsing, returning the final data.
#     This function encapsulates the core logic from your main.py loop.
#     """
#     pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#     pdf_downloaded = False
    
#     # Initialize all fields that we want in the final CSV output for this MPN
#     result_data = {
#         "mpn": mpn,
#         "length": None, "width": None, "thickness": None,
#         "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None,
#         "packaging": None, "package_code": None, "shape_name": None,
#         "pitch": None # Ensure this is also in the result_data for consistency
#     }

#     logging.info(f"\n--- Processing MPN: {mpn} ---")

#     # Step 1: Check if PDF already exists locally and is valid
#     if os.path.exists(pdf_path_downloaded):
#         if is_valid_pdf(pdf_path_downloaded):
#             logging.info(f"✅ PDF already exists and is valid for MPN {mpn}.")
#             pdf_downloaded = True
#         else:
#             logging.warning(f"⚠️ Existing PDF for MPN {mpn} is invalid. Deleting and attempting re-download.")
#             os.remove(pdf_path_downloaded)
    
#     if not pdf_downloaded:
#         logging.info("PDF not found locally or was invalid. Initiating online search and download attempts...")
        
#         # --- Search Query Logic ---
#         # Prioritize major distributors and manufacturers
#         # For Murata, explicitly target Murata and major distributors
#         preferred_domains = [
#             "murata.com", "mouser.com", "digikey.com", 
#             "industrial.panasonic.com", "samsungsem.com", "infineon.com"
#         ]
        
#         search_query_base = f'"{mpn}" datasheet filetype:pdf'
#         targeted_search_query = search_query_base + " " + " OR ".join([f"site:{d}" for d in preferred_domains])
        
#         urls = search_mpn(targeted_search_query)[:5]
#         if not urls:
#             urls = search_mpn(search_query_base)[:10] 
        
#         blacklisted_domains = ['arrow.com', 'avnet.com', 'datasheetarchive.com', 'alldatasheet.com'] 
#         urls = [url for url in urls if not any(domain in url for domain in blacklisted_domains)]

#         for url in urls:
#             logging.info(f"Checking URL: {url}")

#             # Attempt 1: Direct PDF link detection from search result URL
#             if ".pdf" in url.lower(): 
#                 logging.info("✓ Direct PDF link detected in search result URL. Attempting direct download.")
#                 html_or_success_signal = fetch_page_text(url, mpn=mpn, download_dir="downloads", use_selenium_force=True)
                
#                 if html_or_success_signal == "DOWNLOAD_SUCCESS":
#                     pdf_downloaded = True
#                     pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                     logging.info(f"Selenium handled PDF download directly for {mpn}. Skipping further attempts for this URL.")
#                     break 
#                 elif not html_or_success_signal:
#                     logging.info("Skipped: Could not fetch page content (might be blocked or empty) via Selenium fallback for direct PDF link.")
#                     continue
#                 else: 
#                      html = html_or_success_signal
#                      logging.info(f"Received HTML from {url} after initial direct PDF check failed. Proceeding with HTML parsing.")

#             else: # If URL is not a direct PDF link, proceed to fetch HTML
#                 html = fetch_page_text(url, mpn=mpn, download_dir="downloads")
                
#                 if html == "DOWNLOAD_SUCCESS":
#                     pdf_downloaded = True
#                     pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
#                     logging.info(f"Selenium handled PDF download directly for {mpn}. Skipping further attempts for this URL.")
#                     break
#                 elif not html:
#                     logging.info("Skipped: Could not fetch page content (might be blocked or empty) via Selenium fallback.")
#                     continue

#             # Attempt 3: Try PDF link extraction via BeautifulSoup scraper from fetched HTML
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
#             logging.error(f"❌ No PDF found for {mpn} in top search results or after all attempts. Cannot proceed with parsing.")
#             return result_data # Return data with None for dimensions


#     # --- PDF is now downloaded (or already existed and validated) ---
    
#     logging.info(f"Extracting mechanical dimensions and other data from PDF for {mpn}...")
    
#     # Try MPN-based vendor rules first (fastest) for initial data population
#     dims_from_mpn_rules = parse_murata_mpn(mpn) 
#     result_data.update(dims_from_mpn_rules) 

#     # For Murata, we now directly call the PDF parser for detailed info
#     # The MurataParser is designed to get all fields, preferring PDF content over MPN rules if found.
#     vendor = detect_vendor(mpn) # Detect vendor to pass to extract_dimensions_from_pdf
#     if vendor == "murata": # Only attempt PDF parsing for Murata with MurataParser
#         try:
#             parsed_data_from_pdf = extract_dimensions_from_pdf(mpn) 
            
#             # Merge results: PDF parsed data generally preferred for accuracy.
#             # Overwrite fields with PDF data if PDF data is not None.
#             for key, value in parsed_data_from_pdf.items():
#                 if value is not None:
#                     result_data[key] = value
#         except Exception as e:
#             logging.error(f"ERROR] PDF content parsing failed for {mpn}: {e}. Falling back to MPN-rule data.")
#     else:
#         logging.warning(f"No specific PDF parser (e.g., MurataParser) implemented for {mpn}'s vendor: {vendor}. Relying solely on MPN rule data.")

#     logging.info(f"Final extracted data for {mpn}: {result_data}")
#     return result_data


# def run_pipeline(input_csv_path: str, output_csv_path: str):
#     """
#     Reads MPNs from an input CSV, processes each, and writes all results to an output CSV.
#     """
#     input_mpns = []
#     try:
#         with open(input_csv_path, mode='r', newline='', encoding='utf-8') as infile:
#             reader = csv.DictReader(infile)
#             for row in reader:
#                 if 'MPN' in row and row['MPN'].strip(): # Assuming MPN column name
#                     input_mpns.append(row['MPN'].strip())
#                 else:
#                     logging.warning(f"Skipping row due to missing or empty 'MPN' field: {row}")
#     except FileNotFoundError:
#         logging.error(f"Input CSV file not found: {input_csv_path}")
#         return
#     except Exception as e:
#         logging.error(f"Error reading input CSV {input_csv_path}: {e}")
#         return

#     if not input_mpns:
#         logging.warning("No MPNs found in the input CSV. Pipeline aborted.")
#         return

#     all_results = []
#     # Define the exact fieldnames for your output CSV, including all possible fields
#     output_fieldnames = [
#         "mpn",
#         "length", "width", "thickness",
#         "pin_length", "pin_width", "pin_pitch", "pin_count",
#         "shape_name",
#         "package_code",
#         "pitch",        # Include pitch and packaging from vendor rules output
#         "packaging",
#         # Add 'NAPINO PART NO.' and 'COMPONENTS DESCRIPTION' here if you will read them from the input BOM CSV
#         # 'NAPINO PART NO.', 'COMPONENTS DESCRIPTION'
#     ]

#     # Create/overwrite the output CSV with headers
#     os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
#     with open(output_csv_path, mode='w', newline='', encoding='utf-8') as outfile:
#         writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
#         writer.writeheader()

#         for mpn in input_mpns:
#             single_mpn_data = process_single_mpn(mpn)
#             # Ensure all keys in single_mpn_data are in output_fieldnames to avoid ValueError
#             # If not, DictWriter will raise error. Or just write the row directly if fields match.
#             writer.writerow(single_mpn_data)
#             all_results.append(single_mpn_data) # Store for potential later use or review

#     logging.info(f"\n--- Batch processing complete. Results saved to {output_csv_path} ---")


# if __name__ == "__main__":
#     # Create the input_boms directory if it doesn't exist
#     os.makedirs("input_boms", exist_ok=True)
    
#     # Create a dummy input CSV for testing
#     dummy_input_csv_path = "input_boms/murata_boms.csv"
#     if not os.path.exists(dummy_input_csv_path):
#         with open(dummy_input_csv_path, 'w', newline='') as f:
#             writer = csv.writer(f)
#             writer.writerow(['MPN'])
#             writer.writerow(['GRM155R61A475MEAAD'])
#             writer.writerow(['GCM1555C1H221JA16D'])
#             writer.writerow(['GRT033C81A104KE01J'])
#             # Add more Murata MPNs for testing
#             # writer.writerow(['GRM188R71C104KA01D']) # Example
#         logging.info(f"Created a dummy input CSV: {dummy_input_csv_path}")

#     # Set the output CSV path
#     output_csv_path = "output/mechanical_data.csv"
    
#     run_pipeline(dummy_input_csv_path, output_csv_path)

# pipeline.py
import csv
import os
import logging
from src.tools.search_google import search_mpn
from src.tools.agent_check_page import fetch_page_text, ask_ollama
from src.tools.datasheet_scraper import find_pdf_link, download_pdf, is_valid_pdf
from src.tools.vendor_rules import parse_murata_mpn
from src.parse_pdf.vendor_registry import extract_dimensions_from_pdf, detect_vendor # Import detect_vendor here

# Configure logging for better visibility in pipeline
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_single_mpn(mpn: str) -> dict:
    """
    Processes a single MPN from download to parsing, returning the final data.
    This function encapsulates the core logic for a single MPN pipeline run.
    """
    pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
    pdf_downloaded = False
    
    # Initialize all fields that we want in the final CSV output for this MPN
    result_data = {
        "mpn": mpn,
        "length": None, "width": None, "thickness": None,
        "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None,
        "packaging": None, "package_code": None, "shape_name": None,
        "pitch": None # Ensure this is also in the result_data for consistency
    }

    logging.info(f"\n--- Processing MPN: {mpn} ---")

    # Step 1: Check if PDF already exists locally and is valid
    if os.path.exists(pdf_path_downloaded):
        if is_valid_pdf(pdf_path_downloaded):
            logging.info(f"✅ PDF already exists and is valid for MPN {mpn}.")
            pdf_downloaded = True
        else:
            logging.warning(f"⚠️ Existing PDF for MPN {mpn} is invalid. Deleting and attempting re-download.")
            os.remove(pdf_path_downloaded)
    
    if not pdf_downloaded:
        logging.info("PDF not found locally or was invalid. Initiating online search and download attempts...")
        
        # --- Search Query Logic ---
        preferred_domains = [
            "murata.com", "mouser.com", "digikey.com", 
            "industrial.panasonic.com", "samsungsem.com", "infineon.com"
        ]
        
        search_query_base = f'"{mpn}" datasheet filetype:pdf'
        targeted_search_query = search_query_base + " " + " OR ".join([f"site:{d}" for d in preferred_domains])
        
        urls = search_mpn(targeted_search_query)[:5]
        if not urls:
            urls = search_mpn(search_query_base)[:10] 
        
        blacklisted_domains = ['arrow.com', 'avnet.com', 'datasheetarchive.com', 'alldatasheet.com'] 
        urls = [url for url in urls if not any(domain in url for domain in blacklisted_domains)]

        for url in urls:
            logging.info(f"Checking URL: {url}")

            # Attempt 1: Direct PDF link detection from search result URL
            if ".pdf" in url.lower(): 
                logging.info("✓ Direct PDF link detected in search result URL. Attempting direct download.")
                html_or_success_signal = fetch_page_text(url, mpn=mpn, download_dir="downloads", use_selenium_force=True)
                
                if html_or_success_signal == "DOWNLOAD_SUCCESS":
                    pdf_downloaded = True
                    pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
                    logging.info(f"Selenium handled PDF download directly for {mpn}. Skipping further attempts for this URL.")
                    break 
                elif not html_or_success_signal:
                    logging.info("Skipped: Could not fetch page content (might be blocked or empty) via Selenium fallback for direct PDF link.")
                    continue
                else: 
                     html = html_or_success_signal
                     logging.info(f"Received HTML from {url} after initial direct PDF check failed. Proceeding with HTML parsing.")

            else: # If URL is not a direct PDF link, proceed to fetch HTML
                html = fetch_page_text(url, mpn=mpn, download_dir="downloads")
                
                if html == "DOWNLOAD_SUCCESS":
                    pdf_downloaded = True
                    pdf_path_downloaded = os.path.join("downloads", f"{mpn}.pdf")
                    logging.info(f"Selenium handled PDF download directly for {mpn}. Skipping further attempts for this URL.")
                    break
                elif not html:
                    logging.info("Skipped: Could not fetch page content (might be blocked or empty) via Selenium fallback.")
                    continue

            # Attempt 3: Try PDF link extraction via BeautifulSoup scraper from fetched HTML
            if not pdf_downloaded:
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
            return result_data # Return data with None for dimensions


    # --- PDF is now downloaded (or already existed and validated) ---
    
    logging.info(f"Extracting mechanical dimensions and other data from PDF for {mpn}...")
    
    # Initialize all fields that we want in the final CSV output for this MPN
    # These fields must match the output_fieldnames in run_pipeline
    final_parsed_data = {
        "mpn": mpn,
        "length": None, "width": None, "thickness": None,
        "pin_length": None, "pin_width": None, "pin_pitch": None, "pin_count": None,
        "packaging": None, "package_code": None, "shape_name": None,
        "pitch": None # This is from vendor_rules's specific pitch, distinct from pin_pitch but often same
    }


    # Try MPN-based vendor rules first (fastest) for initial data population
    dims_from_mpn_rules = parse_murata_mpn(mpn) 
    final_parsed_data.update(dims_from_mpn_rules) 

    # Fallback to PDF content parsing if body dimensions are still missing
    # Or to get more precise details (pin data, refined shape/package code)
    vendor = detect_vendor(mpn)
    if vendor == "murata": # Only attempt detailed PDF parsing for Murata with MurataParser
        logging.info("Attempting detailed PDF parsing using MurataParser.")
        try:
            parsed_data_from_pdf = extract_dimensions_from_pdf(mpn) 
            
            # Merge results: PDF parsed data generally preferred for accuracy.
            # Overwrite fields with PDF data if PDF data is not None.
            for key, value in parsed_data_from_pdf.items():
                if value is not None:
                    final_parsed_data[key] = value
        except Exception as e:
            logging.error(f"ERROR] PDF content parsing (MurataParser) failed for {mpn}: {e}. Relying on MPN-rule data.")
    else:
        logging.warning(f"No specific PDF parser (e.g., MurataParser) implemented for {mpn}'s vendor: {vendor}. Relying solely on MPN rule data.")

    logging.info(f"Final extracted data for {mpn}: {final_parsed_data}")
    return final_parsed_data


def run_pipeline(input_csv_path: str, output_csv_path: str):
    """
    Reads MPNs from an input CSV, processes each, and writes all results to an output CSV.
    """
    input_mpns = []
    try:
        with open(input_csv_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                if 'MPN' in row and row['MPN'].strip(): # Assuming MPN column name
                    input_mpns.append(row['MPN'].strip())
                else:
                    logging.warning(f"Skipping row due to missing or empty 'MPN' field: {row}")
    except FileNotFoundError:
        logging.error(f"Input CSV file not found: {input_csv_path}")
        return
    except Exception as e:
        logging.error(f"Error reading input CSV {input_csv_path}: {e}")
        return

    if not input_mpns:
        logging.warning("No MPNs found in the input CSV. Pipeline aborted.")
        return

    # Define the exact fieldnames for your output CSV, including all possible fields
    output_fieldnames = [
        "mpn",
        "length", "width", "thickness",
        "pin_length", "pin_width", "pin_pitch", "pin_count",
        "shape_name",
        "package_code",
        "pitch",        # Include pitch and packaging from vendor rules output
        "packaging",
        # Add 'NAPINO PART NO.' and 'COMPONENTS DESCRIPTION' here if you will read them from the input BOM CSV
        # 'NAPINO PART NO.', 'COMPONENTS DESCRIPTION'
    ]

    # Create/overwrite the output CSV with headers
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
        writer.writeheader()

        for mpn in input_mpns:
            single_mpn_data = process_single_mpn(mpn) # Call the single MPN processing function
            writer.writerow(single_mpn_data) # Write the result to the output CSV

    logging.info(f"\n--- Batch processing complete. Results saved to {output_csv_path} ---")


if __name__ == "__main__":
    # Create the input_boms directory if it doesn't exist
    os.makedirs("input_boms", exist_ok=True)
    
    # Create a dummy input CSV for testing
    dummy_input_csv_path = "input_boms/murata_boms.csv"
    if not os.path.exists(dummy_input_csv_path):
        with open(dummy_input_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['MPN'])
            writer.writerow(['GRM155R61A475MEAAD'])
            writer.writerow(['GCM1555C1H221JA16D'])
            writer.writerow(['GRT033C81A104KE01J'])
            # Add more Murata MPNs for testing
        logging.info(f"Created a dummy input CSV: {dummy_input_csv_path}")

    # Set the output CSV path
    output_csv_path = "output/mechanical_data.csv"
    
    # This is the line that actually runs the batch pipeline
    run_pipeline(dummy_input_csv_path, output_csv_path)