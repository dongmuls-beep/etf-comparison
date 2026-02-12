from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def dump_labels():
    driver = setup_driver()
    try:
        print("Visiting KOFIA...")
        driver.get("https://dis.kofia.or.kr/websquare/index.jsp?w2xPath=/wq/fundann/DISFundFeeCMS.xml&divisionId=MDIS01005001000000&serviceId=SDIS01005001000")
        
        wait = WebDriverWait(driver, 30)
        
        # Wait for Search button as a proxy for page load
        wait.until(EC.presence_of_element_located((By.ID, "btnSear")))
        print("Page loaded. Waiting 10s for dynamic content...")
        time.sleep(10)
        
        print("Dumping Page Text...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        with open("page_text.txt", "w", encoding="utf-8") as f:
            f.write(body_text)
            
        print("Dumping #srchFundType HTML...")
        try:
            fund_type_ul = driver.find_element(By.ID, "srchFundType")
            with open("fund_type_html.txt", "w", encoding="utf-8") as f:
                f.write(fund_type_ul.get_attribute("outerHTML"))
        except Exception as e:
            print(f"Could not find #srchFundType: {e}")

        if "상장지수" in body_text:
            print("FOUND '상장지수' in page text!")
        else:
            print("NOT FOUND '상장지수' in page text.")
            
        print("Done. Check page_text.txt and fund_type_html.txt")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    dump_labels()
