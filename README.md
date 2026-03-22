# 📚 Manga/Manhwa Advanced Recommendation System
![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103.1-009688.svg)
![ChromaDB](https://img.shields.io/badge/Chroma-Vector_DB-FF69B4.svg)
![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black.svg)

An advanced, **100% local, and entirely free** recommendation engine for Manga and Manhwa. This system utilizes official open-source AniList GraphQL API data, local Vector Embeddings via ChromaDB, and Local Large Language Models (LLMs) via Ollama. 

It provides highly personalized, semantic-based recommendations by mapping your reading history to nuanced, AI-extracted traits like **MC Personalities**, **Power Progression**, and **World-Building Tropes**.

---

## ✨ Features
* **Zero Cost & Fully Local**: Runs completely on your own machine. No OpenAI API keys or paid services required!
* **Hybrid Search Engine**: Combines classic metadata filtering (genres, tags) with dense vector semantic search (Cosine Similarity).
* **LLM Feature Extraction**: Uses local LLMs to dynamically read manga descriptions and extract implicit traits (e.g., "Underdog MC", "Skill Tree System").
* **FastAPI Backend**: Provides a real-time REST API endpoint for fetching recommendations instantly.

---

## 🛑 Prerequisites

Because this system runs entirely on your local machine, you **must have Ollama installed and a local LLM pulled**. 

1. Install [Ollama](https://ollama.com/).
2. Open your Command Prompt (cmd) and pull the default model:
   ```cmd
   ollama pull llama3.2
   ```
*(Note: You can use other models like `phi3` or `mistral`, but `llama3.2` is configured as the default in the code).*

---

## 🚀 Setup & Installation

### 1. Activate the Python Environment
Open Command Prompt (cmd) inside your project folder and activate the virtual environment:
```cmd
venv\Scripts\activate.bat
```
*(If the activate script doesn't work, ensure you have the requirements like `chromadb`, `ollama`, and `fastapi` installed).*

### 2. Fetch Manga Data
Run the API client to fetch the top popular Manga and Manhwa directly from the official AniList GraphQL API.
```cmd
python anilist_client.py
```
* **Result**: Creates a `manga_data.json` file inside your folder containing titles, descriptions, and tags.

### 3. Populate the Vector Database (Feature Extraction)
This step reads the JSON data, uses your local LLM to extract "tropes" and "MC traits", and generates dense embeddings to store in ChromaDB using `all-MiniLM-L6-v2`.
```cmd
python embedder.py
```
* ⚠️ **Note**: This process uses your local hardware to analyze dozens of descriptions one by one. It **will take several minutes**.
* **Result**: Creates a folder named `chroma_db` serving as the persistent vector database.

### 4. Start the REST API
Once your database is populated, start the FastAPI server.
```cmd
python api.py
```
* **Result**: A web server starts at `http://localhost:8000`.

---

## 🎯 Usage / Testing

1. Go to `http://localhost:8000/docs` in your browser.
2. Click on the `POST /recommend` route and click "Try it out".
3. Paste a JSON payload of your reading history and preferences:
   ```json
    {
      "user_preferences": {
        "priority": ["power_progression", "mc_personality", "story"]
      },
      "reading_history": [
        {
          "title": "Solo Leveling",
          "rating": 9.5,
          "notes": "loved the fast progression and the system"
        }
      ]
    }
   ```
4. Click **Execute**, and you will receive your highly-personalized strict JSON recommendations!

---

## ⚙️ Configuration
By default, the scripts look for your local Ollama model under the name `'llama3.2'`.
If you pulled a different model, you must update the `LLM_MODEL` variable at the top of `embedder.py`, `recommender.py`, and `api.py`.
