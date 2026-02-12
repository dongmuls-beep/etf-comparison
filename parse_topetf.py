import re
import json
import os


def parse_html():
    source_file = "page_source_debug.html"
    if not os.path.exists(source_file):
        print("Source file not found.")
        return

    with open(source_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate "etfList"
    # It might be part of specific JS syntax.
    # Just finding the first occurrence of "etfList" might work since it's unique key here.
    
    keyword = "etfList"
    idx = content.find(keyword)
    
    if idx == -1:
        print("Keyword 'etfList' not found in file.")
        return
        
    print(f"Found 'etfList' at index {idx}")
    
    # Look for the start of the array '[' after the keyword
    start_bracket = content.find('[', idx)
    if start_bracket == -1:
        print("Could not find start bracket '[' after etfList")
        return
        
    # Extract the array content by counting brackets
    count = 0
    end_bracket = -1
    
    # Optimizing: slice from start_bracket
    # We need to handle string literals containing brackets if any.
    # But usually simple counting works for JSON structure unless complex strings.
    # Given we are parsing a raw file which might have escaped quotes, we need to be careful.
    
    # Alternative: The structure is inside a JS string "..."
    # So `\"` is `"` in the actual JSON.
    # Let's try to extract a large chunk and clean it.
    
    chunk = content[start_bracket:]
    
    # Naive bracket counting
    in_string = False
    escape = False
    
    for i, char in enumerate(chunk):
        if escape:
            escape = False
            continue
            
        if char == '\\':
            escape = True
            continue
            
        if char == '"' and not escape:
            in_string = not in_string
            
        if not in_string:
            if char == '[':
                count += 1
            elif char == ']':
                count -= 1
                if count == 0:
                    end_bracket = start_bracket + i + 1
                    break
    
    if end_bracket != -1:
        raw_json = content[start_bracket:end_bracket]
        
        # Now we need to unescape it because it was inside a JS string?
        # Check if it has backslashes before quotes.
        # Example from file: {\"id\":\"KR...
        # Yes, it looks double escaped or just escaped.
        # Let's try replacing `\"` with `"` 
        
        clean_json = raw_json.replace('\\"', '"')
        clean_json = clean_json.replace('\\\\', '\\') # Handle escaped backslashes if any

        try:
            data = json.loads(clean_json)
            print(f"Successfully parsed {len(data)} items.")
            
            with open("list.txt", "w", encoding="utf-8") as out:
                # Header
                out.write("종목코드\t종목명\t표준코드\t펀드명\n")
                
                for item in data:
                    name = item.get('name', 'N/A')
                    std_code = item.get('id', 'N/A')
                    fund_name = item.get('fullName', 'N/A')
                    
                    # Derive 6-digit code from ISIN (KR7xxxxxx...)
                    # Standard ISIN for KR stocks: KR7 + 6-digit code + check sum + ...
                    # Example: KR7360200000 -> 360200
                    stock_code = "N/A"
                    if len(std_code) >= 9 and std_code.startswith("KR7"):
                         stock_code = std_code[3:9]
                    
                    line = f"{stock_code}\t{name}\t{std_code}\t{fund_name}"
                    print(line)
                    out.write(line + "\n")
                    
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Snippet: {clean_json[:100]}...")
            
    else:
        print("Could not find end of array.")

if __name__ == "__main__":
    parse_html()
