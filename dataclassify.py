import os
import shutil
import random

folder = r"/Volumes/SSD1/Real"

final_folder = r"/Volumes/SSD1/Dataset_Final"

subfolders = [f.path for f in os.scandir(folder) if f.is_dir()]

for person in subfolders:
    
    person_name = os.path.basename(person)
    
    files = [f for f in os.listdir(person) if not f.startswith('.')]
    
    total_files = len(files)
    
    random.shuffle(files)
    
    train = int(total_files * 0.8)
    val = train + int(total_files* 0.1)
    
    print((train, val))
    
    train_files = files[:train]
    valid_files = files[train:val]
    test_files = files[val:]
    
    splits = {
        "train": train_files,
        "valid": valid_files,
        "test": test_files        
}
    
    for split_name, file_list in splits.items():
        
        dataset_dir = os.path.join(final_folder, split_name, "real", person_name)
        
        os.makedirs(dataset_dir, exist_ok=True)
    
        for file_name in file_list:
            
            src_file = os.path.join(person, file_name)
            dataset_file = os.path.join(dataset_dir, file_name)
            
            shutil.copy2(src_file, dataset_file)

