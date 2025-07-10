# import requests
# from bs4 import BeautifulSoup
# import os

# def download_datasheet(mpn: str, save_dir="data/datasheets"):
#     print(f"[INFO] Searching datasheet for: {mpn}")

#     # Make sure the save directory exists
#     os.makedirs(save_dir, exist_ok=True)
#     # STEP 1: Search engine URL
#     search_url = f"https://www.bing.com/search?q={mpn}"
#     # STEP 2: Get HTML
#     response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
#     if response.status_code != 200:
#         print("Error: Could not fetch search results.")
#         return
#     # STEP 3: Parse PDF links
#     soup = BeautifulSoup(response.text, "html.parser")

#     # STEP 4: Download PDF
#     pdf_links = []
#     for link in soup.find_all("a", href=True):
#         href = link["href"]
#         if ".pdf" in href:
#             pdf_links.append(href)

#     if not pdf_links:
#         print("No PDF links found.")
#         return
#     # STEP 5: Save to disk
#     pdf_url = pdf_links[0]
#     print(f"Found PDF: {pdf_url}")

#     pdf_response = requests.get(pdf_url, stream=True)

#     if pdf_response.status_code != 200:
#         print("Error: Failed to download PDF.")
#         return

#     file_path = os.path.join(save_dir, f"{mpn}.pdf")

#     with open(file_path, "wb") as f:
#         for chunk in pdf_response.iter_content(chunk_size=1024):
#             if chunk:
#                 f.write(chunk)

#     print(f"Saved datasheet to: {file_path}")

#     pass  # You'll fill this in step-by-step

# # Example usage
# if __name__ == "__main__":
#     mpn_input = input("Enter MPN: ")
#     download_datasheet(mpn_input)
