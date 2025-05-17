import re

def parse_conversion_input(text):
    # Common patterns for conversion
    patterns = [
        r'convert\s+(\d+(?:\.\d+)?)\s+(\w+(?:\s+\w+)?)\s+to\s+(\w+(?:\s+\w+)?)',  # convert 5 pounds to rupees
        r'(\d+(?:\.\d+)?)\s+(\w+(?:\s+\w+)?)\s+to\s+(\w+(?:\s+\w+)?)',           # 5 pounds to rupees
        r'convert\s+(\d+(?:\.\d+)?)\s+(\w+(?:\s+\w+)?)\s+in\s+(\w+(?:\s+\w+)?)',  # convert 5 pounds in rupees
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            value = float(match.group(1))
            from_unit = match.group(2).strip()
            to_unit = match.group(3).strip()
            print(f"Parsed conversion: {value} {from_unit} to {to_unit}")
            return value, from_unit, to_unit
    return None