# import fitz  # PyMuPDF

# class BaseParser:
#     def __init__(self, pdf_path):
#         self.pdf_path = pdf_path
#         self.text = self.extract_text()

#     def extract_text(self):
#         try:
#             doc = fitz.open(self.pdf_path)
#             text = ""
#             for page in doc:
#                 text += page.get_text()
#             return text
#         except Exception as e:
#             print(f"[ERROR] Could not extract text from {self.pdf_path}: {e}")
#             return ""

# src/parse_pdf/base_parser.py
import fitz # PyMuPDF
import logging
import os # Import os for path checking

class BaseParser:
    def __init__(self, pdf_path: str, mpn: str = ""): # mpn added to constructor for consistency
        self.pdf_path = pdf_path
        self.mpn = mpn
        self.text = self._extract_text_from_pdf()
        
    def _extract_text_from_pdf(self) -> str:
        """
        Extracts all text from the PDF file specified by self.pdf_path.
        Includes basic checks for file existence.
        """
        text = ""
        if not os.path.exists(self.pdf_path):
            logging.error(f"BaseParser: PDF file not found for text extraction at {self.pdf_path}.")
            return ""

        try:
            doc = fitz.open(self.pdf_path)
            for page in doc:
                text += page.get_text()
            logging.info(f"BaseParser: Extracted {len(text)} characters from {self.pdf_path}.")
            return text
        except Exception as e:
            logging.error(f"BaseParser: Error extracting text from {self.pdf_path}: {e}")
            return ""
        finally:
            if 'doc' in locals() and doc:
                doc.close()

    def extract_all(self, mpn: str) -> dict:
        """
        Abstract method to be implemented by subclasses.
        Should orchestrate all extraction logic (dimensions, pins, packaging, shape_name)
        and return a comprehensive dictionary of results.
        """
        raise NotImplementedError("Subclasses must implement extract_all() method to define extraction logic.")