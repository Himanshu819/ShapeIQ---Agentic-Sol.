import requests
import subprocess
def fetch_page_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200:
            return None
        # Ensure we return only UTF-8 text
        return res.text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[ERROR] Could not fetch page: {e}")
        return None
def ask_ollama(mpn, html_content):
    # Clean HTML content before sending to LLM
    clean_html = html_content.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    prompt = f"""
You are an intelligent web assistant for electronics engineers.
Your task is to verify whether a webpage contains a valid datasheet or specification for the component part number: "{mpn}"
You are given the raw HTML text of a webpage. Analyze it and:
1. Determine how closely the part number "{mpn}" matches anything mentioned in the content. Use exact string match, partial match, or variant recognition (e.g., trimmed or aliased names).
2. Tell me how many times the exact or partial part number appears.
3. Check whether this page is most likely a:
   -  Product detail page
   -  Distributor listing
   -  Article/blog
   -  Generic result
4. Based on your analysis, tell me whether this page is a good match for the MPN.
5. If yes, find and return the **most likely datasheet link** — this could be:
   - A PDF download link (preferred)
   - An image or document preview
   - An embedded table of specs
:warning: Be careful: Only return a datasheet link if you’re confident that it belongs to the MPN "{mpn}".
If you’re not sure, just say "Not confident."
--- START OF PAGE CONTENT ---
{clean_html[:4000]}
--- END OF PAGE CONTENT ---
"""
    try:
        process = subprocess.Popen(
            ["ollama", "run", "mistral"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate(input=prompt.encode('utf-8'))
        return stdout.decode('utf-8').strip()
    except Exception as e:
        return f"[LLM ERROR] {e}"