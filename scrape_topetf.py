from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import json
import os

def setup_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_data_from_source(content):
    keyword = "etfList"
    idx = content.find(keyword)
    if idx == -1: return []
    
    start_bracket = content.find('[', idx)
    if start_bracket == -1: return []
    
    count = 0
    end_bracket = -1
    chunk = content[start_bracket:]
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
        clean_json = raw_json.replace('\\"', '"').replace('\\\\', '\\')
        try:
            return json.loads(clean_json)
        except:
            return []
    return []

def scrape_all():
    urls = [
        "https://topetf.app/SPX",
        "https://topetf.app/NDX",
        "https://topetf.app/DJUSDIV",
        "https://topetf.app/KOSPI200",
        "https://topetf.app/US30YT",
        "https://topetf.app/UST10T",
        "https://topetf.app/HSTECH",
        "https://topetf.app/NIFTY50"
    ]
    
    driver = setup_driver()
    all_data = []
    
    try:
        # File mode: 'w' to overwrite initially, or we can just collect all and write once.
        # Let's write header first.
        with open("list.txt", "w", encoding="utf-8") as f:
            f.write("종목코드\t종목명\t표준코드\t펀드명\n")

        for url in urls:
            print(f"Scraping {url}...")
            driver.get(url)
            
            # Wait for body or specific element
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(3) # Wait for hydration
            except:
                print(f"Timeout loading {url}")
                continue
                
            source = driver.page_source
            items = extract_data_from_source(source)
            print(f" -> Found {len(items)} items.")
            
            with open("list.txt", "a", encoding="utf-8") as f:
                for item in items:
                    name = item.get('name', 'N/A')
                    std_code = item.get('id', 'N/A')
                    fund_name = item.get('fullName', 'N/A')
                    
                    stock_code = "N/A"
                    if len(std_code) >= 9 and std_code.startswith("KR7"):
                         stock_code = std_code[3:9]
                    
                    # Avoid duplicates if any (though lists should be distinct ideally)
                    # But multiple lists might have overlaps? 
                    # Assuming typical usage, just append.
                    
                    line = f"{stock_code}\t{name}\t{std_code}\t{fund_name}"
                    f.write(line + "\n")
                    
    finally:
        driver.quit()
        print("Done.")

if __name__ == "__main__":
    scrape_all()
