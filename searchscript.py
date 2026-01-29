import os
import time
import requests
from urllib.parse import urljoin, urlparse


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://www.gettyimages.com/search/2/image?family=editorial&numberofpeople=one&phrase=taylor%20swift&sort=mostpopular&specificpeople=619504"
URL_PATTERN = "&page={}"
OUTPUT_DIR = "/Volumes/SSD1/TaylorSwift_Scraped" 
TARGET_LIMIT = 2500  


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def setup_driver():
    """Configurează browserul Chrome controlat de cod."""
    options = Options()
    
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_argument("--start-maximized")

    driver = webdriver.Safari()
    return driver

def scroll_to_bottom(driver):
    """Dă scroll treptat până jos ca să încarce toate pozele (Lazy Loading)."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2) 
        
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            
            break
        last_height = new_height

def download_image(img_url, folder):
    """Funcția ta originală de download, adaptată să returneze True/False."""
    try:
        
        if not img_url.startswith('http'):
            return False

        parsed = urlparse(img_url)
        filename = os.path.basename(parsed.path)
        
        
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return False

        save_path = os.path.join(folder, filename)
        
        if os.path.exists(save_path):
            return False 

        
        with requests.get(img_url, headers=HEADERS, stream=True, timeout=10) as r:
            if r.status_code == 200:
                if len(r.content) < 5000:  
                    return False 
                    
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ Salvat: {filename}")
                return True
            else:
                return False

    except Exception as e:
        print(f"Eroare download: {e}")
        return False

def start_scraping():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    driver = setup_driver()
    page = 1
    total_downloaded = 0

    try:
        while True:
            current_url = f"{BASE_URL}{URL_PATTERN.format(page)}"
            print(f"\n--- 🌍 Navighez la Pagina {page} --- (Total: {total_downloaded})")
            
            driver.get(current_url)
            time.sleep(3) 

            
            print("📜 Execut scroll pentru lazy loading...")
            scroll_to_bottom(driver)
            
            
            images = driver.find_elements(By.TAG_NAME, "img")
            print(f"👀 Am detectat {len(images)} elemente img pe pagină.")

            if len(images) < 5:
                print("⚠️ Prea puține imagini. Probabil final de căutare sau eroare.")
                break

            found_on_page = 0
            
            
            for img in images:
                try:
                    src = img.get_attribute('src')
                    
                    
                    if src and "gettyimages" in src:
                        if download_image(src, OUTPUT_DIR):
                            total_downloaded += 1
                            found_on_page += 1
                            print(f"📊 Progres Total: {total_downloaded}/{TARGET_LIMIT}")

                        
                        if total_downloaded >= TARGET_LIMIT:
                            print(f"\n🎉 GATA! Am atins limita de {TARGET_LIMIT} imagini.")
                            return 
                except:
                    continue 

            if found_on_page == 0:
                print("Nu am reușit să descarc nimic valid de pe pagina asta.")
            
            page += 1

    except KeyboardInterrupt:
        print("\nOprit manual de utilizator.")
    except Exception as e:
        print(f"Eroare critică în bucla principală: {e}")
    finally:
        print("Închid browserul...")
        driver.quit()

if __name__ == "__main__":
    start_scraping()