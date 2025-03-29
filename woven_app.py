import streamlit as st
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Session state setup
if "story_state" not in st.session_state:
    st.session_state.story_state = {
        "genre": None,
        "target_emotion": None,
        "turns": [],
        "turn_count": 0,
        "chosen_turns": 5  # default, we'll let user pick later
    }

st.title("🧶 Woven: A Dreamlike Story Journey")

# Let user set parameters
genre = st.selectbox("Choose your genre", ["fantasy", "mystery", "dreamlike", "sci-fi"])
emotion = st.selectbox("Choose your ending emotion", ["hopeful", "nostalgic", "changed", "bittersweet"])
turns = st.slider("How many turns?", 3, 10, 5)

# Save to session state
st.session_state.story_state["genre"] = genre
st.session_state.story_state["target_emotion"] = emotion
st.session_state.story_state["chosen_turns"] = turns

user_input = st.text_input("What do you do next?")

if st.button("Submit"):
    # Build prompt from prior turns
    prior_turns = st.session_state.story_state["turns"]
    prompt = f"You are telling a {genre} story that should end with a feeling of {emotion}.\n"
    for turn in prior_turns:
        prompt += f"User: {turn['user_input']}\nStory: {turn['story_output']}\n"
    prompt += f"User: {user_input}\nStory:"

    # Call OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a poetic storyteller. The genre is {genre}. The goal is to guide the player toward a feeling of {emotion} by the end."},
            {"role": "user", "content": prompt}
        ]
    )

    story_output = response["choices"][0]["messagpe"]["content"]

    # Save the turn
    st.session_state.story_state["turns"].append({
        "user_input": user_input,
        "story_output": story_output
    })
    st.session_state.story_state["turn_count"] += 1

st.markdown("---")
st.subheader("Your Story So Far:")

for turn in st.session_state.story_state["turns"]:
    st.markdown(f"**You:** {turn['user_input']}")
    st.markdown(f"*{turn['story_output']}*")

if st.session_state.story_state["turn_count"] >= st.session_state.story_state["chosen_turns"]:
    st.markdown("✨ **The story concludes...**")
    st.stop()
