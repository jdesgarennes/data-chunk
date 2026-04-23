import json
import requests
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

QDRANT = "http://10.1.60.67:6333"
OLLAMA = "http://rancher.pechanga.com:31434"
COLLECTION = "hr_policies"

MODEL = "nomic-embed-text-v2-moe"
BATCH = 50
WORKERS = 5

# --- CREATE COLLECTION (if not exists) ---
requests.put(
    f"{QDRANT}/collections/{COLLECTION}",
    json={"vectors": {"size": 768, "distance": "Cosine"}}
)

def embed(obj):
    r = requests.post(f"{OLLAMA}/api/embed", json={
        "model": MODEL,
        "input": "search_document: " + obj["text"]
    })
    r.raise_for_status()
    return {
        "id": str(uuid.uuid4()),
        "vector": r.json()["embeddings"][0],
        "payload": {
            "text": obj["text"],
            "source": obj["source"]
        }
    }

points = []

with open("../spacy/output/output.jsonl") as f:
    data = [json.loads(line) for line in f]

with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = [executor.submit(embed, obj) for obj in data]

    for future in as_completed(futures):
        points.append(future.result())

        if len(points) >= BATCH:
            requests.put(
                f"{QDRANT}/collections/{COLLECTION}/points",
                json={"points": points}
            )
            points = []

# flush remaining
if points:
    requests.put(
        f"{QDRANT}/collections/{COLLECTION}/points",
        json={"points": points}
    )

print("done")