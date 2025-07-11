# import os
# from src.parse_pdf.murata_parser import MurataParser
# from src.parse_pdf.base_parser import BaseParser

# # 1. Register all available vendor parsers here
# VENDOR_PARSERS = {
#     'murata': MurataParser,
#     # Add more when available
#     # 'samsung': SamsungParser,
#     # 'infineon': InfineonParser,
# }

# # 2. Detect vendor from MPN (basic heuristic, can improve later)
# def detect_vendor(mpn: str) -> str:
#     mpn = mpn.upper()
#     if mpn.startswith("GRM") or mpn.startswith("GCM")or mpn.startswith("GRT"):
#         return "murata"
#     # Add more rules here
#     return "unknown"

# # 3. Return the correct parser class for a given vendor name
# def get_parser_for_vendor(vendor: str):
#     parser_class = VENDOR_PARSERS.get(vendor.lower())
#     if not parser_class:
#         raise ValueError(f"No parser found for vendor: {vendor}")
#     return parser_class

# # 4. Main callable function for pipeline
# def extract_dimensions_from_pdf(mpn: str) -> dict:
#     vendor = detect_vendor(mpn)
#     parser_class = get_parser_for_vendor(vendor)

#     # Load text from downloaded PDF
#     pdf_path = f"downloads/{mpn}.pdf"
#     if not os.path.exists(pdf_path):
#         print(f"[ERROR] PDF not found for MPN {mpn}")
#         return {}

#     parser = parser_class(pdf_path)
#     return parser.extract_all(mpn)


# src/parse_pdf/vendor_registry.py
import os
import logging
from src.parse_pdf.murata_parser import MurataParser
from src.parse_pdf.base_parser import BaseParser # Ensure BaseParser is imported

# 1. Register all available vendor parsers here
VENDOR_PARSERS = {
    'murata': MurataParser,
    # 'samsung': SamsungParser, # Add more when available
    # 'infineon': InfineonParser, # Add more when available
    # 'generic_llm': GenericLLMParser # For a future LLM fallback parser
}

# 2. Detect vendor from MPN (basic heuristic, can improve later)
def detect_vendor(mpn: str) -> str:
    mpn = mpn.upper()
    if mpn.startswith("GRM") or mpn.startswith("GCM") or mpn.startswith("GRT") or mpn.startswith("GCJ"): # Murata Capacitor series
        return "murata"
    # Add more rules here for other vendors/component types
    # elif mpn.startswith("CL") or mpn.startswith("CIGW"): return "samsung"
    # elif mpn.startswith("SK"): return "diode_standard" # Placeholder for a general diode parser
    # elif mpn.startswith("SOT"): return "transistor_standard" # Placeholder for a general transistor parser
    logging.warning(f"Vendor detection: Could not identify specific vendor for MPN: {mpn}. Falling back to 'unknown'.")
    return "unknown" 

# 3. Return the correct parser class for a given vendor name
def get_parser_for_vendor(vendor: str):
    parser_class = VENDOR_PARSERS.get(vendor.lower())
    if not parser_class:
        raise ValueError(f"No parser found for vendor: {vendor}")
    return parser_class

# 4. Main callable function for pipeline
def extract_dimensions_from_pdf(mpn: str) -> dict:
    """
    Orchestrates PDF parsing by detecting the vendor and using the appropriate parser.
    Returns a dictionary with extracted dimensions and other data.
    """
    vendor = detect_vendor(mpn) 
    
    # If no specific parser, we can't do rule-based PDF parsing.
    # A future improvement would be to call a generic LLM parser here.
    if vendor == "unknown":
        logging.warning(f"No specific PDF parser implemented for vendor of MPN: {mpn}. Returning empty data from PDF parsing.")
        return {
            'length': None, 'width': None, 'thickness': None,
            'pin_length': None, 'pin_width': None, 'pin_pitch': None, 'pin_count': None,
            'packaging': None, 'package_code': None, 'shape_name': None
        }

    try:
        parser_class = get_parser_for_vendor(vendor)

        pdf_path = os.path.join("downloads", f"{mpn}.pdf") # Ensure correct path
        if not os.path.exists(pdf_path):
            logging.error(f"PDF content parsing: PDF file not found for MPN {mpn} at {pdf_path}. Cannot parse.")
            return {}
        
        # Instantiate parser, passing pdf_path and mpn
        parser = parser_class(pdf_path=pdf_path, mpn=mpn) 
        
        # Call extract_all, which performs the parsing logic
        parsed_data = parser.extract_all(mpn) 
        return parsed_data

    except Exception as e:
        logging.error(f"Error during PDF parsing for MPN {mpn} (vendor: {vendor}): {e}")
        return {} # Return empty dict on error