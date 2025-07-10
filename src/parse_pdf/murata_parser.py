
# # src/parse_pdf/murata_parser.py
# from src.parse_pdf.base_parser import BaseParser
# import re
# import logging

# class MurataParser(BaseParser):
#     # Mapping for standard EIA/Imperial package sizes from Metric L x W (in mm)
#     # This should be comprehensive based on your Nexim library and common industry standards.
#     # Note: These are typical values, adjust if your specific Murata datasheet uses slightly different nominals.
#     PACKAGE_SIZE_MAP = {
#         (0.4, 0.2): "01005", # 0.4mm x 0.2mm
#         (0.6, 0.3): "0201",  # 0.6mm x 0.3mm
#         (1.0, 0.5): "0402",  # 1.0mm x 0.5mm
#         (1.6, 0.8): "0603",  # 1.6mm x 0.8mm
#         (2.0, 1.25): "0805", # 2.0mm x 1.25mm
#         (3.2, 1.6): "1206",  # 3.2mm x 1.6mm
#         (3.2, 2.5): "1210",  # 3.2mm x 2.5mm
#         (4.5, 3.2): "1812",  # 4.5mm x 3.2mm
#         (5.7, 5.0): "2220",  # 5.7mm x 5.0mm
#         # Add more common sizes as needed for other Murata series (e.g., for GRM/GCM)
#     }

#     def __init__(self, pdf_path: str, mpn: str = ""):
#         super().__init__(pdf_path) # Calls BaseParser's init to set self.text
#         self.mpn = mpn.upper()
#         logging.basicConfig(level=logging.INFO) # Ensure logging is configured

#     def _get_component_type_char(self) -> str:
#         """
#         Infers the single-character component type for the SHAPE name (e.g., 'C' for Capacitor).
#         For Murata GRM/GCM, it's typically a Capacitor. This can be expanded for other vendors/MPNs.
#         """
#         # Based on MPN prefix
#         if self.mpn.startswith("GRM") or self.mpn.startswith("GCM") or self.mpn.startswith("GRT"):
#             return "C" # Capacitor
#         # Add more rules as needed for other components
#         # elif self.mpn.startswith("ERJ"): return "R" # Resistor
#         # elif self.mpn.startswith("SK"): return "D" # Diode
#         return "" # Default to empty if unknown

#     def _get_shape_name(self, length: float, width: float, component_type_char: str) -> str | None:
#         """
#         Generates the SHAPE name (e.g., C0402) from component dimensions and type.
#         """
#         if length is None or width is None or not component_type_char:
#             return None

#         # Round dimensions to a common precision for mapping
#         rounded_L = round(length, 1)
#         rounded_W = round(width, 1)

#         # Handle specific cases for (0.6, 0.3) where it might be 0201 or 0603 in some contexts
#         # Based on your Murata PDF for GCM1555C1H221JA16D.pdf, it's 1.0x0.5 -> 0402 [cite: 4265]
#         # And the image shows C0402, C0603 etc.
#         package_size_code = self.PACKAGE_SIZE_MAP.get((rounded_L, rounded_W))
        
#         if not package_size_code:
#             # Fallback for exact integer sizes if float doesn't match
#             package_size_code = self.PACKAGE_SIZE_MAP.get((int(length), int(width)))

#         if package_size_code:
#             return f"{component_type_char}{package_size_code}"
#         else:
#             logging.warning(f"MurataParser: No standard shape code found for L:{length} x W:{width} mm. Cannot determine SHAPE name.")
#             return None

#     def extract_dimensions(self) -> dict:
#         """
#         Extract L, W, T from 'Type & Dimension' section of Murata PDF.
#         Supports direct L/W/T patterns or fallback grouped formats like:
#         "1.0 ± 0.05 0.5 ± 0.05 0.5 ± 0.05"
#         """
#         dimension_data = {'length': None, 'width': None, 'thickness': None}

#         # Look for the 'Type & Dimension' section to narrow down the search area
#         # This PDF has 'Type & Dimension' on Page 2 [cite: 4247] and the table on Page 8 (for GCM15)[cite: 4336].
#         # We need to refine BaseParser's text extraction or pass the whole text and search within it.
#         # For this Murata PDF, the key dimension table is on Page 8, under "Dimensions (Chip)" for GCM15 [cite: 4336]
#         # Example line: "GCM15","5","1.0+/-0.05","0.5+/-0.05","0.5+/-0.05",... [cite: 4336]

#         # First, try to find the specific table header (L, W, T) in the context of GCM15
#         # The table on Page 8 is excellent for this [cite: 4336]
#         # This regex attempts to find the "L W T" header and then capture the three numbers below it for GCM15
#         table_pattern = re.compile(
#             r"Type\s*\n\s*GCM15\s*5\s*\n.*?" # Find 'Type GCM15 5' and then any lines until L,W,T header
#             r"L\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+\s*" # Capture L (e.g. 1.0+/-0.05)
#             r"W\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+\s*" # Capture W
#             r"T\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+",  # Capture T
#             re.DOTALL | re.IGNORECASE
#         )
#         match_table = table_pattern.search(self.text)

#         if match_table:
#             dimension_data['length'] = float(match_table.group(1))
#             dimension_data['width'] = float(match_table.group(2))
#             dimension_data['thickness'] = float(match_table.group(3))
#             logging.info(f"MurataParser: Extracted from GCM15 table. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
#             return dimension_data


#         # Fallback 1: Direct L: 1.0, W: 0.5, T: 0.5 patterns (less common in this specific PDF, but generally useful)
#         l_pattern = re.compile(r"\bL\s*[:：]?\s*(\d+\.\d+)")
#         w_pattern = re.compile(r"\bW\s*[:：]?\s*(\d+\.\d+)")
#         t_pattern = re.compile(r"\bT\s*[:：]?\s*(\d+\.\d+)")

#         l_match = l_pattern.search(self.text)
#         w_match = w_pattern.search(self.text)
#         t_match = t_pattern.search(self.text)

#         if l_match: dimension_data['length'] = float(l_match.group(1))
#         if w_match: dimension_data['width'] = float(w_match.group(1))
#         if t_match: dimension_data['thickness'] = float(t_match.group(1))
        
#         if all(dimension_data.values()): # If all found from direct labels, return
#             logging.info(f"MurataParser: Extracted from direct labels. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
#             return dimension_data


#         # Fallback 2: grouped format like: "1.0 ± 0.05 0.5 ± 0.05 0.5 ± 0.05"
#         if not all(dimension_data.values()):
#             fallback_grouped = re.search(
#                 r"(?<!\d)(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+\s+" # Length
#                 r"(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+\s+" # Width
#                 r"(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+",    # Thickness
#                 self.text
#             )
#             if fallback_grouped:
#                 dimension_data['length'] = dimension_data['length'] or float(fallback_grouped.group(1))
#                 dimension_data['width'] = dimension_data['width'] or float(fallback_grouped.group(2))
#                 dimension_data['thickness'] = dimension_data['thickness'] or float(fallback_grouped.group(3))
#                 logging.info(f"MurataParser: Used grouped fallback. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
#                 if all(dimension_data.values()): return dimension_data # Return if all found

#         # Final fallback: first 3 floats (least reliable, for debugging or very unstructured docs)
#         if not all(dimension_data.values()):
#             floats = re.findall(r"\b(\d+\.\d+)\b", self.text)
#             # Heuristic to filter out very small tolerance-like numbers or common non-dimension floats
#             filtered_floats = [f for f in floats if float(f) > 0.1 or (float(f) == 0.05 and 'g' in self.text and '0.05' in self.text)] # Special case for 0.05 if it's explicitly a dimension.
            
#             if len(filtered_floats) >= 3:
#                 dimension_data['length'] = dimension_data['length'] or float(filtered_floats[0])
#                 dimension_data['width'] = dimension_data['width'] or float(filtered_floats[1])
#                 dimension_data['thickness'] = dimension_data['thickness'] or float(filtered_floats[2])
#                 logging.info(f"MurataParser: Used generic float fallback. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")

#         if not all(dimension_data.values()):
#             logging.warning("MurataParser: Incomplete L/W/T dimension data extracted after all attempts.")

#         return dimension_data

#     def extract_pin_data(self) -> dict:
#         """
#         Extracts Pin length, Pin Width, Pin Pitch, Pin Count for chip components.
#         For 2-pin passive chips, Pin Count is typically 2.
#         Pin Pitch can be inferred from 'g' dimension in Murata diagrams (terminal spacing).
#         Pin length/width are often not explicitly given for chip components in the same way as leads.
#         """
#         pin_data = {
#             'pin_length': None,
#             'pin_width': None,
#             'pin_pitch': None,
#             'pin_count': 2 # Default for 2-terminal passive components [cite: 52]
#         }
        
#         # Search for 'g' dimension (electrode spacing) which can be considered 'pin pitch' for chips
#         # Found on Page 8, GCM15 table, column 'g' [cite: 4336]
#         # Look for "g" followed by a float in a relevant table context
#         g_match = re.search(r"g\s*(\d+\.\d+)\s*min\.", self.text, re.IGNORECASE)
#         if g_match:
#             pin_data['pin_pitch'] = float(g_match.group(1))
#             logging.info(f"MurataParser: Extracted Pin Pitch (g dimension): {pin_data['pin_pitch']} mm")
#         else:
#             logging.warning("MurataParser: 'g' dimension (Pin Pitch) not found.")

#         # For passive chips, Pin Length and Pin Width are usually not discrete dimensions like for active components.
#         # They are part of the overall L/W/T. Keep as None or infer from electrode dimensions if found.
#         # For now, keep as None to reflect that datasheets don't usually provide these for simple chips.

#         return pin_data


#     def extract_packaging(self, mpn: str) -> dict:
#         """
#         Extract packaging type and infer packaging code like:
#         'paper tape' + W8P2 → P0802
#         """
#         packaging_info = {'packaging': None, 'package_code': None}
#         text = self.text.lower()
#         upper_text = self.text.upper()

#         tape_type_char = None # 'P' or 'E'
#         if 'paper tape' in text:
#             tape_type_char = 'P'
#             packaging_info['packaging'] = 'paper tape'
#             logging.info("MurataParser: Detected packaging type: paper tape")
#         elif 'plastic tape' in text:
#             tape_type_char = 'E'
#             packaging_info['packaging'] = 'plastic tape'
#             logging.info("MurataParser: Detected packaging type: plastic tape")
#         else:
#             logging.warning("MurataParser: Tape type (paper/plastic) not explicitly found.")

#         # Find W8P2/W8P4-like reel descriptions
#         # Example found in PDF: "180mm Reel PAPER Tape W8P2" [cite: 4270]
#         match = re.search(r"W(\d)P(\d)", upper_text)
#         if match and tape_type_char:
#             width_code = match.group(1) # e.g., '8'
#             pitch_code = match.group(2) # e.g., '2'
            
#             # Format as P0802 or E0804
#             packaging_info['package_code'] = f"{tape_type_char}0{width_code}{pitch_code.zfill(2)}"
#             logging.info(f"MurataParser: Reel format matched: W{width_code}P{pitch_code} -> {packaging_info['package_code']}")
#         else:
#             logging.warning("MurataParser: Packaging code not detected from W/P pattern or tape type missing.")

#         return packaging_info


#     def extract_all(self, mpn: str) -> dict:
#         logging.info(f"MurataParser: Starting extraction for MPN: {mpn}")
        
#         # Initialize all fields to None to ensure consistency in output CSV
#         result = {
#             'mpn': mpn,
#             'length': None,
#             'width': None,
#             'thickness': None,
#             'pin_length': None,
#             'pin_width': None,
#             'pin_pitch': None,
#             'pin_count': None,
#             'packaging': None,
#             'package_code': None,
#             'shape_name': None # This will be generated last
#         }

#         # Extract body dimensions
#         body_dims = self.extract_dimensions()
#         result.update(body_dims)

#         # Extract pin data (even if mostly N/A for passives, keep fields consistent)
#         pin_data = self.extract_pin_data()
#         result.update(pin_data)

#         # Extract packaging info
#         packaging_info = self.extract_packaging(mpn)
#         result.update(packaging_info)

#         # Generate SHAPE name if body dimensions are available
#         component_type_char = self._get_component_type_char()
#         if result['length'] is not None and result['width'] is not None and component_type_char:
#             result['shape_name'] = self._get_shape_name(result['length'], result['width'], component_type_char)
#         else:
#             logging.warning("MurataParser: Could not determine SHAPE name due to missing dimensions or component type.")

#         logging.info(f"MurataParser: Final extracted result for {mpn}: {result}")
#         return result

# src/parse_pdf/murata_parser.py
from src.parse_pdf.base_parser import BaseParser
import re
import logging

class MurataParser(BaseParser):
    # Mapping for standard EIA/Imperial package sizes from Metric L x W (in mm)
    PACKAGE_SIZE_MAP = {
        (0.4, 0.2): "01005", # 0.4mm x 0.2mm
        (0.6, 0.3): "0201",  # 0.6mm x 0.3mm
        (1.0, 0.5): "0402",  # 1.0mm x 0.5mm
        (1.6, 0.8): "0603",  # 1.6mm x 0.8mm
        (2.0, 1.25): "0805", # 2.0mm x 1.25mm
        (3.2, 1.6): "1206",  # 3.2mm x 1.6mm
        (3.2, 2.5): "1210",  # 3.2mm x 2.5mm
        (4.5, 3.2): "1812",  # 4.5mm x 3.2mm
        (5.7, 5.0): "2220",  # 5.7mm x 5.0mm
    }

    def __init__(self, pdf_path: str, mpn: str = ""):
        super().__init__(pdf_path) 
        self.mpn = mpn.upper()
        # logging.basicConfig(level=logging.INFO) # Consider moving this to main.py to avoid re-configuring on every object creation

    def _get_component_type_char(self) -> str:
        """Infers the single-character component type for the SHAPE name."""
        if self.mpn.startswith("GRM") or self.mpn.startswith("GCM") or self.mpn.startswith("GRT"):
            return "C" # Capacitor
        return "" 

    def _get_shape_name(self, length: float, width: float, component_type_char: str) -> str | None:
        """Generates the SHAPE name (e.g., C0402) from component dimensions and type.""" # <--- CORRECTED LINE (removed citation)
        if length is None or width is None or not component_type_char:
            return None

        rounded_L = round(length, 1)
        rounded_W = round(width, 1)

        package_size_code = self.PACKAGE_SIZE_MAP.get((rounded_L, rounded_W))
        
        if not package_size_code:
            # Fallback for exact integer sizes if float doesn't match
            package_size_code = self.PACKAGE_SIZE_MAP.get((int(length), int(width)))

        if package_size_code:
            return f"{component_type_char}{package_size_code}"
        else:
            logging.warning(f"MurataParser: No standard shape code found for L:{length} x W:{width} mm. Cannot determine SHAPE name.")
            return None

    def extract_dimensions(self) -> dict:
        """
        Extract L, W, T from 'Type & Dimension' section of Murata PDF.
        Tries multiple strategies for different Murata PDF formats.
        """
        dimension_data = {'length': None, 'width': None, 'thickness': None}

        # Strategy 1: Specific table header for GCM15 type PDFs (e.g., GCM155... from Page 8)
        table_pattern_gcm15 = re.compile(
            r"Type\s*\n\s*GCM15\s*5\s*\n.*?" # Find 'Type GCM15 5'
            r"L\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+\s*" # Capture L (e.g. 1.0+/-0.05)
            r"W\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+\s*" # Capture W
            r"T\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+",  # Capture T
            re.DOTALL | re.IGNORECASE
        )
        match_gcm15 = table_pattern_gcm15.search(self.text)

        if match_gcm15:
            dimension_data['length'] = float(match_gcm15.group(1))
            dimension_data['width'] = float(match_gcm15.group(2))
            dimension_data['thickness'] = float(match_gcm15.group(3))
            logging.info(f"MurataParser: Strategy 1 (GCM15 table) successful. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
            if all(dimension_data.values()): return dimension_data 

        # Strategy 2: Direct L: 1.0, W: 0.5, T: 0.5 patterns (often on Page 2 for GRT033C81A104KE01J type)
        l_pattern_direct = re.compile(r"\bL\s*[:：]?\s*(\d+\.\d+)")
        w_pattern_direct = re.compile(r"\bW\s*[:：]?\s*(\d+\.\d+)")
        t_pattern_direct = re.compile(r"\bT\s*[:：]?\s*(\d+\.\d+)")

        l_match = l_pattern_direct.search(self.text)
        w_match = w_pattern_direct.search(self.text)
        t_match = t_pattern_direct.search(self.text)

        if l_match: dimension_data['length'] = float(l_match.group(1))
        if w_match: dimension_data['width'] = float(w_match.group(1))
        if t_match: dimension_data['thickness'] = float(t_match.group(1))
        
        if all(dimension_data.values()): 
            logging.info(f"MurataParser: Strategy 2 (direct L/W/T labels) successful. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
            return dimension_data

        # Strategy 3: Fallback for grouped format like: "1.0 ± 0.05 0.5 ± 0.05 0.5 ± 0.05" (general pattern)
        if not all(dimension_data.values()):
            fallback_grouped = re.search(
                r"(?<!\d)(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+\s+" 
                r"(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+\s+" 
                r"(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+",    
                self.text
            )
            if fallback_grouped:
                dimension_data['length'] = float(fallback_grouped.group(1)) 
                dimension_data['width'] = float(fallback_grouped.group(2))
                dimension_data['thickness'] = float(fallback_grouped.group(3))
                logging.info(f"MurataParser: Strategy 3 (grouped fallback) successful. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
                if all(dimension_data.values()): return dimension_data 

        # Final fallback: first 3 plausible floats (least reliable)
        if not all(dimension_data.values()):
            floats = re.findall(r"\b(\d+\.\d+)\b", self.text)
            filtered_floats = [float(f) for f in floats if float(f) >= 0.2 or float(f) in [0.1, 0.15]] 
            
            if len(filtered_floats) >= 3:
                dimension_data['length'] = filtered_floats[0]
                dimension_data['width'] = filtered_floats[1]
                dimension_data['thickness'] = filtered_floats[2]
                logging.info(f"MurataParser: Strategy 4 (generic float fallback) used. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")

        if not all(dimension_data.values()):
            logging.warning("MurataParser: Incomplete L/W/T dimension data extracted after all strategies failed.")

        return dimension_data

    def extract_pin_data(self) -> dict:
        """
        Extracts Pin length, Pin Width, Pin Pitch, Pin Count for chip components.
        """
        pin_data = {
            'pin_length': None,
            'pin_width': None,
            'pin_pitch': None,
            'pin_count': 2 
        }
        
        # Search for 'g' dimension (electrode spacing) which serves as 'pin pitch' for chips
        g_match = re.search(r"g\s*(\d+\.\d+)\s*(?:min\.)?", self.text, re.IGNORECASE)
        if g_match:
            pin_data['pin_pitch'] = float(g_match.group(1))
            logging.info(f"MurataParser: Extracted Pin Pitch (g dimension): {pin_data['pin_pitch']} mm")
        else:
            logging.warning("MurataParser: 'g' dimension (Pin Pitch) not found.")

        return pin_data

    def extract_packaging(self, mpn: str) -> dict:
        """
        Extract packaging type and infer packaging code.
        """
        packaging_info = {'packaging': None, 'package_code': None}
        text = self.text.lower()
        upper_text = self.text.upper()

        tape_type_char = None 
        if 'paper tape' in text:
            tape_type_char = 'P'
            packaging_info['packaging'] = 'paper tape'
            logging.info("MurataParser: Detected packaging type: paper tape")
        elif 'plastic tape' in text:
            tape_type_char = 'E'
            packaging_info['packaging'] = 'plastic tape'
            logging.info("MurataParser: Detected packaging type: plastic tape")
        else:
            logging.warning("MurataParser: Tape type (paper/plastic) not explicitly found.")

        # Find W8P2/W8P4-like reel descriptions
        match = re.search(r"W(\d)P(\d)", upper_text)
        if match and tape_type_char:
            width_code = match.group(1) 
            pitch_code = match.group(2) 
            
            packaging_info['package_code'] = f"{tape_type_char}0{width_code}{pitch_code.zfill(2)}"
            logging.info(f"MurataParser: Reel format matched: W{width_code}P{pitch_code} -> {packaging_info['package_code']}")
        else:
            logging.warning("MurataParser: Packaging code not detected from W/P pattern or tape type missing.")

        return packaging_info

    def extract_all(self, mpn: str) -> dict:
        logging.info(f"MurataParser: Starting extraction for MPN: {mpn}")
        
        result = {
            'mpn': mpn,
            'length': None, 'width': None, 'thickness': None,
            'pin_length': None, 'pin_width': None, 'pin_pitch': None, 'pin_count': None,
            'packaging': None, 'package_code': None, 'shape_name': None 
        }

        body_dims = self.extract_dimensions()
        result.update(body_dims)

        pin_data = self.extract_pin_data()
        result.update(pin_data)

        packaging_info = self.extract_packaging(mpn)
        result.update(packaging_info)

        component_type_char = self._get_component_type_char()
        if result['length'] is not None and result['width'] is not None and component_type_char:
            result['shape_name'] = self._get_shape_name(result['length'], result['width'], component_type_char)
        else:
            logging.warning("MurataParser: Could not determine SHAPE name due to missing dimensions or component type.")

        logging.info(f"MurataParser: Final extracted result for {mpn}: {result}")
        return result