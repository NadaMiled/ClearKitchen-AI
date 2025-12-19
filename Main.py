import csv, time
import streamlit as st
import base64
from openai import OpenAI
import os
import json
import numpy as np
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(layout="wide")
st.markdown("""
<style>
/* Style uniquement pour les boutons 'secondary' (tes selected ingredients) */
button[kind="secondary"] {
    background-color: #f0eaff !important;
    color: #4a4075 !important;
    border-radius: 14px !important;
    padding: 6px 12px !important;
    font-size: 14px !important;
    border: 1px solid #d5c8ff !important;
    white-space: nowrap !important;
    margin: 1px !important;
    width: auto !important;
}

/* Hover pour ces boutons */
button[kind="secondary"]:hover {
    background-color: #e6d9ff !important;
    border-color: #c2aaff !important;
}
</style>
""", unsafe_allow_html=True)


st.markdown("""
<style>
/* Add spacing between columns */
div[data-testid="stHorizontalBlock"] > div {
    padding-right: 50px !important;
   
}
div[data-testid="stHorizontalBlock"] > div:last-child {
    padding-right: 0 !important;
    
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Largeur étendue uniquement pour notre zone de layout */
.layout-container {
    width: 100% !important;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)



st.markdown("""
<style>
/* Change la couleur du header */
header[data-testid="stHeader"] {
    border-bottom: 1px solid #d0d0d0;;
    background-color: #CAE7D3; !important;     /* couleur de fond */
    
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Rendre la colonne gauche sticky */
div[data-testid="column"]:first-child {
    position: sticky;
    top: 100px; /* distance depuis le haut */
    align-self: flex-start;
    z-index: 50;
}
</style>
""", unsafe_allow_html=True)



@st.cache_resource
def load_recipes():
    with open("recipes_emb.json", "r", encoding="utf-8") as f:
        return json.load(f)

local_recipes = load_recipes()


def cosine_sim(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

def ingredient_to_emoji(name):
    name = name.lower()
    mapping = {
        "tomato": "🍅","onion": "🧅","garlic": "🧄","milk": "🥛","egg": "🥚",
        "eggs": "🥚","cheese": "🧀","butter": "🧈","carrot": "🥕","apple": "🍎",
        "banana": "🍌","rice": "🍚","bread": "🍞","pepper": "🫑","lemon": "🍋","lime": "🍋",
        "pecan": "🥜","nuts": "🌰","Bagel":"🥯", "Bagels":"🥯","croissant":"🥐",
        "pretzels":"🥨","sugar": "🍬","shrimp": "🦐","prawn": "🦐","chocolate": "🍫",
        "wine": "🍷","watermelon": "🍉","melon": "🍈","orange": "🍊","coconut": "🥥",
        "kiwi": "🥝","pear": "🍐","peach": "🍑","blueberry": "🫐","potato": "🥔",
        "mushroom": "🍄","avocado": "🥑","cucumber": "🥒","lettuce": "🥬","cabbage": "🥬",
        "broccoli": "🥦","olive": "🫒","eggplant": "🍆","aubergine": "🍆","grapes":"🍇",
        "corn": "🌽","chili": "🌶️","hot pepper": "🌶️","strawberry": "🍓",
        "cherry": "🍒","canned": "🥫","can ": "🥫","pineapple": "🍍","leafy greens": "🥬",
        "mango": "🥭","tomato paste": "🥫", "honey":"🍯", "bacon": "🥓",
        "meat":"🥩", "beef":"🥩","ground beef":"🥩", "chicken": "🍗","sweet potato":"🍠",
        "juice": "🧃"
    }
    for key in mapping:
        if key in name:
            return mapping[key]
    return "🟡"   # fallback




def retrieve_recipes_embedding(user_ingredients, recipes, k=5, client=None):
    """
    RAG via embeddings :
    - crée un embedding pour la requête utilisateur
    - compare à tous les embeddings de recettes
    - retourne les k plus similaires
    """
    if client is None:
        raise ValueError("OpenAI client is required")

    # 1) Embedding de la requête (ingrédients utilisateur)
    query_text = user_ingredients.strip()
    if not query_text:
        return []

    q_resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=query_text
    )
    q_vec = q_resp.data[0].embedding

    
    scored = []
    for r in recipes:
        r_vec = r.get("embedding", None)
        if r_vec is None:
            continue
        sim = cosine_sim(q_vec, r_vec)
        scored.append((sim, r))

    
        # if sim < 0.1: continue
        top.append(r)

    return top


#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# init state
for k,v in dict(recipe=None, prompt="", ingredients="", diet="none", max_time=40).items():
    st.session_state.setdefault(k, v)

st.title("ClearKitchen AI 🍝🥗🥞")

#st.markdown('<div class="layout-container">', unsafe_allow_html=True)

# === 2-COLUMN LAYOUT (60% / 40%) ===
left, right = st.columns([3, 5])  # 3/2 = 60% vs 40%

with left:
    st.markdown("""
    <style>
    h1 {
        margin-top: 50px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    .streamlit-expanderHeader {
        font-size: 18px;
    }

    /* Réduit les marges entre colonnes */
    .block-container {
        padding-top: 1rem;
    }

    /* Réduit les espaces autour des boutons dans les colonnes */
    .css-1cpxqw2, .css-1kyxreq, .css-18e3th9 {  
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Style optionnel pour rendre les boutons plus jolis */
    .stButton>button {
        border-radius: 16px;
        padding: 6px 14px;
        border: 1px solid #dedbff;
        background-color: #f7f5ff;
        color: #000;
    }
    .stButton>button:hover {
        background-color: #ece7ff;
    }
    .detected-ing button {
        white-space: nowrap !important;
    }

    </style>
    """, unsafe_allow_html=True)



    st.markdown("""
    <style>
    .sel-btn {
        background-color: #e8ffe8;
        border-radius: 20px;
        padding: 6px 10px;
        margin: 4px;
        display: inline-block;
        border: 1px solid #b6e8b6;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)
    



    #col1, col2 = st.columns([4, 1])

    #with col1:
    ingredients = st.text_area(
            "### Enter your available ingredients:",
            value=st.session_state.get("ingredients", ""),
            #key="ingredients_input",
            placeholder="e.g., tomatoes, pasta, olive oil"
        )
    st.session_state.ingredients = ingredients
    


with right:
    

    st.markdown("### 📷 Try with a fridge image")
    uploaded_image = st.file_uploader("Upload a fridge/ingredients photo", type=["jpg","jpeg","png"])

    def encode_image(file):
        return base64.b64encode(file.read()).decode("utf-8")

    # Show image if uploaded
    if uploaded_image is not None:
        st.image(uploaded_image, caption="Uploaded image", use_container_width=True)
        # Button to detect ingredients
        if st.button("Detect Ingredients"):
            status = st.empty()
            status.write("Detecting ingredients...")
            st.session_state.fridge_selection = ""   # RESET à chaque nouvelle image
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
                for line in detected.split("\n") 
                if line.strip()
            ]

            status.empty()
        

    
    items = st.session_state.get("vision_items", [])
   

    
    if items:
        
        st.subheader("Detected ingredients (click to add):")

        cols = st.columns(min(len(items), 4))

        for i, item in enumerate(items):
            emoji = ingredient_to_emoji(item)

            # empêcher les retours à la ligne dans le texte
            #item_one_line = item.replace(" ", "\u00A0")

            with cols[i % len(cols)]:
                if st.button(f"{emoji} {item}", key=f"vision_btn_{i}"):
                    current = st.session_state.get("fridge_selection", "")
                    combined = (current + ", " + item).strip(", ")
                    st.session_state.fridge_selection = combined
                    st.rerun()



 # --- SELECTED INGREDIENTS BOX WITH REMOVABLE TAGS ---
    st.subheader("Selected ingredients (click to remove):")

    raw = st.session_state.get("fridge_selection", "")
    ingredients_list = [i.strip() for i in raw.split(",") if i.strip()]

    if not ingredients_list:
        st.info("No selected ingredients yet.")

    else:

        # --- 3 colonnes max ---
        cols = st.columns(4)

        for idx, ingr in enumerate(ingredients_list):
            
            col = cols[idx % 4]

            with col:
                
                if st.button(ingr, key=f"tag_{idx}", help="Click to remove"):
                    ingredients_list.pop(idx)
                    st.session_state.fridge_selection = ", ".join(ingredients_list)
                    st.rerun()

                
                st.markdown(
                    f"""
                    <script>
                    const btn = window.parent.document.querySelector('button[key="tag_{idx}"]');
                    if (btn) btn.parentElement.classList.add('tag-btn');
                    </script>
                    """,
                    unsafe_allow_html=True
                )


# --- SPACER ---
st.markdown("""
<hr style="height:3px; border:none; background-color:#d0d0d0;">
""", unsafe_allow_html=True)

# Init du flag feedback
st.session_state.setdefault("feedback_clicked", False)

spacer_left, center, spacer_right = st.columns([1, 2, 1])

with center:

    c1, c2 = st.columns(2)
    diet = c1.selectbox("Diet", ["none","vegetarian","vegan","halal","gluten-free"],
        index=["none","vegetarian","vegan","halal","gluten-free"].index(st.session_state.diet)
    )
    max_time = c2.slider("Max cook time (min)", 10, 120, st.session_state.max_time)

    # --- BUTTON STYLE ---
    st.markdown("""
    <style>
    .stButton > button {
        white-space: nowrap !important;
        width: auto !important;
        background-color: #CAE7D3 !important;
        color: #585858 !important;
        padding: 6px 5px !important;
        border-radius: 12px !important;
        font-size: 10px !important;
    }
    .stButton > button:hover {
        background-color: #b6e0c3 !important;
        cursor: pointer !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- CENTER BUTTON ---
    b1, b2, b3 = st.columns([1, 1, 1])
    with b2:
        generate_clicked = st.button("Suggest Recipe", key="generate_btn")

    # --- CLICK ON GENERATE ---
    if generate_clicked:

        user_text = st.session_state.get("ingredients", "").strip()
        vision_text = st.session_state.get("fridge_selection", "").strip()

        parts = []
        if user_text:
            parts.append(user_text)
        if vision_text:
            parts.append(vision_text)

        all_ingredients = ", ".join(parts)

        if not all_ingredients:
            st.warning("Please enter or select at least one ingredient.")
            st.stop()

        # --- RAG STEP ---
        retrieved = retrieve_recipes_embedding(
            all_ingredients,
            local_recipes,
            k=5,
            client=client
        )

        retrieved_text = "\n\n".join([
            f"TITLE: {r['title']}\nINGREDIENTS: {', '.join(r['ingredients'])}\nINSTRUCTIONS: {' '.join(r['instructions'])}"
            for r in retrieved
        ]) if retrieved else "No matching recipes found locally."

        # --- LLM PROMPT ---
        prompt = f"""
        You are an expert cooking assistant.

        User ingredients:
        {all_ingredients}

        Diet: {diet}
        Max cook time: {max_time} minutes.

        Local trusted recipes (DO NOT IGNORE):
        {retrieved_text}

        Using ONLY the user ingredients, and following realistic cooking rules,
        suggest ONE recipe that is feasible and reproducible.

        Return: title + ingredients with real quantities + step-by-step instructions.
        """

        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        st.session_state.recipe = resp.choices[0].message.content
        st.session_state.prompt = prompt
        st.session_state.diet = diet
        st.session_state.max_time = max_time
        st.session_state.feedback_clicked = False  # reset flag on new recipe


# ALWAYS SHOW THE RECIPE IF IT EXISTS (EVEN AFTER LIKE/DISLIKE)


if st.session_state.recipe:
    centerA, mid, centerB = st.columns([1, 2, 1])
    with mid:
        st.subheader("Suggested Recipe")
        st.write(st.session_state.recipe)

        with st.expander("🔍 Show technical details (prompt & raw output)"):
            st.write("**Prompt sent to the model**")
            st.code(st.session_state.prompt, language="text")

            st.write("**Raw model output**")
            st.code(st.session_state.recipe, language="text")

        f1, f2 = st.columns(2)

        def log_feedback(label):
            with open("logs.csv","a",newline="",encoding="utf-8") as f:
                csv.writer(f).writerow([
                    time.time(),
                    label,
                    st.session_state.ingredients,
                    st.session_state.diet,
                    st.session_state.max_time
                ])
            st.session_state.last_feedback = label  


        f1.button("👍 Like", on_click=log_feedback, args=("like",), key="like_btn_persist")
        f2.button("👎 Not helpful", on_click=log_feedback, args=("dislike",), key="dislike_btn_persist")
        # Zone de confirmation
        if st.session_state.get("last_feedback") == "like":
            st.success("Thanks! Your feedback was recorded.")
        elif st.session_state.get("last_feedback") == "dislike":
            st.warning("Feedback noted. We'll work to improve the suggestions.")

