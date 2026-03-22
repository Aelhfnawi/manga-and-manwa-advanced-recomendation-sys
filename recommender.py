import json
import chromadb
import ollama

# Setup ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
try:
    collection = chroma_client.get_collection("manga_collection")
except Exception:
    print("manga_collection not found. Please run embedder.py first to populate the DB.")
    exit(1)

LLM_MODEL = 'llama3.2' # Completely local AI

def generate_recommendations(user_payload):
    prefs = user_payload.get('user_preferences', {})
    history = user_payload.get('reading_history', [])
    
    if not history:
        print("Empty reading history.")
        return
        
    user_taste = f"Priority features: {', '.join(prefs.get('priority', []))}.\n"
    user_taste += "Favorite Tropes and Manga:\n"
    for item in history:
        if item.get('rating', 0) >= 8.0:
            user_taste += f"- {item.get('title')}: {item.get('notes', '')}\n"
            
    print("Searching for similar manga in ChromaDB using local vector embeddings...")
    # Passing query_texts automatically invokes the default local embedding function in Chroma
    results = collection.query(
        query_texts=[user_taste],
        n_results=10
    )
    
    # Check if we got results
    if not results['ids'] or len(results['ids'][0]) == 0:
        print("No candidates found in the database. Try running embedder.py on a larger dataset.")
        return

    candidates = []
    for i in range(len(results['ids'][0])):
        candidates.append({
            "id": results['ids'][0][i],
            "title": results['metadatas'][0][i]['title'],
            "genres": results['metadatas'][0][i]['genres'],
            "tropes": results['metadatas'][0][i]['tropes'],
            "mc_traits": results['metadatas'][0][i]['mc_traits'],
            "progression": results['metadatas'][0][i]['progression'],
            "similarity": 1 - results['distances'][0][i] # Cosine distance
        })
        
    prompt = f"""
    You are an AI Manga/Manhwa Recommendation System.
    Based on the following User Profile and Top Candidates retrieved from a vector database, 
    select the EXACT 3 best recommendations. 
    Output strictly in the specified JSON schema without any markdown blocks or extra text.

    User Profile:
    {json.dumps(user_payload, indent=2)}
    
    Top Candidates:
    {json.dumps(candidates, indent=2)}
    
    JSON Schema Required:
    {{
      "taste_profile": {{
        "top_genres": [], "favorite_tropes": [], "preferred_mc_traits": [], "preferred_progression": "", "pacing_preference": "", "tone_preference": ""
      }},
      "recommendations": [
        {{ "title": "", "predicted_rating": 0, "similarity_score": "", "matching_features": [], "reason": "" }}
      ]
    }}
    """
    
    print("Formatting final recommendations via local Ollama LLM...")
    try:
        response = ollama.chat(model=LLM_MODEL, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], format='json')
        
        output = response['message']['content']
        print("\n--- FINAL JSON OUTPUT ---\n")
        print(output)
    except Exception as e:
        print(f"Ollama recommendation formatting failed: {e}")

if __name__ == "__main__":
    sample_input = {
      "user_preferences": {
        "priority": ["power_progression", "mc_personality", "story", "world_building", "art_style"]
      },
      "reading_history": [
        {
          "title": "Solo Leveling",
          "rating": 9.5,
          "finished_date": "15/12/2025",
          "chapter": 168,
          "notes": "loved the fast progression and the system"
        }
      ]
    }
    generate_recommendations(sample_input)
