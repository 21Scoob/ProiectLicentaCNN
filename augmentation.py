import os
import random
from PIL import Image, ImageEnhance
from tqdm import tqdm 


FOLDER_PATH = r"/Volumes/SSD1/Charlie_Kirk_Scraped" 
TARGET_COUNT = 2500 
VALID_EXTENSIONS = ('.jpg', '.jpeg', '.png')


def apply_random_augmentation(img):
    """Aplică o serie de modificări aleatorii imaginii."""
    
    
    if random.random() > 0.5:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        
    
    
    angle = random.uniform(-15, 15)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False)
    
    
    enhancer_brightness = ImageEnhance.Brightness(img)
    img = enhancer_brightness.enhance(random.uniform(0.4, 2))
    
    
    enhancer_contrast = ImageEnhance.Contrast(img)
    img = enhancer_contrast.enhance(random.uniform(0.4, 2))
    
    return img

def main():
    if not os.path.exists(FOLDER_PATH):
        print(f"❌ Folderul nu există: {FOLDER_PATH}")
        return

    
    original_files = [f for f in os.listdir(FOLDER_PATH) if not f.startswith('.')]
    current_count = len(original_files)
    
    print(f"📊 Ai {current_count} imagini în folder.")
    
    if current_count >= TARGET_COUNT:
        print("✅ Ai deja numărul dorit (sau mai multe) de imagini. Nu e nevoie de augmentare.")
        return
        
    needed_images = TARGET_COUNT - current_count
    print(f"🚀 Generez {needed_images} imagini noi prin augmentare...")

    
    for i in tqdm(range(needed_images), desc="Augmentare", unit="img"):
        
        random_filename = random.choice(original_files)
        input_path = os.path.join(FOLDER_PATH, random_filename)
        
        try:
            with Image.open(input_path) as img:
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                
                aug_img = apply_random_augmentation(img)
                
                
                new_filename = f"aug_{i}_{random_filename}"
                output_path = os.path.join(FOLDER_PATH, new_filename)
                
                aug_img.save(output_path, quality=95)
                
        except Exception as e:
            
            continue

    print(f"\n🎉 Gata! Folderul tău are acum aproximativ {TARGET_COUNT} imagini.")

if __name__ == "__main__":
    main()