from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os
import glob
import pandas as pd

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    prefs = {
        "download.default_directory": os.getcwd(),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def run_scraper():
    driver = setup_driver()
    try:
        url = "https://dis.kofia.or.kr/websquare/index.jsp?w2xPath=/wq/fundann/DISFundFeeCMS.xml&divisionId=MDIS01005001000000&serviceId=SDIS01005001000"
        print(f"Visiting {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 30)
        
        # 1. Wait for Main Search Button (Page Load)
        print("Waiting for page load...")
        search_btn = wait.until(EC.element_to_be_clickable((By.ID, "btnSear")))
        time.sleep(5) # Let things settle
        
        # 2. Enter '상장지수' in Fund Name (펀드명)
        # This bypasses the complex checkbox selectors and filters by name directly.
        # "상장지수" is the standard term for ETF in Korean fund names.
        print("Entering '상장지수' in Fund Name Search...")
        try:
             fund_nm_input = wait.until(EC.visibility_of_element_located((By.ID, "fundNm")))
             fund_nm_input.clear()
             fund_nm_input.send_keys("상장지수")
             print("Entered '상장지수'")
             time.sleep(1)
        except Exception as e:
             print(f"Error entering fund name: {e}")
             return False

        # 3. Click Search
        print("Clicking Search...")
        driver.execute_script("arguments[0].click();", search_btn)
        
        # 5. Wait for Grid Load (Loading Bar)
        print("Waiting for data to load (20s)...")
        time.sleep(20) # Conservative wait
        
        # 6. Download Excel
        print("Clicking Excel Download...")
        try:
            excel_btn = driver.find_element(By.XPATH, "//img[contains(@alt, '엑셀') or contains(@alt, 'Excel')]/parent::*")
            excel_btn.click()
        except:
            # Fallback selectors
            excel_btn = driver.find_element(By.CSS_SELECTOR, "#btnExcel, #excelDown")
            excel_btn.click()
            
        # 7. Wait for Download
        print("Waiting for download...")
        time.sleep(10)
        
        # 8. Identify Latest File
        files = glob.glob("*.xls") # KOFIA uses .xls
        if not files:
            print("No .xls files found!")
            return False
            
        latest_file = max(files, key=os.path.getctime)
        print(f"Downloaded: {latest_file}")
        
        # Rename to fixed name
        output_file = "kofia_etf_data_latest.xls"
        if os.path.exists(output_file):
            os.remove(output_file)
        os.rename(latest_file, output_file)
        print(f"Renamed to {output_file}")
        
        # 9. Verify Content (Row Count)
        print("Verifying content...")
        df = pd.read_excel(output_file, header=1) # Header is usually row 1 for these
        
        row_count = len(df)
        print(f"Total Rows: {row_count}")
        
        if row_count > 500:
            print("SUCCESS: Downloaded substantial data (likely all ETFs).")
            # We accept K55 codes because KOFIA provides Fund Codes, not Listing Codes (KR7).
            # Mapping will be handled in ETL.
            return True
        else:
            print("FAILURE: Row count too low.")
            return False
             
    except Exception as e:
        print(f"Critical Error: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    success = run_scraper()
    if success:
        print("Scraper Finished Successfully.")
    else:
        print("Scraper Failed.")
        exit(1)
