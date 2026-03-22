import requests
import json
import os
import time

ANILIST_URL = 'https://graphql.anilist.co'

def fetch_top_manga(page=1, per_page=50):
    query = '''
    query ($page: Int, $perPage: Int) {
      Page (page: $page, perPage: $perPage) {
        media (type: MANGA, sort: POPULARITY_DESC) {
          id
          title {
            romaji
            english
          }
          description
          genres
          tags {
            name
          }
          averageScore
          popularity
          countryOfOrigin
        }
      }
    }
    '''
    
    variables = {
        'page': page,
        'perPage': per_page
    }

    response = requests.post(ANILIST_URL, json={'query': query, 'variables': variables})
    
    if response.status_code == 200:
        return response.json()['data']['Page']['media']
    else:
        print(f"Failed to fetch data: {response.status_code}")
        print(response.text)
        return []

def save_manga_data(filename="manga_data.json", num_pages=1):
    all_manga = []
    print(f"Fetching top {num_pages * 50} manga/manhwa from AniList...")
    
    for page in range(1, num_pages + 1):
        print(f"Fetching page {page}...")
        manga_list = fetch_top_manga(page=page, per_page=50)
        all_manga.extend(manga_list)
        time.sleep(1.5)  # Prevents occasional 500 error from rapid firing pagination
        
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_manga, f, ensure_ascii=False, indent=2)
        
    print(f"Saved {len(all_manga)} entries to {filename}.")
    return all_manga

if __name__ == "__main__":
    save_manga_data("manga_data.json", num_pages=2)
