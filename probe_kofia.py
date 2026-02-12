from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def probe():
    driver = setup_driver()
    try:
        url = "https://dis.kofia.or.kr/websquare/index.jsp?w2xPath=/wq/fundann/DISFundFeeCMS.xml&divisionId=MDIS01005001000000&serviceId=SDIS01005001000"
        print(f"Visiting {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "btnSear")))
        time.sleep(5)
        
        # 1. Screenshot Initial State
        print("Capturing initial state...")
        driver.save_screenshot("kofia_initial.png")
        
        # 2. Probe 'Fund Type' (펀드유형) - Click the input/checkbox area
        print("Probing 'Fund Type'...")
        # Try to find the container for "Fund Type" and print its content
        try:
            # Based on page_labels, condition_textbox39 is the label for 펀드유형
            # We want to find the checkboxes associated with it.
            # Usually they are in a table row or div nearby.
            # Let's try to click the first checkbox in that group if possible
            pass # Just screenshot for now
        except:
             pass

        # 3. Check for specific text like "상장" in the whole page source
        src = driver.page_source
        if "상장" in src:
            print("Found '상장' in source!")
        else:
            print("NOT Found '상장' in source.")

        # 4. Dump all 'label' texts again with coordinates to see layout? No, just screenshot.
        
        # 5. Try to Click 'Fund Classification' (펀드종류) - 'Investment Trust' (투자신탁)
        # Maybe ETF appears then?
        try:
            print("Clicking 'Investment Trust' (투자신탁)...")
            # Label for '투자신탁' is For: 'fundGb_input_1'
            trust_label = driver.find_element(By.XPATH, "//label[contains(text(), '투자신탁')]")
            trust_label.click()
            time.sleep(3)
            driver.save_screenshot("kofia_after_click_trust.png")
            
            # Check for ETF text again
            if "상장지수" in driver.page_source:
                print("Found '상장지수' after clicking Investment Trust!")
            else:
                 print("Still no '상장지수' after clicking Investment Trust.")
                 
        except Exception as e:
            print(f"Click failed: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    probe()
