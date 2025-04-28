import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)  # Add override=True
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Session state for tracking story progress and user input
if "story_state" not in st.session_state:
    st.session_state.story_state = {
        "genre": None,
        "name": None,
        "current_emotion": None,
        "target_emotion": None,
        "summary": [],
        "turn_count": 0,
        "total_turns": 5,
        "started": False
    }

st.title("🧶 Woven: into your story")

# Only show the input form if the story hasn't started yet
if not st.session_state.story_state["started"]:
    with st.form(key="user_input_form"):
        name = st.text_input("What is your name?")
        genre = st.selectbox("Choose your genre", ["fantasy", "mystery", "dreamlike", "sci-fi", "horror", "romance", "comedy", "adventure"])
        current_emotion = st.text_input("How do you feel right now?")
        target_emotion = st.text_input("What do you want to feel?")
        turns = st.slider("How many minutes do you have?", 2, 10, 5)
        
        submit_button = st.form_submit_button("Submit")
        
        if submit_button:
            if name and genre and current_emotion and target_emotion:
                st.session_state.story_state.update({
                    "name": name,
                    "current_emotion": current_emotion,
                    "target_emotion": target_emotion,
                    "genre": genre,
                    "total_turns": turns,
                    "turn_count": 0,
                    "started": True
                })
                st.rerun()  # Updated from experimental_rerun to rerun
            else:
                st.error("Please fill out all fields before continuing.")

# Function to call OpenAI API
def openai_call(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a creative storyteller."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return None

# Function to build prompt based on story state
def build_prompt(final=False):
    base_summary = ", ".join(st.session_state.story_state['summary'])
    name = st.session_state.story_state['name']
    genre = st.session_state.story_state['genre']
    current_emotion = st.session_state.story_state['current_emotion']
    target_emotion = st.session_state.story_state['target_emotion']

    if final:
        return f"""
The story so far: {base_summary}.
Main character: {name}.
Genre: {genre}.
They feel {current_emotion} but will end feeling {target_emotion}.

Write the LAST paragraph. Respond exactly like this:
- The paragraph
- ~~~~
- 20-word story summary.
"""
    else:
        return f"""
The story so far: {base_summary}.
Main character: {name}.
Genre: {genre}.
They feel {current_emotion} but will end feeling {target_emotion}.

Write the NEXT paragraph ending with a CHOICE (action, path, dialogue). Respond exactly like this:
- The paragraph
- ~~~~
- Pose the choice as a question
- ~~~~
- 20-word story summary.
"""

# Function to play a turn of the story
def play_turn(final=False):
    prompt = build_prompt(final=final)
    raw_response = openai_call(prompt)
    
    if raw_response:
        parts = raw_response.split("~~~~")

        if len(parts) >= 3:
            story_output = parts[0].strip()
            question = parts[1].strip()
            summary = parts[2].strip()
        else:
            story_output = raw_response.strip()
            question = "What do you do next?"
            summary = ""

        st.write(story_output)
        if not final:
            st.caption(question)

        if summary:
            st.session_state.story_state['summary'].append(summary)
        st.session_state.story_state['turn_count'] += 1
        
        # Add a placeholder for user input between turns
        if not final:
            user_choice = st.text_input("Your choice:", key=f"choice_{st.session_state.story_state['turn_count']}")
            if user_choice:
                st.session_state.story_state['summary'].append(f"{st.session_state.story_state['name']} chose: {user_choice}")
                return True
        return True
    return False

# Story progression logic - only runs if the story has started
if st.session_state.story_state["started"]:
    # Display story header
    st.header(f"{st.session_state.story_state['name']}'s {st.session_state.story_state['genre']} Story")
    
    # If this is a new story, start the first turn
    if st.session_state.story_state["turn_count"] == 0:
        play_turn()
    
    # If we've reached the end, play the final turn
    elif st.session_state.story_state["turn_count"] >= st.session_state.story_state["total_turns"]:
        if "completed" not in st.session_state.story_state or not st.session_state.story_state["completed"]:
            play_turn(final=True)
            st.session_state.story_state["completed"] = True
            st.success("🌟 Story complete!")
            
            # Add reset button
            if st.button("Start a new story"):
                st.session_state.story_state = {
                    "genre": None,
                    "name": None,
                    "current_emotion": None,
                    "target_emotion": None,
                    "summary": [],
                    "turn_count": 0,
                    "total_turns": 5,
                    "started": False
                }
                st.rerun()  # Updated from experimental_rerun to rerun
    
    # Continue with the next turn if the user made a choice
    elif "last_turn_completed" not in st.session_state.story_state or st.session_state.story_state["last_turn_completed"]:
        turn_complete = play_turn()
        st.session_state.story_state["last_turn_completed"] = not turn_complete