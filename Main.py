import csv, time
import streamlit as st
import base64
from openai import OpenAI

import json

with open("recipes_clean.json", "r", encoding="utf-8") as f:
    local_recipes = json.load(f)

def retrieve_recipes(user_ingredients, recipes, k=5):
    """Simple RAG retrieval: score recipes by ingredient substring overlap."""
    # ingrédients saisis par l'utilisateur
    user_list = [i.strip().lower() for i in user_ingredients.split(",") if i.strip()]

    scored = []
    for r in recipes:
        ing_texts = [ing.lower() for ing in r["ingredients"]]

        score = 0
        for u in user_list:
            # si le texte de l'ingrédient apparaît dans au moins un ingrédient de la recette
            if any(u in ing for ing in ing_texts):
                score += 1

        if score > 0:
            scored.append((score, r))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [r for score, r in scored[:k]]






client = OpenAI(api_key="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")

# init state
for k,v in dict(recipe=None, prompt="", ingredients="", diet="none", max_time=40).items():
    st.session_state.setdefault(k, v)

st.title("ClearKitchen AI 🍝🥗🥞")

col1, col2 = st.columns([4, 1])

with col1:
    ingredients = st.text_area(
        "Enter your available ingredients:",
        value=st.session_state.get("ingredients", ""),
        #key="ingredients_input",
        placeholder="e.g., tomatoes, pasta, olive oil"
    )
    st.session_state.ingredients = ingredients

#with col2:
   # st.write("")  # petit espace pour l’alignement vertical
    #if st.button("💾 Save"):
    #    st.session_state.ingredients = ingredients
     #   st.success("Ingredients saved!")

c1,c2 = st.columns(2)
diet = c1.selectbox("Diet", ["none","vegetarian","vegan","halal","gluten-free"],
                    index=["none","vegetarian","vegan","halal","gluten-free"].index(st.session_state.diet))
max_time = c2.slider("Max cook time (min)", 10, 120, st.session_state.max_time)

#if st.button("Generate Recipe"):
    #if ingredients.strip():
    #    prompt = (
    #        "Suggest a realistic, reproducible recipe using ONLY these ingredients:\n"
    #        f"{ingredients}\nConstraints: diet={diet}, max_cook_time={max_time} minutes.\n"
    #        "Return title + ingredients (with quantities) + steps."
    #    )
    #    resp = client.chat.completions.create(
    #        model="gpt-3.5-turbo",
    #        messages=[{"role":"user","content":prompt}]
    #    )
    #    st.session_state.recipe = resp.choices[0].message.content
    #    st.session_state.prompt = prompt
    #    st.session_state.ingredients = ingredients
    #    st.session_state.diet = diet
    #    st.session_state.max_time = max_time



if st.button("Generate Recipe"):
    if ingredients.strip():

        # --- RAG STEP : retrieve similar recipes ---
        retrieved = retrieve_recipes(ingredients, local_recipes, k=5)



        # 🔍 DEBUG — voir si le RAG fonctionne
        st.write("🔍 RAG found", len(retrieved), "recipes")
        for r in retrieved:
            st.write("- ", r["title"])




        retrieved_text = "\n\n".join([
            f"TITLE: {r['title']}\nINGREDIENTS: {', '.join(r['ingredients'])}\nINSTRUCTIONS: {' '.join(r['instructions'])}"
            for r in retrieved
        ]) if retrieved else "No matching recipes found locally."

        # --- LLM PROMPT USING RAG ---
        prompt = f"""
You are an expert cooking assistant.

User ingredients:
{ingredients}

Diet: {diet}
Max cook time: {max_time} minutes.

Local trusted recipes (DO NOT IGNORE):
{retrieved_text}

Using ONLY the user ingredients, and following realistic cooking rules,
suggest ONE recipe that is feasible and reproducible.

If the local recipes contain partial matches, use them as inspiration and use the title as it is.
Return: title + ingredients with real quantities + step-by-step instructions.
"""

        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        st.session_state.recipe = resp.choices[0].message.content
        st.session_state.prompt = prompt
        st.session_state.ingredients = ingredients
        st.session_state.diet = diet
        st.session_state.max_time = max_time





# show last result if present
if st.session_state.recipe:
    st.subheader("Suggested Recipe")
    st.write(st.session_state.recipe)

    st.markdown("### Transparency")
    st.write("**Prompt sent to the model**")
    st.code(st.session_state.prompt, language="text")
    st.write("**Raw model output**")
    st.code(st.session_state.recipe, language="text")

    st.markdown("### Feedback")
    f1,f2 = st.columns(2)

    def log_feedback(label):
        with open("logs.csv","a",newline="",encoding="utf-8") as f:
            csv.writer(f).writerow([time.time(),label,
                                    st.session_state.ingredients,
                                    st.session_state.diet,
                                    st.session_state.max_time])
    f1.button("👍 Like", on_click=log_feedback, args=("like",), key="like_btn")
    f2.button("👎 Not helpful", on_click=log_feedback, args=("dislike",), key="dislike_btn")
else:
    st.info("Enter ingredients and click Generate Recipe.")




st.markdown("### 📷 Try with a fridge image")
uploaded_image = st.file_uploader("Upload a fridge/ingredients photo", type=["jpg","jpeg","png"])

def encode_image(file):
    return base64.b64encode(file.read()).decode("utf-8")

# Show image if uploaded
if uploaded_image is not None:
    st.image(uploaded_image, caption="Uploaded image", use_container_width=True)
    # Button to detect ingredients
    if st.button("Detect Ingredients"):
        st.write("Detecting ingredients...")
        img_b64 = encode_image(uploaded_image)

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "List ONLY the visible food ingredients as one item per line. No descriptions, no shelf info, no numbers. Example:\n- eggs\n- milk\n- tomatoes"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                        },
                    ],
                }
            ],
        )

        detected = response.choices[0].message.content

        # Save in session
        st.session_state["vision_items"] = [
            line.replace("-", "").strip()
            for line in detected.split("\n") if line.strip()
        ]

# ---- SHOW CHECKBOXES OUTSIDE THE BUTTON ----
items = st.session_state.get("vision_items", [])

if items:
    st.subheader("Select ingredients to add:")
    selected = []
    for i, item in enumerate(items):
        if st.checkbox(item, key=f"cb_{i}_{item}"):
            selected.append(item)

    if st.button("➕ Add selected"):
        current = st.session_state.get("ingredients", "")
        combined = (current + ", " + ", ".join(selected)).strip(", ")
        st.session_state["ingredients"] = combined
        st.success("Added selected ingredients!")













