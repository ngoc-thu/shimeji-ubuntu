#!/usr/bin/env python3
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DIRECTORY_URL = "https://shimejis.xyz/directory"
BASE_SPRITE_URL = "https://sprite.shimejis.xyz/directory/{slug}/img/shime{frame}.png"

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARACTERS_DIR = os.path.join(APP_ROOT, "characters")
OPENCLAW_CHARACTERS_DIR = "/home/ngoctien/.openclaw/workspace/apps/linux-shimeji/characters"

def clean_slug_to_foldername(slug):
    # Split slug by dash
    parts = slug.split("-")
    
    # Check common category prefixes
    category_map = {
        "genshin": "Genshin",
        "pokemon": "Pokemon",
        "naruto": "Naruto",
        "undertale": "Undertale",
        "vocaloid": "Vocaloid",
        "homestuck": "Homestuck",
        "hetalia": "Hetalia",
        "kingdom": "KingdomHearts",
        "mario": "Mario",
        "one": "OnePiece",
        "osomatsu": "Osomatsu",
        "steven": "StevenUniverse",
        "the": "Avengers",
        "yu": "YuGiOh",
        "jojos": "JJBA",
        "my": "MHA",
        "night": "NITW",
    }
    
    # Capitalize parts cleanly
    clean_parts = []
    skip_next = False
    for i, p in enumerate(parts):
        if p.lower() in ["by", "01", "02", "03", "04"]:
            break
        clean_parts.append(p.capitalize())
        
    name = "_".join(clean_parts)
    if not name:
        name = slug.replace("-", "_").capitalize()
    return name

def fetch_all_slugs():
    req = urllib.request.Request(DIRECTORY_URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    content = urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")
    
    # Extract sprite URLs
    sprite_slugs = re.findall(r"https?://sprite\.shimejis\.xyz/directory/([^/]+)/img/shime1\.png", content)
    slugs = sorted(list(set(sprite_slugs)))
    return slugs

def download_single_frame(slug, frame, target_dirs):
    url = BASE_SPRITE_URL.format(slug=slug, frame=frame)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    try:
        data = urllib.request.urlopen(req, timeout=10).read()
        for d in target_dirs:
            filepath = os.path.join(d, f"shime{frame}.png")
            with open(filepath, "wb") as f:
                f.write(data)
        return True
    except Exception as e:
        return False

def download_character(slug):
    folder_name = clean_slug_to_foldername(slug)
    t1 = os.path.join(CHARACTERS_DIR, folder_name)
    t2 = os.path.join(OPENCLAW_CHARACTERS_DIR, folder_name)
    os.makedirs(t1, exist_ok=True)
    os.makedirs(t2, exist_ok=True)
    
    success = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(download_single_frame, slug, f, [t1, t2]) for f in range(1, 47)]
        for fut in as_completed(futures):
            if fut.result():
                success += 1
                
    if success == 46:
        print(f"[OK] {slug} -> {folder_name} (46/46 frames)")
    else:
        print(f"[PARTIAL] {slug} -> {folder_name} ({success}/46 frames)")
    return folder_name, success

def main():
    print("Fetching catalog from shimejis.xyz...")
    slugs = fetch_all_slugs()
    print(f"Found {len(slugs)} total character slugs!")
    
    completed = 0
    with ThreadPoolExecutor(max_workers=10) as char_executor:
        futures = [char_executor.submit(download_character, slug) for slug in slugs]
        for fut in as_completed(futures):
            folder, count = fut.result()
            if count == 46:
                completed += 1
                
    print(f"\nAll done! Successfully imported {completed}/{len(slugs)} character packs!")

if __name__ == "__main__":
    main()
