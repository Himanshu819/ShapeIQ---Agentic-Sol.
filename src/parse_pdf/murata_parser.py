# # src/parse_pdf/murata_parser.py
# from src.parse_pdf.base_parser import BaseParser
# import re
# import logging

# class MurataParser(BaseParser):
#     # Mapping for standard EIA/Imperial package sizes from Metric L x W (in mm)
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
#     }

#     def __init__(self, pdf_path: str, mpn: str = ""):
#         super().__init__(pdf_path) 
#         self.mpn = mpn.upper()
#         # logging.basicConfig(level=logging.INFO) # Consider moving this to main.py to avoid re-configuring on every object creation

#     def _get_component_type_char(self) -> str:
#         """Infers the single-character component type for the SHAPE name."""
#         if self.mpn.startswith("GRM") or self.mpn.startswith("GCM") or self.mpn.startswith("GRT") or self.mpn.startswith("GCJ"):
#             return "C" # Capacitor
#         return "" 

#     def _get_shape_name(self, length: float, width: float, component_type_char: str) -> str | None:
#         """Generates the SHAPE name (e.g., C0402) from component dimensions and type.""" # <--- CORRECTED LINE (removed citation)
#         if length is None or width is None or not component_type_char:
#             return None

#         rounded_L = round(length, 1)
#         rounded_W = round(width, 1)

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
#         Tries multiple strategies for different Murata PDF formats.
#         """
#         dimension_data = {'length': None, 'width': None, 'thickness': None}

#         # Strategy 1: Specific table header for GCM15 type PDFs (e.g., GCM155... from Page 8)
#         table_pattern_gcm15 = re.compile(
#             r"Type\s*\n\s*GCM15\s*5\s*\n.*?" # Find 'Type GCM15 5'
#             r"L\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+\s*" # Capture L (e.g. 1.0+/-0.05)
#             r"W\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+\s*" # Capture W
#             r"T\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+",  # Capture T
#             re.DOTALL | re.IGNORECASE
#         )
#         match_gcm15 = table_pattern_gcm15.search(self.text)

#         if match_gcm15:
#             dimension_data['length'] = float(match_gcm15.group(1))
#             dimension_data['width'] = float(match_gcm15.group(2))
#             dimension_data['thickness'] = float(match_gcm15.group(3))
#             logging.info(f"MurataParser: Strategy 1 (GCM15 table) successful. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
#             if all(dimension_data.values()): return dimension_data 

#         # Strategy 2: Direct L: 1.0, W: 0.5, T: 0.5 patterns (often on Page 2 for GRT033C81A104KE01J type)
#         l_pattern_direct = re.compile(r"\bL\s*[:：]?\s*(\d+\.\d+)")
#         w_pattern_direct = re.compile(r"\bW\s*[:：]?\s*(\d+\.\d+)")
#         t_pattern_direct = re.compile(r"\bT\s*[:：]?\s*(\d+\.\d+)")

#         l_match = l_pattern_direct.search(self.text)
#         w_match = w_pattern_direct.search(self.text)
#         t_match = t_pattern_direct.search(self.text)

#         if l_match: dimension_data['length'] = float(l_match.group(1))
#         if w_match: dimension_data['width'] = float(w_match.group(1))
#         if t_match: dimension_data['thickness'] = float(t_match.group(1))
        
#         if all(dimension_data.values()): 
#             logging.info(f"MurataParser: Strategy 2 (direct L/W/T labels) successful. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
#             return dimension_data

#         # Strategy 3: Fallback for grouped format like: "1.0 ± 0.05 0.5 ± 0.05 0.5 ± 0.05" (general pattern)
#         if not all(dimension_data.values()):
#             fallback_grouped = re.search(
#                 r"(?<!\d)(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+\s+" 
#                 r"(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+\s+" 
#                 r"(\d+\.\d+)\s*[±+\-]\s*\d+\.\d+",    
#                 self.text
#             )
#             if fallback_grouped:
#                 dimension_data['length'] = float(fallback_grouped.group(1)) 
#                 dimension_data['width'] = float(fallback_grouped.group(2))
#                 dimension_data['thickness'] = float(fallback_grouped.group(3))
#                 logging.info(f"MurataParser: Strategy 3 (grouped fallback) successful. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
#                 if all(dimension_data.values()): return dimension_data 

#         # Final fallback: first 3 plausible floats (least reliable)
#         if not all(dimension_data.values()):
#             floats = re.findall(r"\b(\d+\.\d+)\b", self.text)
#             filtered_floats = [float(f) for f in floats if float(f) >= 0.2 or float(f) in [0.1, 0.15]] 
            
#             if len(filtered_floats) >= 3:
#                 dimension_data['length'] = filtered_floats[0]
#                 dimension_data['width'] = filtered_floats[1]
#                 dimension_data['thickness'] = filtered_floats[2]
#                 logging.info(f"MurataParser: Strategy 4 (generic float fallback) used. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")

#         if not all(dimension_data.values()):
#             logging.warning("MurataParser: Incomplete L/W/T dimension data extracted after all strategies failed.")

#         return dimension_data

#     def extract_pin_data(self) -> dict:
#         """
#         Extracts Pin length, Pin Width, Pin Pitch, Pin Count for chip components.
#         """
#         pin_data = {
#             'pin_length': None,
#             'pin_width': None,
#             'pin_pitch': None,
#             'pin_count': 2 
#         }
        
#         # Search for 'g' dimension (electrode spacing) which serves as 'pin pitch' for chips
#         g_match = re.search(r"g\s*(\d+\.\d+)\s*(?:min\.)?", self.text, re.IGNORECASE)
#         if g_match:
#             pin_data['pin_pitch'] = float(g_match.group(1))
#             logging.info(f"MurataParser: Extracted Pin Pitch (g dimension): {pin_data['pin_pitch']} mm")
#         else:
#             logging.warning("MurataParser: 'g' dimension (Pin Pitch) not found.")

#         return pin_data

#     def extract_packaging(self, mpn: str) -> dict:
#         """
#         Extract packaging type and infer packaging code.
#         """
#         packaging_info = {'packaging': None, 'package_code': None}
#         text = self.text.lower()
#         upper_text = self.text.upper()

#         tape_type_char = None 
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
#         match = re.search(r"W(\d)P(\d)", upper_text)
#         if match and tape_type_char:
#             width_code = match.group(1) 
#             pitch_code = match.group(2) 
            
#             packaging_info['package_code'] = f"{tape_type_char}0{width_code}{pitch_code.zfill(2)}"
#             logging.info(f"MurataParser: Reel format matched: W{width_code}P{pitch_code} -> {packaging_info['package_code']}")
#         else:
#             logging.warning("MurataParser: Packaging code not detected from W/P pattern or tape type missing.")

#         return packaging_info

#     def extract_all(self, mpn: str) -> dict:
#         logging.info(f"MurataParser: Starting extraction for MPN: {mpn}")
        
#         result = {
#             'mpn': mpn,
#             'length': None, 'width': None, 'thickness': None,
#             'pin_length': None, 'pin_width': None, 'pin_pitch': None, 'pin_count': None,
#             'packaging': None, 'package_code': None, 'shape_name': None 
#         }

#         body_dims = self.extract_dimensions()
#         result.update(body_dims)

#         pin_data = self.extract_pin_data()
#         result.update(pin_data)

#         packaging_info = self.extract_packaging(mpn)
#         result.update(packaging_info)

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
        (0.4, 0.2): "01005", 
        (0.6, 0.3): "0201",  
        (1.0, 0.5): "0402",  
        (1.6, 0.8): "0603",  
        (2.0, 1.25): "0805", 
        (3.2, 1.6): "1206",  
        (3.2, 2.5): "1210",  
        (4.5, 3.2): "1812",  
        (5.7, 5.0): "2220",  
    }

    def __init__(self, pdf_path: str, mpn: str = ""):
        super().__init__(pdf_path) 
        self.mpn = mpn.upper()
        # logging.basicConfig(level=logging.INFO) # Keep logging config in main.py

    def _get_component_type_char(self) -> str:
        """Infers the single-character component type for the SHAPE name."""
        if self.mpn.startswith(("GRM", "GCM", "GRT", "GCJ")): # Added GCJ
            return "C" # Capacitor
        return "" 

    def _get_shape_name(self, length: float, width: float, component_type_char: str) -> str | None:
        """Generates the SHAPE name (e.g., C0402) from component dimensions and type."""
        if length is None or width is None or not component_type_char:
            logging.warning("MurataParser: Missing length/width/component_type to generate SHAPE name.")
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
        Tries multiple strategies for different Murata PDF formats, prioritizing specific ones.
        """
        dimension_data = {'length': None, 'width': None, 'thickness': None}

        # Strategy 1: Specific table header for GCM15 type PDFs (e.g., GCM155... from Page 8)
        table_pattern_gcm15 = re.compile(
            r"Type\s*\n\s*GCM15\s*5\s*\n.*?" 
            r"L\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+\s*" 
            r"W\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+\s*" 
            r"T\s*(\d+\.\d+)\s*[\+-±]\s*\d+\.\d+",  
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
        
        if all(dimension_data.values()): # If all found, return
            logging.info(f"MurataParser: Strategy 2 (direct L/W/T labels) successful. L:{dimension_data['length']}, W:{dimension_data['width']}, T:{dimension_data['thickness']}")
            return dimension_data

        # Strategy 3: Fallback for grouped format like: "1.0 ± 0.05 0.5 ± 0.05 0.5 ± 0.05" (general pattern)
        if not all(dimension_data.values()): # Only if previous strategies failed
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

        # Strategy 4: Final fallback: first 3 plausible floats (least reliable, last resort)
        if not all(dimension_data.values()): # Only if previous strategies failed
            floats = re.findall(r"\b(\d+\.\d+)\b", self.text)
            filtered_floats = [f for f in floats if float(f) >= 0.2 or float(f) in [0.1, 0.15]] 
            
            if len(filtered_floats) >= 3:
                dimension_data['length'] = float(filtered_floats[0])
                dimension_data['width'] = float(filtered_floats[1])
                dimension_data['thickness'] = float(filtered_floats[2])
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
            'pin_count': 2 # Default for 2-terminal passive components
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