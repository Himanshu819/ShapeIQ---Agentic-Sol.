# # src/tools/vendor_rules.py
# import re

# # Murata chip dimension rules
# MURATA_SIZE_MAP = {
#     "015": {"length": 0.4, "width": 0.2, "thickness": 0.2, "pitch": 2.0},
#     "018": {"length": 0.6, "width": 0.3, "thickness": 0.3, "pitch": 2.0},
#     "021": {"length": 0.6, "width": 0.3, "thickness": 0.3, "pitch": 2.0},
#     "03":  {"length": 0.6, "width": 0.3, "thickness": 0.3, "pitch": 2.0},
#     "15":  {"length": 1.0, "width": 0.5, "thickness": 0.5, "pitch": 2.0},
#     "18":  {"length": 1.6, "width": 0.8, "thickness": 0.8, "pitch": 2.0},
#     "21":  {"length": 2.0, "width": 1.25, "thickness": 1.25, "pitch": 4.0},
#     "31":  {"length": 3.2, "width": 1.6, "thickness": 1.6, "pitch": 4.0},
#     "32":  {"length": 3.2, "width": 2.5, "thickness": 2.5, "pitch": 4.0},
#     "43":  {"length": 4.5, "width": 3.2, "thickness": 3.2, "pitch": 4.0},
#     "55":  {"length": 5.7, "width": 5.0, "thickness": 5.0, "pitch": 8.0}
# }

# # Packaging code mappings
# MURATA_PACKAGING = {
#     "D": "paper tape",
#     "W": "paper tape",
#     "J": "paper tape",
#     "V": "paper tape",
#     "K": "plastic tape",
#     "L": "plastic tape",
# }

# def parse_murata_mpn(mpn: str) -> dict:
#     mpn = mpn.upper()
#     parsed = {
#         "length": None,
#         "width": None,
#         "thickness": None,
#         "pitch": None,
#         "packaging": None,
#         "package_code": None
#     }

#     # Extract size code: GRM155... → '15'
#     size_match = re.match(r"(GRM|GCM)(\d{2})\d", mpn)
#     if size_match:
#         size_key = size_match.group(2)
#         dims = MURATA_SIZE_MAP.get(size_key)
#         if dims:
#             parsed.update(dims)

#     # Get packaging type
#     suffix = mpn[-1]
#     packaging_type = MURATA_PACKAGING.get(suffix)
#     if packaging_type:
#         parsed["packaging"] = packaging_type

#     # Generate package_code (e.g., P0802, E0804) if packaging and pitch available
#     if parsed["packaging"] and parsed["pitch"]:
#         pitch = int(parsed["pitch"])
#         type_letter = "P" if "paper" in parsed["packaging"] else "E"
#         parsed["package_code"] = f"{type_letter}08{pitch}"

#     return parsed

# src/tools/vendor_rules.py
import re

# Murata chip dimension rules
MURATA_SIZE_MAP = {
    # Format: "Size Code": {"length": L, "width": W, "thickness": T, "pitch": P}
    "015": {"length": 0.4, "width": 0.2, "thickness": 0.2, "pitch": 2.0},
    "018": {"length": 0.6, "width": 0.3, "thickness": 0.3, "pitch": 2.0}, # GCM018, GRM018
    "021": {"length": 0.6, "width": 0.3, "thickness": 0.3, "pitch": 2.0}, # GRT021
    "03":  {"length": 0.6, "width": 0.3, "thickness": 0.3, "pitch": 2.0}, # Common for some GRM series (e.g. 0.6x0.3mm sometimes mapped to size code '03')
    "15":  {"length": 1.0, "width": 0.5, "thickness": 0.5, "pitch": 2.0}, # GCM155, GRM155
    "18":  {"length": 1.6, "width": 0.8, "thickness": 0.8, "pitch": 2.0}, # GCM188, GRM188
    "21":  {"length": 2.0, "width": 1.25, "thickness": 1.25, "pitch": 4.0}, # GCM21, GRM21
    "31":  {"length": 3.2, "width": 1.6, "thickness": 1.6, "pitch": 4.0}, # GCM31, GRM31
    "32":  {"length": 3.2, "width": 2.5, "thickness": 2.5, "pitch": 4.0}, # GCM32, GRM32
    "43":  {"length": 4.5, "width": 3.2, "thickness": 3.2, "pitch": 4.0}, # GCM43, GRM43
    "55":  {"length": 5.7, "width": 5.0, "thickness": 5.0, "pitch": 8.0}  # GCM55, GRM55
}

# Mapping for standard EIA/Imperial package sizes from Metric L x W (in mm)
# This is crucial for deriving the SHAPE name (e.g., C0402 from 1.0x0.5mm)
EIA_PACKAGE_SIZE_MAP = {
    (0.4, 0.2): "01005", # 0.4mm x 0.2mm (metric) -> EIA 01005
    (0.6, 0.3): "0201",  # 0.6mm x 0.3mm (metric) -> EIA 0201
    (1.0, 0.5): "0402",  # 1.0mm x 0.5mm (metric) -> EIA 0402
    (1.6, 0.8): "0603",  # 1.6mm x 0.8mm (metric) -> EIA 0603
    (2.0, 1.25): "0805", # 2.0mm x 1.25mm (metric) -> EIA 0805
    (3.2, 1.6): "1206",  # 3.2mm x 1.6mm (metric) -> EIA 1206
    (3.2, 2.5): "1210",  # 3.2mm x 2.5mm (metric) -> EIA 1210
    (4.5, 3.2): "1812",  # 4.5mm x 3.2mm (metric) -> EIA 1812
    (5.7, 5.0): "2220",  # 5.7mm x 5.0mm (metric) -> EIA 2220
    # Add more as per your Nexim library
}


# Packaging code mappings (last char of MPN often denotes packaging type)
MURATA_PACKAGING = {
    "D": "paper tape", # 180mm Reel PAPER Tape W8P2 (common for D)
    "W": "paper tape", # 180mm Reel PAPER Tape W8P1 (common for W)
    "J": "paper tape", # 330mm Reel PAPER Tape W8P2 (common for J)
    "V": "paper tape", # 330mm Reel PAPER Tape W8P1 (common for V)
    "K": "plastic tape",
    "L": "plastic tape",
}

def parse_murata_mpn(mpn: str) -> dict:
    mpn = mpn.upper()
    parsed = {
        "length": None,
        "width": None,
        "thickness": None,
        "pitch": None,       # Pitch from MURATA_SIZE_MAP (g dimension for chips)
        "packaging": None,
        "package_code": None,
        "pin_length": None,  # Not typically applicable for passive chips, but included for CSV
        "pin_width": None,   # Not typically applicable for passive chips, but included for CSV
        "pin_pitch": None,   # This will be same as 'pitch' from MURATA_SIZE_MAP for chips
        "pin_count": 2,      # Default for 2-terminal passive components
        "shape_name": None   # Nexim SHAPE name (e.g., C0402)
    }

    # Extract numeric size code: GRM155... → '15'
    size_match = re.match(r"(GRM|GCM|GRT)(\d{2})\d", mpn) # Added GRT prefix
    if size_match:
        size_key = size_match.group(2) # Gets "15", "18", etc.
        dims = MURATA_SIZE_MAP.get(size_key)
        if dims:
            parsed.update(dims)
            # For 2-pin chips, 'pitch' from MURATA_SIZE_MAP is often the 'pin_pitch'
            parsed["pin_pitch"] = dims["pitch"]

    # Get packaging type from last character
    suffix = mpn[-1]
    packaging_type = MURATA_PACKAGING.get(suffix)
    if packaging_type:
        parsed["packaging"] = packaging_type

    # Generate package_code (e.g., P0802, E0804) if packaging and pitch available
    if parsed["packaging"] and parsed["pin_pitch"]: # Use pin_pitch for consistency
        pitch = int(parsed["pin_pitch"])
        type_letter = "P" if "paper" in parsed["packaging"] else "E"
        # Standard format P080X, where 08 is 8mm tape width, X is pitch (e.g. 2mm pitch -> P0802)
        # This assumes a fixed 8mm tape width for these component types, which is common.
        parsed["package_code"] = f"{type_letter}08{str(pitch).zfill(2)}" # Zfill to ensure 02, 04 etc.

    # Generate SHAPE name (e.g., C0402, R0603)
    if parsed["length"] is not None and parsed["width"] is not None:
        component_type_char = ""
        # Infer component type based on MPN prefix (common for Murata Passives)
        if mpn.startswith(("GRM", "GCM", "GRT")):
            component_type_char = "C" # Capacitor
        # Add more component type inferences if needed for other prefixes/vendors

        if component_type_char:
            # Round dimensions for lookup
            rounded_L = round(parsed["length"], 1)
            rounded_W = round(parsed["width"], 1)
            
            eia_code = EIA_PACKAGE_SIZE_MAP.get((rounded_L, rounded_W))
            if eia_code:
                parsed["shape_name"] = f"{component_type_char}{eia_code}"
            else:
                # Fallback for small variations in float comparison or if 0.6x0.3 is sometimes 0603
                # This is a heuristic, tune as needed based on your Nexim mapping rules.
                if (rounded_L, rounded_W) == (0.6, 0.3): # 0.6x0.3 sometimes maps to 0201 in EIA
                    parsed["shape_name"] = f"{component_type_char}0201"
                elif (rounded_L, rounded_W) == (1.6, 0.8): # 1.6x0.8 sometimes maps to 0603 in EIA
                     parsed["shape_name"] = f"{component_type_char}0603"
                else:
                    logging.warning(f"VendorRules: No direct EIA code for {rounded_L}x{rounded_W} for SHAPE name.")


    return parsed