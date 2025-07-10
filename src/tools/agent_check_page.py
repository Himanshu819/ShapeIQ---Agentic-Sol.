# import requests
# import subprocess

# def fetch_page_text(url):
#     headers = {"User-Agent": "Mozilla/5.0"}
#     try:
#         res = requests.get(url, headers=headers, timeout=10)
#         if res.status_code != 200:
#             return None
#         # Ensure we return only UTF-8 text
#         return res.text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
#     except Exception as e:
#         print(f"[ERROR] Could not fetch page: {e}")
#         return None

# def fetch_page_text(url):
#     try:
#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
#             "Referer": "https://www.mouser.com/",
#             "Accept-Language": "en-US,en;q=0.9",
#             "Accept": "text/html,application/xhtml+xml",
#         }
#         response = requests.get(url, headers=headers, timeout=10)
#         if response.status_code != 200:
#             print(f"[ERROR] HTTP {response.status_code} from {url}")
#             return None
#         if "access denied" in response.text.lower():
#             print("[ERROR] Access Denied detected in HTML.")
#             return None
#         return response.text
#     except Exception as e:
#         print(f"[EXCEPTION] Failed to fetch {url}: {e}")
#         return None


# def ask_ollama(mpn, html_content):
#     # Clean HTML content before sending to LLM
#     clean_html = html_content.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

#     prompt = f"""
# You are an intelligent web assistant for electronics engineers.

# Your task is to verify whether a webpage contains a valid datasheet or specification for the component part number: "{mpn}"

# You are given the raw HTML text of a webpage. Analyze it and:

# 1. Determine how closely the part number "{mpn}" matches anything mentioned in the content. Use exact string match, partial match, or variant recognition (e.g., trimmed or aliased names).
# 2. Tell me how many times the exact or partial part number appears.
# 3. Check whether this page is most likely a:
#    -  Product detail page
#    -  Distributor listing
#    -  Article/blog
#    -  Generic result
# 4. Based on your analysis, tell me whether this page is a good match for the MPN.
# 5. If yes, find and return the **most likely datasheet link** — this could be:
#    - A PDF download link (preferred)
#    - An image or document preview
#    - An embedded table of specs

# ⚠️ Be careful: Only return a datasheet link if you’re confident that it belongs to the MPN "{mpn}".
# If you’re not sure, just say "Not confident."

# --- START OF PAGE CONTENT ---
# {clean_html[:4000]}
# --- END OF PAGE CONTENT ---
# """

#     try:
#         process = subprocess.Popen(
#             ["ollama", "run", "mistral"],
#             stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE
#         )
#         stdout, stderr = process.communicate(input=prompt.encode('utf-8'))
#         return stdout.decode('utf-8').strip()
#     except Exception as e:
#         return f"[LLM ERROR] {e}"

# import requests
# import subprocess

# def fetch_page_text(url):
#     try:
#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
#             "Referer": "https://www.mouser.com/",
#             "Accept-Language": "en-US,en;q=0.9",
#             "Accept": "text/html,application/xhtml+xml",
#         }
#         response = requests.get(url, headers=headers, timeout=10)
#         if response.status_code != 200:
#             print(f"[ERROR] HTTP {response.status_code} from {url}")
#             return None
#         if "access denied" in response.text.lower():
#             print("[ERROR] Access Denied detected in HTML.")
#             return None
#         return response.text
#     except Exception as e:
#         print(f"[EXCEPTION] Failed to fetch {url}: {e}")
#         return None


# src/tools/fetch_page.py
# import requests
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By # New: for explicit waits
# from selenium.webdriver.support.ui import WebDriverWait # New: for explicit waits
# from selenium.webdriver.support import expected_conditions as EC # New: for explicit waits
# from selenium.common.exceptions import WebDriverException, TimeoutException
# import os
# import time # New: for small delays

# def fetch_page_text(url: str, use_selenium_force: bool = False) -> str | None:
#     """
#     Fetches the HTML content of a URL.
#     Attempts a direct requests call first. If it fails or detects bot blocking,
#     it falls back to Selenium (headless browser) with enhanced evasion techniques.
#     'use_selenium_force=True' will bypass initial requests attempt and go straight to Selenium.
#     """
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
#         "Referer": "https://www.google.com/", # Generic Referer
#         "Accept-Language": "en-US,en;q=0.9",
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
#         "Connection": "keep-alive"
#     }

#     html_content = None

#     # --- Attempt 1: Direct requests call ---
#     if not use_selenium_force:
#         print(f"[INFO] Attempting to fetch {url} with direct requests...")
#         try:
#             response = requests.get(url, headers=headers, timeout=15)
            
#             # Check status code and common bot detection/blocking patterns in text
#             if response.status_code == 200:
#                 if "access denied" in response.text.lower() or \
#                    "bot detected" in response.text.lower() or \
#                    "cloudflare" in response.text.lower() or \
#                    "captcha" in response.text.lower() or \
#                    len(response.text.strip()) < 500: # Very short content might indicate a block
#                     print(f"[WARN] Direct request got limited access/blocked page for {url}. Initiating Selenium fallback.")
#                     use_selenium_force = True
#                 else:
#                     html_content = response.text
#                     print(f"[INFO] Direct request successful for {url}.")
#             else:
#                 print(f"[WARN] Direct request got HTTP {response.status_code} for {url}. Initiating Selenium fallback.")
#                 use_selenium_force = True

#         except requests.exceptions.RequestException as e:
#             print(f"[EXCEPTION] Direct request failed for {url}: {e}. Initiating Selenium fallback.")
#             use_selenium_force = True
#     else:
#         print(f"[INFO] Bypassing direct requests, forcing Selenium for {url}.")

#     # --- Attempt 2: Selenium Fallback ---
#     if use_selenium_force or html_content is None: # Only proceed if needed or direct request failed
#         print(f"[INFO] Attempting to fetch {url} with Selenium (headless browser)...")
#         driver = None # Initialize driver outside try block for proper cleanup
#         try:
#             chrome_options = Options()
#             chrome_options.add_argument("--headless")
#             chrome_options.add_argument("--disable-gpu")
#             chrome_options.add_argument("--no-sandbox")
#             chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
#             chrome_options.add_argument("--window-size=1920,1080")
#             chrome_options.add_argument("--disable-dev-shm-usage")
#             chrome_options.add_argument("--incognito")
            
#             # Selenium stealth options (common for evading bot detection)
#             chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#             chrome_options.add_experimental_option('useAutomationExtension', False)
            
#             script_dir = os.path.dirname(__file__)
#             chromedriver_path = os.path.join(script_dir, 'chromedriver.exe')
            
#             if not os.path.exists(chromedriver_path):
#                 print(f"[WARN] chromedriver.exe not found at {chromedriver_path}. Relying on system PATH.")
#                 service = Service() 
#             else:
#                 service = Service(executable_path=chromedriver_path)

#             driver = webdriver.Chrome(service=service, options=chrome_options)
#             driver.set_page_load_timeout(30)
            
#             # Inject JavaScript to prevent detection (optional, but can be effective)
#             driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
#                 "source": """
#                     Object.defineProperty(navigator, 'webdriver', {
#                     get: () => undefined
#                     });
#                 """
#             })

#             driver.get(url)
            
#             # --- Explicit Waits for Content to Load (Crucial for Mouser/Digi-Key) ---
#             # Wait for the presence of a common element on product pages
#             # For Mouser, common elements might be product title, part number display, or "datasheet" link.
#             # For Digi-Key, similar product details are good targets.
#             try:
#                 # Attempt to wait for a part number, product title, or datasheet link to appear
#                 WebDriverWait(driver, 15).until(
#                     EC.any_of(
#                         EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'datasheet')]")), # Text "datasheet"
#                         EC.presence_of_element_located((By.CSS_SELECTOR, "h1.ProductDetail-header__title")), # Mouser product title
#                         EC.presence_of_element_located((By.ID, "product-overview")), # Digi-Key product overview section
#                         EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'.pdf')]")) # Any PDF link
#                     )
#                 )
#                 print("[INFO] Page content seems to have loaded successfully (after explicit wait).")
#             except TimeoutException:
#                 print(f"[WARN] Content did not load within expected time for {url}. Proceeding anyway.")
            
#             # Small delay to ensure all dynamic elements are potentially rendered
#             time.sleep(2) 

#             html_content = driver.page_source
            
#             # Final check on Selenium-fetched content
#             if "access denied" in html_content.lower() or \
#                "bot detected" in html_content.lower() or \
#                "captcha" in html_content.lower() or \
#                len(html_content.strip()) < 500:
#                 print(f"[ERROR] Selenium also hit access denied or returned empty content for {url}. Could not retrieve page.")
#                 return None

#             print(f"[INFO] Selenium fetch successful for {url}.")
#             return html_content

#         except TimeoutException:
#             print(f"[ERROR] Selenium page load timed out for {url}.")
#             return None
#         except WebDriverException as e:
#             print(f"[ERROR] Selenium WebDriver error for {url}: {e}")
#             print("Please ensure ChromeDriver is installed and its path is correct/in system PATH, and compatible with your Chrome browser.")
#             return None
#         except Exception as e:
#             print(f"[EXCEPTION] Unexpected error with Selenium for {url}: {e}")
#             return None
#         finally:
#             if driver:
#                 driver.quit() # Ensure driver is always closed
            
#     return None # If all attempts fail

# def ask_ollama(mpn, html_content):
#     # Truncate and clean for LLM input
#     clean_html = html_content.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

#     prompt = f"""
# You are an intelligent assistant for electronics engineers.

# You are given the HTML content of a webpage. Your job is to determine if it contains a valid datasheet or specification for the component: "{mpn}".

# Steps:
# 1. Search for exact or close matches of the part number: "{mpn}"
# 2. Classify the page as one of:
#    - Product detail page
#    - Distributor listing
#    - Article/blog
#    - Generic result
#    - Access Denied or blocked
# 3. If the page is access denied or restricted, say so.
# 4. If it's a valid match and contains a datasheet, return the PDF URL.
# 5. Otherwise, suggest where the datasheet might be (alternative domains, other page elements).

# Be concise and precise.

# --- START OF HTML ---
# {clean_html[:4000]}
# --- END OF HTML ---
# """

#     try:
#         process = subprocess.Popen(
#             ["ollama", "run", "mistral"],
#             stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE
#         )
#         stdout, stderr = process.communicate(input=prompt.encode('utf-8'))
#         return stdout.decode('utf-8').strip()
#     except Exception as e:
#         return f"[LLM ERROR] {e}"


# src/tools/agent_check_page.py
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import os
import time
import logging
import subprocess

from selenium_stealth import stealth # Make sure you have this installed: pip install selenium-stealth
from src.tools.datasheet_scraper import is_valid_pdf # <--- Ensure this import is here at the top
from src.tools.datasheet_scraper import download_pdf as scraper_download_pdf # Also keep this aliased import at the top if fetch_page_text uses download_pdf directly


def fetch_page_text(url: str, use_selenium_force: bool = False, download_dir: str = "downloads", mpn: str = "") -> str | None:
    """
    Fetches the HTML content of a URL.
    Attempts a direct requests call first. If it fails or detects bot blocking,
    it falls back to Selenium (headless browser) with selenium-stealth.
    If a datasheet download button/link is found via Selenium, it attempts to click it
    and expects a file to be downloaded by the browser itself.
    Returns the page source if no direct download, or "DOWNLOAD_SUCCESS" sentinel value if successful.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Connection": "keep-alive"
    }

    html_content = None

    # --- Attempt 1: Direct requests call ---
    if not use_selenium_force:
        logging.info(f"Attempting to fetch {url} with direct requests...")
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            # CRITICAL: Handle direct PDF content from API URLs (like Murata's)
            if response.status_code == 200 and "application/pdf" in response.headers.get("Content-Type", ""):
                logging.info(f"Direct requests got PDF content from API URL: {url}. Attempting to save.")
                # Save binary content directly
                filepath = os.path.join(download_dir, f"{mpn}.pdf")
                os.makedirs(download_dir, exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # is_valid_pdf is now available due to top-level import
                if is_valid_pdf(filepath):
                    logging.info(f"Direct requests successfully downloaded and validated PDF from API: {filepath}")
                    return "DOWNLOAD_SUCCESS" # Signal success
                else:
                    logging.error(f"Direct requests downloaded invalid PDF from API: {url}. File: {filepath}")
                    if os.path.exists(filepath): os.remove(filepath) # Remove invalid file
                    return None # Signal failure

            # Handle HTML response after direct request
            if response.status_code == 200:
                if "access denied" in response.text.lower() or \
                   "bot detected" in response.text.lower() or \
                   "cloudflare" in response.text.lower() or \
                   "captcha" in response.text.lower() or \
                   len(response.text.strip()) < 500:
                    logging.warning(f"Direct request got limited access/blocked HTML page for {url}. Initiating Selenium fallback.")
                    use_selenium_force = True
                else:
                    html_content = response.text
                    logging.info(f"Direct request successful for {url}. Returning HTML content.")
            else:
                logging.warning(f"Direct request got HTTP {response.status_code} for {url}. Initiating Selenium fallback.")
                use_selenium_force = True

        except requests.exceptions.RequestException as e:
            logging.exception(f"Direct request failed for {url}: {e}. Initiating Selenium fallback.")
            use_selenium_force = True
    else:
        logging.info(f"Bypassing direct requests, forcing Selenium for {url}.")

    # --- Attempt 2: Selenium Fallback ---
    if use_selenium_force or html_content is None:
        logging.info(f"Attempting to fetch {url} with Selenium (headless browser) and potentially trigger download...")
        driver = None
        try:
            prefs = {
                "download.default_directory": os.path.abspath(download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options = Options()
            chrome_options.add_experimental_option("prefs", prefs)
            
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument(f"user-agent={headers['User-Agent']}")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--incognito")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            script_dir = os.path.dirname(__file__)
            chromedriver_path = os.path.join(script_dir, 'chromedriver.exe')
            
            service = Service(executable_path=chromedriver_path) if os.path.exists(chromedriver_path) else Service()

            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="ANGLE (Intel, Intel(R) UHD Graphics 630 (WDDM 2.7.0) Direct3D11 vs_5_0 ps_5_0, D3D11)",
                    fix_hairline=True,
                    )

            driver.set_page_load_timeout(30)
            
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                    });
                """
            })

            driver.get(url)
            
            # --- Explicit Waits for Content to Load and Download Button ---
            try:
                download_link_locator = (By.XPATH, "//a[contains(translate(., 'DATASHEETPDFDOWNLOADSPECSPECIFICATIONDOCUMENT', 'datasheetpdfdownloadspecspecificationdocument'), 'datasheet') and contains(@href, '.pdf')] | //button[contains(translate(., 'DATASHEETPDFDOWNLOADSPECSPECIFICATIONDOCUMENT', 'datasheetpdfdownloadspecspecificationdocument'), 'datasheet')] | //a[contains(@href,'.pdf')] | //button[contains(.,'Download')] | //h1[contains(.,'Product')] | //div[@id='product-overview']")
                
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(download_link_locator)
                )
                logging.info(f"Page content seems to have loaded successfully (after explicit wait) for {url}.")

                try:
                    download_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(translate(., 'DATASHEETPDFDOWNLOADSPECSPECIFICATIONDOCUMENT', 'datasheetpdfdownloadspecspecificationdocument'), 'datasheet') and contains(@href, '.pdf')] | //button[contains(translate(., 'DATASHEETPDFDOWNLOADSPECSPECIFICATIONDOCUMENT', 'datasheetpdfdownloadspecspecificationdocument'), 'datasheet')] | //a[contains(@href,'.pdf')] | //button[contains(.,'Download')]"))
                    )
                    logging.info(f"Found clickable download element: {download_button.text} -> {download_button.get_attribute('href')}")
                    
                    old_files = [f for f in os.listdir(download_dir) if f.startswith(mpn) and f.endswith(".pdf")]
                    for f in old_files:
                        os.remove(os.path.join(download_dir, f))
                        logging.info(f"Removed old download: {f}")

                    download_button.click()
                    logging.info("Clicked download element. Waiting for download to complete...")

                    downloaded_filepath = os.path.join(download_dir, f"{mpn}.pdf")
                    new_file_found = False
                    for _ in range(30):
                        time.sleep(1)
                        if os.path.exists(downloaded_filepath) and os.path.getsize(downloaded_filepath) > 0:
                            logging.info(f"Download detected at: {downloaded_filepath}")
                            new_file_found = True
                            break
                        recent_pdfs = [f for f in os.listdir(download_dir) if f.endswith('.pdf') and time.time() - os.path.getctime(os.path.join(download_dir, f)) < 30]
                        if recent_pdfs:
                            actual_downloaded_name = os.path.join(download_dir, recent_pdfs[0])
                            if actual_downloaded_name != downloaded_filepath:
                                try:
                                    os.rename(actual_downloaded_name, downloaded_filepath)
                                    logging.info(f"Renamed downloaded file to {downloaded_filepath}")
                                except OSError:
                                    logging.warning(f"Could not rename {actual_downloaded_name} to {downloaded_filepath}. Using existing name for validation.")
                                    downloaded_filepath = actual_downloaded_name
                            new_file_found = True
                            break

                    if new_file_found:
                        logging.info(f"File potentially downloaded by Selenium: {downloaded_filepath}")
                        # is_valid_pdf is correctly imported at the top
                        if is_valid_pdf(downloaded_filepath):
                            logging.info("Selenium successfully downloaded a valid PDF directly. Returning DOWNLOAD_SUCCESS signal.")
                            return "DOWNLOAD_SUCCESS"
                        else:
                            logging.error("Selenium downloaded file but it's corrupted/invalid.")
                            return None
                except TimeoutException:
                    logging.info("No primary datasheet download button found or clickable. Proceeding to extract page HTML for parsing.")


            except TimeoutException:
                logging.warning(f"Selenium page load or essential element wait timed out for {url}. Page might not have fully loaded.")
            
            time.sleep(2) 

            html_content = driver.page_source
            
            if "access denied" in html_content.lower() or \
               "bot detected" in html_content.lower() or \
               "captcha" in html_content.lower() or \
               len(html_content.strip()) < 500:
                logging.error(f"Selenium also hit access denied or returned empty content for {url}. Could not retrieve page.")
                return None

            logging.info(f"Selenium fetch successful for {url}. Returning page source.")
            return html_content

        except TimeoutException:
            logging.error(f"Selenium page load or element wait timed out for {url}.")
            return None
        except WebDriverException as e:
            logging.exception(f"Selenium WebDriver error for {url}: {e}")
            logging.error("Please ensure ChromeDriver is installed and its path is correct/in system PATH, and compatible with your Chrome browser.")
            return None
        except Exception as e:
            logging.exception(f"Unexpected error with Selenium for {url}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
            
    return html_content # Return page source from requests or Selenium if no direct download was triggered

def ask_ollama(mpn, html_content):
    clean_html = html_content.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

    prompt = f"""
You are an intelligent assistant for electronics engineers.

You are given the HTML content of a webpage. Your job is to determine if it contains a valid datasheet or specification for the component: "{mpn}".

Steps:
1. Search for exact or close matches of the part number: "{mpn}"
2. Classify the page as one of:
   - Product detail page
   - Distributor listing
   - Article/blog
   - Generic result
   - Access Denied or blocked
3. If the page is access denied or restricted, say so.
4. If it's a valid match and contains a datasheet, return the PDF URL.
5. Otherwise, suggest where the datasheet might be (alternative domains, other page elements).

Be concise and precise.

--- START OF HTML ---
{clean_html[:4000]}
--- END OF HTML ---
"""

    try:
        process = subprocess.Popen(
            ["ollama", "run", "mistral"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate(input=prompt, timeout=120)
        
        if process.returncode != 0:
            logging.error(f"Ollama process exited with code {process.returncode}. Stderr: {stderr}")
            return f"[LLM ERROR] Ollama failed: {stderr.strip()}"

        return stdout.strip()
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        logging.error(f"Ollama process timed out. Stderr: {stderr.decode('utf-8', errors='ignore')}")
        return "[LLM ERROR] Ollama timed out."
    except Exception as e:
        logging.exception(f"Exception during Ollama call: {e}")
        return f"[LLM ERROR] {e}"