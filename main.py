import re
from typing import List, Dict, Union

def parse_lab_results(text: str) -> List[Dict[str, Union[str, float, bool, None]]]:
    """Parse lab report text and extract test results with reference ranges."""
    results = []
    
    # Preprocess the text - more comprehensive cleaning
    cleaned_text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Replace non-ASCII with space
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  # Normalize whitespace
    
    # Improved pattern to match lab test formats
    pattern = re.compile(
        r"(?P<test_name>[A-Z][A-Za-z\s\/\-\(\)]+?)\s+"  # Test name
        r"(?P<result_value>[><]?[\d\.]+)\s*"  # Result value (may include > or <)
        r"(?P<unit>[a-zA-Z\/%°]+)?\s*"  # Optional units
        r"(?:[\-\s]*"  # Separator between value and range
        r"(?P<ref_range>[\d\.]+\s*[-–]\s*[\d\.]+)\s*"  # Reference range
        r"(?P<ref_unit>[a-zA-Z\/%°]+)?)?"  # Optional reference units
    )
    
    # Find all matches in the text
    for match in pattern.finditer(cleaned_text):
        test_name = match.group("test_name").strip()
        result_value = match.group("result_value")
        unit = match.group("unit") or ""
        ref_range = match.group("ref_range") or ""
        ref_unit = match.group("ref_unit") or ""
        
        # Skip obviously invalid test names (e.g., metadata)
        if len(test_name) < 2 or test_name.isdigit() or "SPECIMEN" in test_name or "WARD" in test_name:
            continue
            
        # Clean up test name
        test_name = re.sub(r'\s+', ' ', test_name).strip()
        
        # Parse result value (handle > and < symbols)
        try:
            if result_value.startswith(('>', '<')):
                numeric_value = float(result_value[1:])
            else:
                numeric_value = float(result_value)
        except ValueError:
            continue  # Skip if we can't parse the value
            
        # Parse reference range if available
        bio_reference_range = ""
        out_of_range = None
        
        if ref_range:
            try:
                # Handle different separators and clean up
                ref_parts = re.split(r'\s*[-–]\s*', ref_range)
                if len(ref_parts) == 2:
                    ref_low = float(ref_parts[0])
                    ref_high = float(ref_parts[1])
                    bio_reference_range = f"{ref_low}-{ref_high}{' ' + ref_unit if ref_unit else ''}"
                    
                    # Determine if value is out of range
                    if result_value.startswith('>'):
                        out_of_range = numeric_value <= ref_high  # >60 means OK if value >60
                    elif result_value.startswith('<'):
                        out_of_range = numeric_value >= ref_low   # <10 means OK if value <10
                    else:
                        out_of_range = not (ref_low <= numeric_value <= ref_high)
            except (ValueError, IndexError):
                pass
        
        results.append({
            "test_name": test_name,
            "result_value": numeric_value,
            "unit": unit,
            "bio_reference_range": bio_reference_range,
            "lab_test_out_of_range": out_of_range
        })
    
    return results

# Test with the provided OCR output
extracted_text = r"""SARVODAVA HOSPITAL Dr, cotta Atul ve rai MD. Path
Ke7, Kavi Nagar, Ghaviabad WU'P Reus No, MCL Son8
Patient ID, : fe ns
‘}\Patient nt ae
‘Referred VERMA ;
Lab Seria! No: 19 , Receiving __J18/Apr/2025 12:15:00PM
| Ward No 1 SP-25 Reporting Date : 18/Apr/2025 3:17:39PM |
‘| CR/UHD No a 0223/ 381503 os : Date TAT : 3 Hours 2 Minute
lnvestiqation mo . a o _ Observed Value Unit — Biological Ref-interval --: ?
SEROLOGY
oc
AMMONIA ug/dl - 17.00 - $0.00
Specimen : BLOOD
- END OF REPORT *
‘FACILITIES > FOR HORMONES ASSAYS, FNAG |
NOTE : ABUVE MENTIONED FINDINGS ARE 4 PRO
‘INVESTIGATION RESULTS ARE TG BE CORELATED SuINIC- P"""

# Extract lab results
parsed_results = parse_lab_results(extracted_text)

for result in parsed_results:
    print(result)
