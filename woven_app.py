import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)
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

# Add this to store all paragraphs
if "story_paragraphs" not in st.session_state:
    st.session_state.story_paragraphs = []
    
if "story_questions" not in st.session_state:
    st.session_state.story_questions = []

# Define genre-specific background images
# Replace these with your actual image URLs
GENRE_IMAGES = {
    "fantasy": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23",
    "mystery": "https://images.unsplash.com/photo-1555679486-e341a3e7b6de",
    "dreamlike": "https://images.unsplash.com/photo-1534447677768-be436bb09401",
    "sci-fi": "https://images.unsplash.com/photo-1484950763426-56b5bf172dbb",
    "horror": "https://images.unsplash.com/photo-1476900966873-ab290e38e3f7",
    "romance": "https://images.unsplash.com/photo-1518199266791-5375a83190b7",
    "comedy": "https://images.unsplash.com/photo-1551948521-0c49f5c12ce1",
    "adventure": "https://images.unsplash.com/photo-1504609773096-104ff2c73ba4"
}

# Add styling with full-page background and translucent elements
st.markdown("""
<style>
    /* Override Streamlit's default background */
    .stApp {
        background-color: transparent;
    }
    
    /* Full page background */
    .fullscreen-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-size: cover;
        background-position: center;
        z-index: -1;
        filter: brightness(0.7);
    }
    
    /* Main content container */
    .app-container {
        margin: 0 auto;
        max-width: 800px;
        padding: 20px;
    }
    
    /* Story paragraph styling */
    .story-text {
        background-color: rgba(20, 20, 20, 0.8);
        padding: 25px;
        border-radius: 10px;
        font-size: 20px;
        line-height: 1.6;
        font-family: 'Arial', sans-serif;
        color: #f8f8f8;
        text-shadow: 1px 1px 2px #000;
        margin-bottom: 25px;
        backdrop-filter: blur(3px);
        border: 1px solid rgba(80, 80, 80, 0.3);
    }
    
    /* Question styling */
    .story-question {
        background-color: rgba(40, 40, 40, 0.9);
        padding: 20px;
        border-radius: 8px;
        font-weight: bold;
        color: white;
        text-shadow: 1px 1px 2px #000;
        font-size: 18px;
        margin-top: 25px;
        margin-bottom: 20px;
        backdrop-filter: blur(5px);
        border-left: 4px solid rgba(200, 200, 200, 0.5);
    }
    
    /* Input field styling */
    .stTextInput > div > div > input {
        background-color: rgba(30, 30, 30, 0.7);
        color: white;
        border: 1px solid rgba(100, 100, 100, 0.3);
        padding: 12px;
        border-radius: 5px;
        backdrop-filter: blur(3px);
    }
    
    /* Placeholder text */
    .stTextInput input::placeholder {
        color: rgba(200, 200, 200, 0.6);
    }
    
    /* Headings */
    h1, h2, h3 {
        color: white;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: rgba(60, 60, 60, 0.7);
        color: white;
        border: 1px solid rgba(120, 120, 120, 0.3);
        backdrop-filter: blur(3px);
    }
    
    /* Input form styling */
    .stForm {
        background-color: rgba(30, 30, 30, 0.7);
        padding: 20px;
        border-radius: 10px;
        backdrop-filter: blur(5px);
    }
    
    /* Success message */
    .stSuccess {
        background-color: rgba(40, 120, 40, 0.7);
        color: white;
        backdrop-filter: blur(3px);
    }
</style>
""", unsafe_allow_html=True)

# Function to set full-page background image
def set_background(image_url):
    st.markdown(
        f"""
        <div class="fullscreen-bg" style="background-image: url('{image_url}');"></div>
        """,
        unsafe_allow_html=True
    )

# Main app container
st.markdown('<div class="app-container">', unsafe_allow_html=True)

st.title("🧶 Woven: into your story")

# Only show the input form if the story hasn't started yet
if not st.session_state.story_state["started"]:
    # Default background for start screen
    set_background("https://images.unsplash.com/photo-1518709268805-4e9042af9f23")
    
    with st.form(key="user_input_form"):
        name = st.text_input("What is your name?")
        genre = st.selectbox("Choose your genre", list(GENRE_IMAGES.keys()))
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
                # Clear any existing paragraphs when starting a new story
                st.session_state.story_paragraphs = []
                st.session_state.story_questions = []
                st.rerun()
            else:
                st.error("Please fill out all fields before continuing.")

# Function to call OpenAI API
def openai_call(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": """You are a creative storyteller who writes in a clear, 
                engaging style. Use simple, direct language that's fun to read. Keep sentences short. 
                Use active voice and strong verbs. Avoid complex vocabulary in favor of familiar, 
                vivid words. Make your writing colorful and interesting while remaining easy to understand."""},
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
Story so far: {base_summary}
You are {name}.
World: {genre}.
Right now, you feel {current_emotion}. You want to feel {target_emotion}.

Write the FINAL part of the story:
- Keep it short and powerful.
- Tie up the journey with emotion.
- Bring in a last surprise if it fits.
- No choice at the end, just a beautiful closing.

Structure:
- short paragraph
- ~~~~
- 20-word story summary
"""
    else:
        return f"""
Story so far: {base_summary}
You are {name}.
World: {genre}.
Right now, you feel {current_emotion}. You want to feel {target_emotion}.

Write the next part of the story:
- Keep the words simple and vivid.
- Bring in unexpected characters or moments that spark emotion.
- Add a short dialogue if it fits.
- End with a choice that pulls the player deeper into the story.

Structure:
- short paragraph
- ~~~~
- a question asking the player what they do next
- ~~~~
- 20-word story summary
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

        # Store paragraph and question in session state
        st.session_state.story_paragraphs.append(story_output)
        if not final:
            st.session_state.story_questions.append(question)

        if summary:
            st.session_state.story_state['summary'].append(summary)
        st.session_state.story_state['turn_count'] += 1
        
        return True
    return False

# Story progression logic - only runs if the story has started
if st.session_state.story_state["started"]:
    # Set background image based on genre
    genre = st.session_state.story_state['genre']
    background_image = GENRE_IMAGES.get(genre)
    if background_image:
        set_background(background_image)
    
    # Display story header
    st.header(f"{st.session_state.story_state['name']}'s {st.session_state.story_state['genre']} Story")
    
    # If this is a new story, start the first turn
    if st.session_state.story_state["turn_count"] == 0:
        turn_complete = play_turn()
        st.rerun()  # Rerun to show the first paragraph
    
    # Display all stored paragraphs with proper styling
    for i, para in enumerate(st.session_state.story_paragraphs):
        st.markdown(f'<div class="story-text">{para}</div>', unsafe_allow_html=True)
    
    # If we've reached the end, play the final turn
    if st.session_state.story_state["turn_count"] >= st.session_state.story_state["total_turns"]:
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
                st.session_state.story_paragraphs = []
                st.session_state.story_questions = []
                st.rerun()
    
    # Continue with the next turn after user input
    elif st.session_state.story_state["turn_count"] > 0:
        # Display the most recent question
        if len(st.session_state.story_questions) > 0:
            st.markdown(f'<div class="story-question">{st.session_state.story_questions[-1]}</div>', unsafe_allow_html=True)
            user_choice = st.text_input("Your choice", key=f"choice_{st.session_state.story_state['turn_count']}", placeholder="Type your choice here...", label_visibility="collapsed")
            if user_choice:
                st.session_state.story_state['summary'].append(f"{st.session_state.story_state['name']} chose: {user_choice}")
                # Generate next paragraph
                turn_complete = play_turn()
                st.rerun()

# Close main app container
st.markdown('</div>', unsafe_allow_html=True)