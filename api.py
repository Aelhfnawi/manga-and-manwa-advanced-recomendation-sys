from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import chromadb
import ollama

app = FastAPI(title="Manga Recommendation API")

# Define input models
class UserPreferences(BaseModel):
    priority: List[str]

class ReadingHistoryItem(BaseModel):
    title: str
    rating: float
    finished_date: Optional[str] = None
    chapter: Optional[int] = None
    notes: Optional[str] = None

class RecommendationRequest(BaseModel):
    user_preferences: UserPreferences
    reading_history: List[ReadingHistoryItem]

# Setup ChromaDB
try:
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection("manga_collection")
except Exception:
    collection = None
    print("WARNING: manga_collection not found. Ensure embedder.py has been run to populate data.")

LLM_MODEL = 'llama3.2' # You can change this to your preferred local model

@app.post("/recommend")
def get_recommendations(req: RecommendationRequest):
    if collection is None:
        raise HTTPException(status_code=500, detail="Database not initialized on server.")
        
    payload = req.model_dump()
    prefs = payload.get('user_preferences', {})
    history = payload.get('reading_history', [])
    
    if not history:
        raise HTTPException(status_code=400, detail="Empty reading history.")

    user_taste = f"Priority features: {', '.join(prefs.get('priority', []))}.\n"
    user_taste += "Favorite Tropes and Manga:\n"
    for item in history:
        if item.get('rating', 0) >= 8.0:
            user_taste += f"- {item.get('title')}: {item.get('notes', '')}\n"
            
    # Query Chroma Local DB
    results = collection.query(
        query_texts=[user_taste],
        n_results=10
    )
    
    if not results['ids'] or len(results['ids'][0]) == 0:
        raise HTTPException(status_code=404, detail="No candidates found in DB.")

    candidates = []
    for i in range(len(results['ids'][0])):
        candidates.append({
            "id": results['ids'][0][i],
            "title": results['metadatas'][0][i]['title'],
            "genres": results['metadatas'][0][i]['genres'],
            "tropes": results['metadatas'][0][i]['tropes'],
            "mc_traits": results['metadatas'][0][i]['mc_traits'],
            "progression": results['metadatas'][0][i]['progression'],
            "similarity": 1 - results['distances'][0][i]
        })

    prompt = f"""
    You are an AI Manga/Manhwa Recommendation System.
    Based on the following User Profile and Top 10 Candidates retrieved from a vector database, 
    select the EXACT 3 best recommendations. 
    Output strictly in the specified JSON schema without any markdown blocks or extra text.

    User Profile:
    {json.dumps(payload, indent=2)}
    
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
    
    try:
        response = ollama.chat(model=LLM_MODEL, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ], format='json')
        
        output = response['message']['content']
        return json.loads(output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM formatting failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
