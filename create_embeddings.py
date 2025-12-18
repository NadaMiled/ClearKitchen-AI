import json
import numpy as np
from openai import OpenAI

client = OpenAI(api_key="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")
# 1. Charger les recettes nettoyées
with open("recipes_clean.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)

emb_data = []

for idx, r in enumerate(recipes):
    title = r.get("title", "")
    ingredients = r.get("ingredients", [])
    instructions = r.get("instructions", [])

    # Texte de base pour l'embedding = titre + ingrédients
    text = title + "\n" + "\n".join(ingredients)

    # 2. Appel embedding
    emb_resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    vector = emb_resp.data[0].embedding  # liste de floats

    emb_data.append({
        "title": title,
        "ingredients": ingredients,
        "instructions": instructions,
        "embedding": vector
    })

    if (idx + 1) % 20 == 0:
        print(f"Embedded {idx+1} recipes...")

# 3. Sauvegarder dans un nouveau fichier
with open("recipes_emb.json", "w", encoding="utf-8") as f:
    json.dump(emb_data, f, ensure_ascii=False, indent=2)

print("DONE: wrote embeddings to recipes_emb.json")
