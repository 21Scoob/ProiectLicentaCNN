import os 


folder = r"/Volumes/SSD1/Elon_Musk_Scraped" 

# Așa citești doar fișierele reale, ignorând mizeria sistemului
fisiere_reale = [f for f in os.listdir(folder) if not f.startswith('.')]
print(f"Număr real de imagini: {len(fisiere_reale)}")