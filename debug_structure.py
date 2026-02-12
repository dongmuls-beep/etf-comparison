from selenium import webdriver
from selenium.webdriver.common.by import By
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

def debug_html():
    driver = setup_driver()
    try:
        url = "https://dis.kofia.or.kr/websquare/index.jsp?w2xPath=/wq/fundann/DISFundFeeCMS.xml&divisionId=MDIS01005001000000&serviceId=SDIS01005001000"
        driver.get(url)
        time.sleep(10)
        
        target = driver.find_element(By.ID, "condition_textbox39")
        parent = target.find_element(By.XPATH, "..")
        grandparent = parent.find_element(By.XPATH, "..")
        
        print(f"Target HTML: {target.get_attribute('outerHTML')}")
        print(f"Parent HTML: {parent.get_attribute('outerHTML')}")
        print(f"Grandparent HTML: {grandparent.get_attribute('outerHTML')}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_html()
