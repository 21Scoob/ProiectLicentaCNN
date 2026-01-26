import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse



BASE_URL = "https://www.gettyimages.com/search/2/image?groupbyevent=false&family=editorial&phrase=trump&sort=mostpopular"  
URL_PATTERN = "&page={}"  
OUTPUT_DIR = "/Volumes/SSD1/Trump_Scraped" 
CSS_SELECTOR = "img" 


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def download_image(img_url, folder):
    try:
        
        img_url = urljoin(BASE_URL, img_url)
        
        
        parsed = urlparse(img_url)
        filename = os.path.basename(parsed.path)
        
        
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return

        save_path = os.path.join(folder, filename)
        
        
        if os.path.exists(save_path):
            return

        
        with requests.get(img_url, headers=HEADERS, stream=True, timeout=10) as r:
            if r.status_code == 200:
                
                if len(r.content) < 5000: 
                    return 
                    
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ Salvat: {filename}")
            else:
                print(f"❌ Eroare link: {r.status_code}")

    except Exception as e:
        print(f"Eroare la download: {e}")

def start_scraping():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    page = 1
    while True:
        
        
        current_url = f"{BASE_URL}{URL_PATTERN.format(page)}"
        print(f"\n--- Procesez Pagina {page} --- [{current_url}]")

        try:
            response = requests.get(current_url, headers=HEADERS)
            if response.status_code != 200:
                print("⛔ Am ajuns la final sau site-ul a dat eroare.")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            
            
            images = soup.select(CSS_SELECTOR)
            
            if not images:
                print("⚠️ Nu am găsit nicio poză pe pagina asta. Probabil final.")
                break

            print(f"Găsit {len(images)} potențiale imagini...")

            for img in images:
                
                src = img.get('src')
                if src: 
                    download_image(src, OUTPUT_DIR)
            
            time.sleep(2) 
            
            page += 1
            
            if page > 75: 
                break

        except Exception as e:
            print(f"Eroare critică: {e}")
            break

if __name__ == "__main__":
    start_scraping()