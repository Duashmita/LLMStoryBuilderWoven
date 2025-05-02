import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os

# Function to analyze user choice and update preferences
def analyze_user_choice(choice, question):
    """Analyze user's choice to update their preference profile"""
    choice_text = choice.lower()
    question_text = question.lower()
    
    # Default choice patterns to look for (can be expanded)
    patterns = {
        "risk_taker": {
            "increase": ["risk", "adventure", "try", "explore", "challenge", "brave", "new", "unknown", "dangerous"],
            "decrease": ["safe", "cautious", "careful", "wait", "hesitate", "home", "familiar", "secure", "protect"]
        },
        "optimism": {
            "increase": ["hope", "bright", "better", "good", "positive", "happy", "joy", "light", "smile", "laugh"],
            "decrease": ["dark", "sad", "worry", "concern", "fear", "doubt", "negative", "problem", "trouble"]
        },
        "social": {
            "increase": ["together", "friend", "people", "group", "help", "others", "talk", "share", "join", "team"],
            "decrease": ["alone", "solitary", "myself", "quiet", "away", "distance", "independent", "solo"]
        },
        "analytical": {
            "increase": ["think", "plan", "analyze", "understand", "reason", "logic", "consider", "examine", "study"],
            "decrease": ["feel", "sense", "heart", "emotion", "gut", "intuition", "instinct", "immediate"]
        },
        "fantasy_interest": {
            "increase": ["magic", "wonder", "dream", "imagine", "fantasy", "dragon", "fairy", "enchanted", "mysterious"],
            "decrease": ["real", "practical", "actual", "realistic", "concrete", "ordinary", "everyday", "normal"]
        },
        "introspective": {
            "increase": ["reflect", "ponder", "contemplate", "inner", "meaning", "thought", "deep", "soul", "mind"],
            "decrease": ["act", "move", "go", "run", "jump", "do", "action", "immediate", "physical"]
        }
    }
    
    # Record the choice pattern for future analysis
    st.session_state.choice_patterns.append(choice_text)
    
    # Check for pattern matches in the choice
    for trait, keywords in patterns.items():
        # Check for increases
        for keyword in keywords["increase"]:
            if keyword in choice_text:
                st.session_state.story_state["user_preferences"][trait] += 1
                break  # Only count each trait once per choice
                
        # Check for decreases
        for keyword in keywords["decrease"]:
            if keyword in choice_text:
                st.session_state.story_state["user_preferences"][trait] -= 1
                break  # Only count each trait once per choice
    
    # Cap values between -5 and 5
    for trait in st.session_state.story_state["user_preferences"]:
        st.session_state.story_state["user_preferences"][trait] = max(-5, min(5, st.session_state.story_state["user_preferences"][trait]))
    
    # If there are more than 5 choice patterns stored, analyze them for themes
    if len(st.session_state.choice_patterns) >= 3:
        all_choices = " ".join(st.session_state.choice_patterns).lower()
        # Additional pattern matching could be done here for more complex analysis
        
    return st.session_state.story_state["user_preferences"]

api_key = st.secrets["openai_api_key"]

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
        "started": False,
        "user_preferences": {
            "risk_taker": 0,       # -5 to 5 scale (cautious to adventurous)
            "optimism": 0,         # -5 to 5 scale (pessimistic to optimistic)
            "social": 0,           # -5 to 5 scale (solitary to social)
            "analytical": 0,       # -5 to 5 scale (intuitive to analytical)
            "fantasy_interest": 0, # -5 to 5 scale (realistic to fantastical)
            "introspective": 0     # -5 to 5 scale (action-oriented to introspective)
        }
    }

# Add this to store all paragraphs
if "story_paragraphs" not in st.session_state:
    st.session_state.story_paragraphs = []
    
if "story_questions" not in st.session_state:
    st.session_state.story_questions = []
    
if "choice_patterns" not in st.session_state:
    st.session_state.choice_patterns = []

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
    turn_count = st.session_state.story_state['turn_count']
    total_turns = st.session_state.story_state['total_turns']
    
    # Get user preferences
    preferences = st.session_state.story_state['user_preferences']
    
    # Build a personalization string based on user preferences
    personalization = []
    
    if preferences['risk_taker'] >= 3:
        personalization.append("The character is drawn to adventure and taking risks.")
    elif preferences['risk_taker'] <= -3:
        personalization.append("The character prefers safety and careful consideration.")
        
    if preferences['optimism'] >= 3:
        personalization.append("The character tends to look for hope and positivity.")
    elif preferences['optimism'] <= -3:
        personalization.append("The character often notices challenges and potential problems.")
        
    if preferences['social'] >= 3:
        personalization.append("The character values connection with others.")
    elif preferences['social'] <= -3:
        personalization.append("The character appreciates solitude and independence.")
        
    if preferences['analytical'] >= 3:
        personalization.append("The character approaches situations with logic and analysis.")
    elif preferences['analytical'] <= -3:
        personalization.append("The character trusts their intuition and feelings.")
        
    if preferences['fantasy_interest'] >= 3:
        personalization.append("The character is open to magical or fantastical elements.")
    elif preferences['fantasy_interest'] <= -3:
        personalization.append("The character prefers grounded, realistic experiences.")
        
    if preferences['introspective'] >= 3:
        personalization.append("The character values reflection and deeper meaning.")
    elif preferences['introspective'] <= -3:
        personalization.append("The character prefers action and practical solutions.")
    
    # Combine the personalization insights
    personalization_string = " ".join(personalization)
    
    # Determine if fantasy elements should be introduced based on player choices
    use_fantasy = preferences['fantasy_interest'] > 0
    
    # Determine if we're approaching the final turns to prepare for the emotional breakthrough
    approaching_climax = (turn_count >= total_turns - 2) and not final

    if final:
        return f"""
Story so far: {base_summary}
You are {name}.
World: {genre}.
The character began feeling {current_emotion} and has been experiencing a journey toward {target_emotion}.

Character insights based on their choices:
{personalization_string}

Write the FINAL part of the story:
- Create a powerful emotional breakthrough moment that finally allows the character to fully experience {target_emotion}
- This should be a specific, concrete event (not just an internal realization)
- The event should feel like the culmination of the character's journey
- Show how this event transforms the character's perspective
- Tailor the nature of this breakthrough to match the character's established preferences and tendencies
- Don't explicitly state the emotion - show it through the character's reactions, sensations, and thoughts
- Keep it short and powerful
- End with a sense of resolution or new beginning that feels earned

Structure:
- short paragraph
- ~~~~
- 20-word story summary
"""
    elif approaching_climax:
        return f"""
Story so far: {base_summary}
You are {name}.
World: {genre}.
The character began feeling {current_emotion} and is approaching a pivotal moment that will lead to experiencing {target_emotion}.

Character insights based on their choices:
{personalization_string}

Write the next part of the story:
- Set up the conditions for an emotional breakthrough in the next turn
- Create a situation that challenges the character's current perspective
- Plant the seeds for a significant event that will transform how they feel
- Don't rush the emotional change yet - build anticipation
- {'Include subtle fantasy elements if they enhance the emotional journey' if use_fantasy else 'Keep the narrative grounded in human experience with a touch of wonder'}
- Add meaningful dialogue that reveals something important
- Tailor this part to align with the character's established preferences and tendencies
- End with a choice that will directly lead to the emotional breakthrough moment

Structure:
- short paragraph
- ~~~~
- a question that presents a meaningful choice with clear emotional implications
- ~~~~
- 20-word story summary
"""
    else:
        return f"""
Story so far: {base_summary}
You are {name}.
World: {genre}.
The character began feeling {current_emotion} and is on a journey that will gradually lead to feeling {target_emotion}.

Character insights based on their choices so far:
{personalization_string}

Write the next part of the story:
- Create vivid, specific scenes with sensory details
- Show subtle shifts in the character's emotional state through their perceptions and actions
- Don't explicitly mention the target emotion - create situations that move toward it indirectly
- Start with human characters in the first turn, only introducing fantasy elements if the player's choices suggest they want that.' if turn_count == 0 else ('Adjust the level of fantasy elements based on the character\'s preferences shown through their choices' if use_fantasy else 'Focus on human characters and real-world situations with authentic emotional depth.'
- Include meaningful dialogue that reveals character and advances the emotional journey
- Tailor the scene to align with the character's established preferences and tendencies
- End with a MEANINGFUL CHOICE that:
  * Presents two clearly different paths with emotional consequences
  * Makes one path align more with staying in {current_emotion} and the other with movement toward {target_emotion}
  * Forces the player to choose between comfort/familiarity vs. growth/change
  * Has real stakes that will impact the story's direction
  * Creates tension between what feels safe and what might lead to growth

Structure:
- short paragraph
- ~~~~
- a question that presents a meaningful emotional choice
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
                    "started": False,
                    "user_preferences": {
                        "risk_taker": 0,
                        "optimism": 0,
                        "social": 0,
                        "analytical": 0,
                        "fantasy_interest": 0,
                        "introspective": 0
                    }
                }
                st.session_state.story_paragraphs = []
                st.session_state.story_questions = []
                st.session_state.choice_patterns = []
                st.rerun()
    
    # Continue with the next turn after user input
    elif st.session_state.story_state["turn_count"] > 0:
        # Display the most recent question
        if len(st.session_state.story_questions) > 0:
            st.markdown(f'<div class="story-question">{st.session_state.story_questions[-1]}</div>', unsafe_allow_html=True)
            user_choice = st.text_input("Your choice", key=f"choice_{st.session_state.story_state['turn_count']}", placeholder="Type your choice here...", label_visibility="collapsed")
            if user_choice:
                # Get the last question to analyze with the user's choice
                last_question = st.session_state.story_questions[-1]
                
                # Analyze the user's choice to update preferences
                analyze_user_choice(user_choice, last_question)
                
                # Add the choice to the story summary
                st.session_state.story_state['summary'].append(f"{st.session_state.story_state['name']} chose: {user_choice}")
                
                # Generate next paragraph
                turn_complete = play_turn()
                st.rerun()

# Close main app container
st.markdown('</div>', unsafe_allow_html=True)