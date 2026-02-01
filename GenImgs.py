import torch
from diffusers import FluxPipeline
from pathlib import Path
import random
import gc
from huggingface_hub import login
import os 
from dotenv import load_dotenv, dotenv_values

load_dotenv()

output_dir = Path("/path/etc.")
output_dir.mkdir(parents=True, exist_ok=True)
TOTAL_IMAGES = 2500
BATCH_SIZE = 10 

login(token=os.getenv("tokenhg")) 


model_id = "black-forest-labs/FLUX.2-dev"

print("🚀 Incarc FLUX.2-dev...")
pipe = FluxPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16
)
pipe.enable_model_cpu_offload()


people = ["Donald Trump"]
locations = ["at the White House", "on a podium", "on stage", "at the Resolute Desk", "White House Garden"]
actions = ["looks at camera", "speaks at a microphone", "waves to crowd", "smiles gently", "looks serious", "shakes hands with someone"]
styles = ["Hyperrealistic photo, high detail, raw photography"]

print(f"Începem generarea în batch-uri de câte {BATCH_SIZE}...")


for i in range(0, TOTAL_IMAGES, BATCH_SIZE):
    
    
    torch.cuda.empty_cache()
    gc.collect()

    
    current_prompts = []
    for _ in range(BATCH_SIZE):
        ppl = random.choice(people)
        loc = random.choice(locations)
        act = random.choice(actions)
        style = random.choice(styles)
        prompt_text = f"{style}, {ppl}, {act}, {loc}"
        current_prompts.append(prompt_text)
    
    print(f"Generare batch {i} - {i+BATCH_SIZE}...")

    
    
    images = pipe(
        current_prompts,  
        height=1024,
        width=1024,
        guidance_scale=3.5, 
        num_inference_steps=50, 
        max_sequence_length=512,
        generator=torch.Generator("cuda").manual_seed(random.randint(0, 1000000))
    ).images
    
    
    for idx, img in enumerate(images):
        file_index = i + idx
        if file_index >= TOTAL_IMAGES: break 
        
        filename = output_dir / f"flux_gen_{file_index}.jpg"
        img.save(filename)
        print(f"  -> Salvat: {filename}")

print("Gata sefu! Dataset creat.")