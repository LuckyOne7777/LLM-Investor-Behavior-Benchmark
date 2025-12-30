import json
import re 

def parse_json(text: str, tag: str):
    # Extract the block from given section
    pattern = rf"<{re.escape(tag)}>\s*(\{{.*?\}})\s*</{re.escape(tag)}>"
    match = re.search(pattern, text, flags=re.DOTALL)
    
    if not match:
        raise ValueError(f"No {tag} block found.")

    json_str = match.group(1)

    json_str = re.sub(r",\s*}", "}", json_str)

    return json.loads(json_str)