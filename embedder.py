import json
import os
import chromadb
import ollama

# Setup ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# ChromaDB uses a local text embedding model by default (all-MiniLM-L6-v2) 
# which requires NO api keys and runs completely on your machine.
collection = chroma_client.get_or_create_collection(
    name="manga_collection",
    metadata={"hnsw:space": "cosine"}
)

LLM_MODEL = 'llama3.2' # Default local model, completely free

def extract_features(manga):
    description = manga.get('description', '')
    if not description:
        description = "No description available."
    tags = [t['name'] for t in manga.get('tags', [])]
    genres = manga.get('genres', [])
    
    prompt = f"""
    Analyze the following manga/manhwa and extract its core tropes, main character traits, and power progression style.
    Respond STRICTLY in JSON format with no extra text.
    Format: {{"tropes": ["string"], "mc_traits": ["string"], "progression": "string"}}
    
    Title: {manga.get('title', {}).get('english') or manga.get('title', {}).get('romaji')}
    Genres: {', '.join(genres)}
    Tags: {', '.join(tags)}
    Description: {description}
    """
    
    try:
        response = ollama.chat(model=LLM_MODEL, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], format='json')
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"Ollama feature extraction failed for {manga['id']}: {e}")
        return {"tropes": [], "mc_traits": [], "progression": "Unknown"}

def processData(filename="manga_data.json"):
    if not os.path.exists(filename):
        print(f"{filename} not found. Run anilist_client.py first.")
        return
        
    with open(filename, 'r', encoding='utf-8') as f:
        manga_list = json.load(f)
        
    print(f"Processing {len(manga_list)} entries...")
    for i, manga in enumerate(manga_list):
        manga_id = str(manga['id'])
        
        # Check if already in DB
        existing = collection.get(ids=[manga_id])
        if existing and len(existing['ids']) > 0:
            continue
            
        title = manga['title'].get('english') or manga['title'].get('romaji')
        print(f"[{i+1}/{len(manga_list)}] Processing: {title}")
        features = extract_features(manga)
        
        # Create a rich text representation for embedding
        rich_text = f"Title: {title}\n"
        rich_text += f"Genres: {', '.join(manga.get('genres', []))}\n"
        rich_text += f"Tropes: {', '.join(features.get('tropes', []))}\n"
        rich_text += f"MC Traits: {', '.join(features.get('mc_traits', []))}\n"
        rich_text += f"Progression: {features.get('progression', '')}\n"
        description = str(manga.get('description', '')).replace('<br>', '\n')
        rich_text += f"Description: {description}"
        
        # Store metadata
        meta = {
            "title": title or '',
            "genres": ", ".join(manga.get('genres', [])),
            "tropes": ", ".join(features.get('tropes', [])),
            "mc_traits": ", ".join(features.get('mc_traits', [])),
            "progression": str(features.get('progression', '')),
            "score": manga.get('averageScore') or 0,
            "popularity": manga.get('popularity') or 0
        }
        
        # Insert into ChromaDB
        # We only supply the document string, and Chroma handles the embedding vector calculation locally automatically!
        collection.add(
            ids=[manga_id],
            metadatas=[meta],
            documents=[rich_text]
        )
        
    print("Done processing and embedding data.")

if __name__ == "__main__":
    processData()
