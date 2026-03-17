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

print("Incarc FLUX.2-dev...")
pipe = FluxPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16
)
pipe.enable_model_cpu_offload()

class PersonSelection:
    def __init__(self, name, locations, actions, styles):
        self.name = name
        self.locations = locations
        self.actions = actions
        
    def get_prompt():
        
        location_random = random.choice(self.locations)
        action_random = random.choice(self.actions)
        
        style = ["Hyperrealistic photo, high detail, raw photography, detailed skin texture, pores visible"]
        
        final_prompt = (
            f"{self.name}, {self.locations}, {self.actions}, {style}"
        )
        
        return final_prompt
    
trump = PersonSelection(
    name="Donald Trump",
    locatii=["at the White House", "on a podium", "on stage", "at the Resolute Desk", "White House Garden"],
    actiuni=["looks at camera", "speaks at a microphone", "waves to crowd", "smiles gently", "looks serious", "shakes hands with someone"]
)



macron = PersonSelection(
    name="Emmanuel Macron",
    locatii=["at the Élysée Palace", "in the European Parliament", "on the streets of Paris", "at an international summit table"],
    actiuni=["speaking passionately with hands", "adjusting his suit tie", "shaking hands with world leaders", "reading an official document"]
)

xi_jinping = PersonSelection(
    name="Xi Jinping",
    locatii=["at the Great Hall of the People", "overlooking Tiananmen Square", "at an official state dinner", "standing at a military parade podium"],
    actiuni=["clapping slowly", "standing strictly at attention", "giving a speech from a wooden podium", "looking stoic and unblinking"]
)

putin = PersonSelection(
    name="Vladimir Putin",
    locatii=["in the Kremlin grand hall", "sitting at a ridiculously long white table", "at a press conference desk", "in a military control room"],
    actiuni=["sitting alone looking serious", "speaking into a desktop microphone", "holding a pen", "listening intently with a stern face"]
)

zelensky = PersonSelection(
    name="Volodymyr Zelenskyy",
    locatii=["in a destroyed city street with rubble", "in an underground military bunker", "at a press briefing room", "addressing a parliament hall"],
    actiuni=["wearing an olive green t-shirt", "looking exhausted but resolute", "speaking directly to the camera", "shaking hands with soldiers"]
)

netanyahu = PersonSelection(
    name="Benjamin Netanyahu",
    locatii=["at the Knesset podium", "in the Prime Minister's office", "at a military base briefing", "at a national press conference"],
    actiuni=["pointing a finger emphatically", "holding up a chart or map", "speaking at a podium with flags", "looking stern and focused"]
)



elon_musk = PersonSelection(
    name="Elon Musk",
    locatii=["inside a SpaceX assembly facility", "on a podcast studio setup", "at a Tesla factory floor", "on a TED talk stage"],
    actiuni=["gesturing while explaining", "laughing with a microphone in hand", "looking up at a rocket", "wearing a plain black t-shirt"]
)

jeffrey_epstein = PersonSelection(
    name="Jeffrey Epstein",
    locatii=["in a wood-paneled courtroom", "at a legal deposition table", "walking outside a courthouse", "on an airport tarmac"],
    actiuni=["consulting with a lawyer", "looking down avoiding the camera", "sitting silently at a defense table", "wearing a formal suit"]
)



lebron_james = PersonSelection(
    name="LeBron James",
    locatii=["on an NBA basketball court", "in a post-game locker room", "at a sports press conference", "walking a red carpet"],
    actiuni=["dribbling a basketball", "wiping sweat with a towel", "giving an interview to reporters", "wearing a Lakers uniform"]
)

kanye_west = PersonSelection(
    name="Kanye West",
    locatii=["on a fashion runway", "in a recording studio", "on a dimly lit concert stage", "walking the streets of Paris"],
    actiuni=["wearing a full face mask", "holding a microphone looking down", "wearing oversized futuristic sunglasses", "looking away from the paparazzi"]
)

taylor_swift = PersonSelection(
    name="Taylor Swift",
    locatii=["on a massive stadium stage", "in a soundproof recording booth", "at a music awards red carpet", "sitting with an acoustic guitar"],
    actiuni=["singing passionately into a sparkly microphone", "waving smiling to a massive crowd", "holding a Grammy award", "playing a guitar"]
)

tom_cruise = PersonSelection(
    name="Tom Cruise",
    locatii=["on a movie premiere red carpet", "on an action movie set", "sitting on a motorcycle", "standing next to a fighter jet"],
    actiuni=["running at full speed", "smiling a wide charismatic smile", "waving to fans with aviator sunglasses", "doing a practical stunt"]
)

will_smith = PersonSelection(
    name="Will Smith",
    locatii=["at the Oscars stage", "on a talk show couch", "at a movie premiere", "on a Hollywood film set"],
    actiuni=["laughing loudly", "posing confidently for cameras", "holding a golden award", "wearing a sharp tailored suit"]
)

morgan_freeman = PersonSelection(
    name="Morgan Freeman",
    locatii=["on a documentary film set", "in a voiceover recording studio", "at a prestigious film festival", "on a late-night talk show"],
    actiuni=["narrating into a studio mic", "smiling wisely at the camera", "wearing a classic tuxedo", "looking directly into the lens"]
)

sydney_sweeney = PersonSelection(
    name="Sydney Sweeney",
    locatii=["on a Hollywood red carpet", "at a high-fashion photoshoot", "on a daytime talk show set", "at a movie premiere backdrop"],
    actiuni=["posing gracefully for photographers", "smiling brightly at the camera", "wearing a designer dress", "sitting for an interview"]
)



charlie_kirk = PersonSelection(
    name="Charlie Kirk",
    locatii=["on a college campus debate stage", "in a podcast recording studio", "at a Turning Point USA conference", "behind a news desk"],
    actiuni=["speaking intensely into a broadcast microphone", "debating a student", "holding a notebook and pointing", "wearing a suit and tie"]
)

albert_einstein = PersonSelection(
    name="Albert Einstein",
    locatii=["at a university chalkboard", "in a vintage physics laboratory", "sitting at a messy wooden desk", "in a 1920s lecture hall"],
    actiuni=["writing complex math equations with chalk", "looking thoughtfully at the camera with his wild hair", "holding a pipe", "sticking his tongue out playfully"]
)

mr_beast = PersonSelection(
    name="MrBeast",
    locatii=["inside a massive colorful warehouse set", "standing next to a mountain of cash", "in a crazy challenge arena", "outdoors holding a giant cardboard check"],
    actiuni=["pointing enthusiastically at the camera", "wearing a MrBeast merch hoodie", "screaming excitedly with arms wide open", "handing stacks of money to a subscriber"]
)

kim_jong_un = PersonSelection(
    name="Kim Jong Un",
    locatii=["at a military observation post looking through binoculars", "at a grand military parade in Pyongyang", "inside a retro missile control room", "walking through a snowy factory facility"],
    actiuni=["wearing a black Mao-style suit", "clapping surrounded by generals taking notes", "smiling broadly while pointing at heavy machinery", "smoking a cigarette during a field inspection"]
)

kim_kardashian = PersonSelection(
    name="Kim Kardashian",
    locatii=["at the Met Gala red carpet", "inside a minimalist beige mansion", "at a SKIMS brand launch event", "sitting in a luxury private jet"],
    actiuni=["taking a mirror selfie with a smartphone", "wearing a skin-tight designer gown", "striking a glamorous pose for paparazzi", "adjusting her sunglasses while holding a designer bag"]
)

barack_obama = PersonSelection(
    name="Barack Obama",
    locatii=["at the White House Rose Garden", "on a large campaign stage with a blue background", "in the Oval Office", "at a town hall meeting"],
    actiuni=["smiling warmly and waving to the crowd", "speaking passionately with rolled-up shirt sleeves", "making his signature thumb-to-finger hand gesture", "wearing a sharp tailored suit and blue tie"]
)

list_persons = [trump, macron, xi_jinping, putin, zelensky, netanyahu,
    elon_musk, jeffrey_epstein, lebron_james, kanye_west, 
    taylor_swift, tom_cruise, will_smith, morgan_freeman, 
    sydney_sweeney, charlie_kirk, albert_einstein, mr_beast, kim_jong_un, kim_kardashian, barack_obama
]

for person in list_persons:
    
    print(f"Image generation for {person}...")
    
    for i in range(0, TOTAL_IMAGES, BATCH_SIZE):
    
    
        torch.cuda.empty_cache()
        gc.collect()

    
        current_prompts = []
        for _ in range(BATCH_SIZE):
            ppl = random.choice(people)
            loc = random.choice(locations)
            act = random.choice(actions)
            style = random.choice(styles)
            current_prompts.append(person.get_prompt())
    
        print(f"Generare batch {i} - {i+BATCH_SIZE}...")

    
    
        images = pipe(
            current_prompts,  
            height=1024,
            width=1024,
            guidance_scale=3.5, 
            num_inference_steps=35, 
            max_sequence_length=512,
            generator=torch.Generator("cuda").manual_seed(random.randint(0, 1000000))
        ).images
    
    
        for idx, img in enumerate(images):
            file_index = i + idx
            if file_index >= TOTAL_IMAGES: break 
        
            filename = output_dir / f"flux_gen_{file_index}.jpg"
            img.save(filename)
            print(f"  -> Salvat: {filename}")
