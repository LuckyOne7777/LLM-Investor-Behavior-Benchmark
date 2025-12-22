import json
import re 

def parse_json(text: str, tag: str):
    # Extract the block from given section
    pattern = rf"<{re.escape(tag)}>\s*(\{{.*?\}})\s*</{re.escape(tag)}>"
    match = re.search(pattern, text, flags=re.DOTALL)
    
    if not match:
        raise ValueError("No ORDERS_JSON block found.")

    json_str = match.group(1)

    # Optional: fix trailing commas
    json_str = re.sub(r",\s*}", "}", json_str)

    return json.loads(json_str)