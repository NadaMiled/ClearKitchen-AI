import json
import csv

input_path = "C:\\Users\\Nada\\Downloads\\dataset\\dataset\\full_dataset.csv"  # chemin vers le CSV du dataset
output_path = "recipes.json"

selected = []
with open(input_path, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if len(selected) >= 200:
            break
        # simple filtre = recette en anglais + ingrédients disponibles
        sel = {
            "title": row["title"],
            "ingredients": row["ingredients"].split(','),  # selon format CSV
            "instructions": row["directions"].split('\n') if "directions" in row else [row.get("instructions","")]
        }
        selected.append(sel)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(selected)} recipes to {output_path}")
