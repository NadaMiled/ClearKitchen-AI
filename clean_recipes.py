import json

with open("recipes.json", "r", encoding="utf-8") as f:
    data = json.load(f)

clean = []
for r in data:

    # Nettoyer ingrédients
    ings = []
    for x in r["ingredients"]:
        x = x.replace("[", "").replace("]", "").replace("\"", "").strip()
        if x:
            ings.append(x)

    # Nettoyer instructions
    instr = []
    for step in r["instructions"]:
        step = step.replace("[", "").replace("]", "").replace("\"", "").strip()
        if step:
            instr.append(step)

    clean.append({
        "title": r["title"],
        "ingredients": ings,
        "instructions": instr
    })

with open("recipes_clean.json", "w", encoding="utf-8") as f:
    json.dump(clean, f, indent=2, ensure_ascii=False)

print("DONE.")
