# murata_parser_standalone.py
import re
import sys
import fitz  # PyMuPDF
import logging

class MurataParser:
    def __init__(self, pdf_path):
        self.text = self.extract_text_from_relevant_section(pdf_path)

    def extract_text_from_relevant_section(self, pdf_path):
        text = ""
        try:
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    page_text = page.get_text()
                    if "Type & Dimension" in page_text:
                        return page_text  # Only return this section
                    text += page_text  # fallback: keep collecting
        except Exception as e:
            logging.error(f"Error reading PDF: {e}")
        return text

    def extract_dimensions(self):
        dimension_data = {'length': None, 'width': None, 'thickness': None}

        # Match three float values followed by "+/-" float (likely from table format)
        grouped = re.search(
            r"(\d+\.\d+)\s*[\u00b1+\-]\s*\d+\.\d+\s+"
            r"(\d+\.\d+)\s*[\u00b1+\-]\s*\d+\.\d+\s+"
            r"(\d+\.\d+)\s*[\u00b1+\-]\s*\d+\.\d+",
            self.text
        )
        if grouped:
            dimension_data['length'] = float(grouped.group(1))
            dimension_data['width'] = float(grouped.group(2))
            dimension_data['thickness'] = float(grouped.group(3))
            return dimension_data

        # Individual fallback patterns (no filtering of similar values)
        patterns = {
            'length': re.compile(r"L\s*[:：]?[\s]*(\d+\.\d+)", re.IGNORECASE),
            'width': re.compile(r"W\s*[:：]?[\s]*(\d+\.\d+)", re.IGNORECASE),
            'thickness': re.compile(r"T\s*[:：]?[\s]*(\d+\.\d+)", re.IGNORECASE),
        }

        for key, pattern in patterns.items():
            match = pattern.search(self.text)
            if match:
                dimension_data[key] = float(match.group(1))

        return dimension_data

    def extract_packaging(self, mpn):
        packaging_info = {'packaging': None, 'package_code': None}
        last_char = mpn[-1].upper()
        text_lower = self.text.lower()

        if 'paper tape' in text_lower:
            tape_type = 'P'
            packaging_info['packaging'] = 'paper tape'
        elif 'plastic tape' in text_lower:
            tape_type = 'E'
            packaging_info['packaging'] = 'plastic tape'
        else:
            tape_type = None

        match = re.search(r"W(\d)P(\d)", self.text.upper())
        if match and tape_type:
            width = match.group(1)
            pitch = match.group(2)
            packaging_info['package_code'] = f"{tape_type}08{pitch}"

        return packaging_info

    def extract_all(self, mpn):
        result = {}
        result.update(self.extract_dimensions())
        result.update(self.extract_packaging(mpn))
        return result

# Run from command line
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python murata_parser_standalone.py <pdf_path> <mpn>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    mpn = sys.argv[2]

    parser = MurataParser(pdf_path)
    result = parser.extract_all(mpn)
    print("\n📦 Final parsed output:")
    print(result)
