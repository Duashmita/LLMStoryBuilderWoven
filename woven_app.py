import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import json
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from emotional_validator import EmotionalValidator

def init_supabase():
    """Initialize Supabase client"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        st.write("Debug - Supabase URL:", url)  # Debug log
        st.write("Debug - Supabase key length:", len(key))  # Debug log (showing length for security)
        client = create_client(url, key)
        st.write("Debug - Supabase client created successfully")  # Debug log
        return client
    except Exception as e:
        st.error(f"Error initializing Supabase: {str(e)}")
        raise

def save_research_email(story_id, email):
    """Save research email to Supabase"""
    supabase = init_supabase()
    supabase.table('stories').update({"research_email": email}).eq("id", story_id).execute()

def save_emotional_data(story_data):
    """Save emotional data to Supabase"""
    try:
        st.write("Debug - Starting save_emotional_data")  # Debug log
        supabase = init_supabase()
        st.write("Debug - Supabase client initialized")  # Debug log
        
        # If this is the first turn, create a new story entry
        if story_data["turn_number"] == 1:
            story_meta = {
                "name": st.session_state.story_state["name"],
                "genre": st.session_state.story_state["genre"],
                "total_turns": st.session_state.story_state["total_turns"],
                "start_time": datetime.now().isoformat(),
                "research_email": st.session_state.story_state.get("research_email")
            }
            st.write("Debug - Creating new story entry:", story_meta)
            try:
                result = supabase.table('stories').insert(story_meta).execute()
                st.write("Debug - Insert result:", result)  # Debug log
                if not result.data:
                    st.error("Failed to create story entry. Please check your database connection.")
                    return
                story_id = result.data[0]['id']
                st.write("Debug - New story created with ID:", story_id)
            except Exception as e:
                st.error(f"Error creating story entry: {str(e)}")
                st.write("Debug - Full error details:", e.__dict__)  # Debug log
                return
        else:
            try:
                # Get the latest story_id
                st.write("Debug - Fetching latest story ID")  # Debug log
                result = supabase.table('stories').select('id').order('id', desc=True).limit(1).execute()
                st.write("Debug - Fetch result:", result)  # Debug log
                if not result.data:
                    st.error("Could not find story ID. Please check your database connection.")
                    return
                story_id = result.data[0]['id']
                st.write("Debug - Retrieved story ID:", story_id)
            except Exception as e:
                st.error(f"Error retrieving story ID: {str(e)}")
                st.write("Debug - Full error details:", e.__dict__)  # Debug log
                return
        
        # Prepare emotional data
        emotional_data = {
            "story_id": story_id,
            "turn_number": story_data["turn_number"],
            "character_mood": story_data["character_mood"],
            "user_mood": story_data["user_mood"],
            "story_summary": story_data["story_summary"],
            "question": story_data["question"],
            "personality_scores": json.dumps(story_data["personality_scores"]),
            "story_phase": story_data["story_phase"],
            "is_final": story_data["is_final"],
            "timestamp": datetime.now().isoformat()
        }
        
        st.write("Debug - Saving emotional data:", emotional_data)
        
        # Insert emotional data
        try:
            st.write("Debug - Attempting to insert emotional data")  # Debug log
            result = supabase.table('emotional_data').insert(emotional_data).execute()
            st.write("Debug - Insert result:", result)  # Debug log
            st.write("Debug - Emotional data saved successfully:", result.data)
        except Exception as e:
            st.error(f"Error saving emotional data: {str(e)}")
            st.write("Debug - Full error details:", e.__dict__)  # Debug log
            return
            
    except Exception as e:
        st.error(f"Unexpected error in save_emotional_data: {str(e)}")
        st.write("Debug - Full error details:", e.__dict__)  # Debug log
        return

def save_validation_data(story_id, arc_right, comments):
    """Save validation data to Supabase"""
    supabase = init_supabase()
    
    validation_data = {
        "story_id": story_id,
        "arc_valid": arc_right == 'Yes',
        "comments": comments,
        "timestamp": datetime.now().isoformat()
    }
    
    supabase.table('mood_validations').insert(validation_data).execute()

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

api_key = st.secrets["gemini"]["api_key"]
genai.configure(api_key=api_key)

# Initialize Gemini client
model = genai.GenerativeModel('gemini-2.0-flash-lite-preview')

# Initialize the emotional validator
emotional_validator = EmotionalValidator()

# Session state for tracking story progress and user input
if "story_state" not in st.session_state:
    st.session_state.story_state = {
        "genre": None,
        "name": None,
        "pronouns": None,  # Add pronouns
        "age": None,      # Add age
        "current_emotion": None,
        "target_emotion": None,
        "summary": [],
        "turn_count": 0,
        "total_turns": 10, # Default to short
        "started": False,
        "character_mood": None,  # Track character's current mood (will be replaced by arc)
        "user_mood": None,      # Track user's current mood (will be replaced by arc)
        "last_user_input": None,  # Add field to store last user input
        "user_preferences": {
            "risk_taker": 0,       # -5 to 5 scale (cautious to adventurous)
            "optimism": 0,         # -5 to 5 scale (pessimistic to optimistic)
            "social": 0,           # -5 to 5 scale (solitary to social)
            "analytical": 0,       # -5 to 5 scale (intuitive to analytical)
            "fantasy_interest": 0, # -5 to 5 scale (realistic to fantastical)
            "introspective": 0     # -5 to 5 scale (action-oriented to introspective)
        },
        "character_mood_arc": {}, # Store character moods by turn
        "user_mood_arc": {},      # Store user moods by turn
        "validation_errors": {}   # Store validation errors by turn
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
    "fantasy": "https://images.unsplash.com/photo-1578662921789-ee37cd491478", # New fantasy image URL (a castle)
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

st.title("Woven: into your story")

# Only show the input form if the story hasn't started yet
if not st.session_state.story_state["started"]:
    # Default background for start screen
    set_background("https://images.unsplash.com/photo-1617396900799-f4e1a370e268") # New welcome page image URL (blurry orange/yellow)
    
    st.markdown("""
        <div class="story-text" style="font-size: 14px; margin-bottom: 20px;">
        **Notice:** Data, including story progress, character mood, user mood (as interpreted by the model), personality scores, and story summaries, is being collected from this application for research purposes aimed at improving AI narrative generation and emotional understanding. If you are interested in learning more about this research, please provide your email address below (optional). To opt out of data collection, please email duashmita@gmail.com with the name you used in the story.
        </div>
    """, unsafe_allow_html=True)

    with st.form(key="user_input_form"):
        name = st.text_input("What is your name?")
        pronouns = st.selectbox(
            "What are your pronouns?",
            ["they/them", "she/her", "he/him", "she/they", "he/they", "other"]
        )
        if pronouns == "other":
            pronouns = st.text_input("Please specify your pronouns")
        age = st.number_input("What is your age?", min_value=13, max_value=100, value=25)
        genre = st.selectbox("Choose your genre", list(GENRE_IMAGES.keys()))
        current_emotion = st.text_input("How do you feel right now?")
        target_emotion = st.text_input("What do you want to feel?")
        # Story length selection
        story_length = st.radio(
            "How long do you want your story to be?",
            ["Short (approx. 10 turns)", "Long (up to 17 turns, aims for target emotion)"],
            index=0,
            help="Select 'Long' for a better experience with emotional arc validation."
        )
        turns_map = {"Short (approx. 10 turns)": 10, "Long (up to 17 turns, Has better results)": 17}
        turns = turns_map[story_length]
        
        # Optional email input for research updates
        research_email = st.text_input("Optional: Your email if you'd like to know more about the research", key="research_email")
        
        submit_button = st.form_submit_button("Submit")
        
        if submit_button:
            if name and pronouns and age and genre and current_emotion and target_emotion:
                st.session_state.story_state.update({
                    "name": name,
                    "pronouns": pronouns,
                    "age": age,
                    "current_emotion": current_emotion,
                    "target_emotion": target_emotion,
                    "genre": genre,
                    "total_turns": turns,
                    "turn_count": 0,
                    "started": True,
                    "user_preferences": {
                        "risk_taker": 0,
                        "optimism": 0,
                        "social": 0,
                        "analytical": 0,
                        "fantasy_interest": 0,
                        "introspective": 0
                    },
                    "character_mood_arc": {},
                    "user_mood_arc": {},
                    "validation_errors": {}
                })
                # Clear any existing paragraphs when starting a new story
                st.session_state.story_paragraphs = []
                st.session_state.story_questions = []
                st.session_state.choice_patterns = []
                
                # Save research email if provided
                if research_email:
                    st.session_state.story_state["research_email"] = research_email
                    # Get the story_id and save email immediately
                    supabase = init_supabase()
                    result = supabase.table('stories').select('id').order('id', desc=True).limit(1).execute()
                    if result.data:
                        story_id = result.data[0]['id']
                        save_research_email(story_id, research_email)
                    st.info("Thank you for your interest! We have recorded your email.")

                st.rerun()
            else:
                st.error("Please fill out all fields before continuing.")

def openai_call(prompt):
    retries = 5
    base_wait = 2
    
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                st.warning(f"Rate limit details: {error_msg}")
                wait_time = base_wait * (2 ** attempt)
                st.warning(f"Attempt {attempt + 1}/{retries}. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                st.error(f"Error calling Gemini API: {error_msg}")
                return None
    
    st.error("Failed to get response after multiple retries. Please try again later.")
    return None

# Function to display personality scores
def display_personality_scores():
    """Display personality scores in a sidebar"""
    with st.sidebar:
        st.markdown("### Your Story Personality")
        preferences = st.session_state.story_state['user_preferences']
        
        # Create a container for the scores
        score_container = st.container()
        
        # Display each score with a progress bar
        for trait, score in preferences.items():
            # Convert trait name to display format
            display_name = trait.replace('_', ' ').title()
            # Normalize score to 0-100 range (from -5 to 5)
            normalized_score = ((score + 5) / 10) * 100
            
            # Create a progress bar with custom styling
            score_container.markdown(f"""
                <div style="margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span>{display_name}</span>
                        <span>{score}/5</span>
                    </div>
                    <div style="background-color: rgba(255, 255, 255, 0.1); height: 8px; border-radius: 4px;">
                        <div style="width: {normalized_score}%; height: 100%; background-color: #4CAF50; border-radius: 4px;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# Function to build prompt based on story state
def build_prompt(final=False):
    base_summary = ", ".join(st.session_state.story_state['summary'])
    name = st.session_state.story_state['name']
    pronouns = st.session_state.story_state['pronouns']
    age = st.session_state.story_state['age']
    genre = st.session_state.story_state['genre']
    current_emotion = st.session_state.story_state['current_emotion']
    target_emotion = st.session_state.story_state['target_emotion']
    turn_count = st.session_state.story_state['turn_count']
    total_turns = st.session_state.story_state['total_turns']
    character_mood = st.session_state.story_state['character_mood']
    user_mood = st.session_state.story_state['user_mood']
    last_user_input = st.session_state.story_state['last_user_input']
    
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
    
    # Create personality score string
    personality_scores = "\n".join([f"{trait.replace('_', ' ').title()}: {score}/5" for trait, score in preferences.items()])
    
    # Determine if fantasy elements should be introduced based on player choices
    use_fantasy = preferences['fantasy_interest'] > 0
    
    # Determine if we're approaching the final turns to prepare for the emotional breakthrough
    approaching_climax = (turn_count >= total_turns - 2) and not final

    # Add last user input to the prompt if it exists
    last_input_context = f"\nLast user response: {last_user_input}" if last_user_input else ""

    # Determine the current phase of the story
    story_phase = "beginning" if turn_count < total_turns // 3 else "middle" if turn_count < (total_turns * 2) // 3 else "climax"

    genre_reinforce = f"This is a {genre} story."

    # Define allowed emotions
    allowed_emotions = """
IMPORTANT - You must use ONLY these 10 emotions for character and user moods:
1. joy (happiness, delight)
2. sadness (grief, sorrow)
3. anger (rage, frustration)
4. fear (anxiety, terror)
5. trust (confidence, faith)
6. surprise (amazement, wonder)
7. anticipation (expectation, hope)
8. disgust (aversion, repulsion)
9. neutral (balanced, calm)
10. confusion (uncertainty, doubt)

When describing moods, use ONLY these exact emotion words."""

    if final:
        return f"""
{genre_reinforce}
Story so far: {base_summary}
You are {name} ({pronouns}), a {age}-year-old character.
World: {genre}.
The character began feeling {current_emotion} and has been experiencing a journey toward {target_emotion}.
The user is currently feeling {user_mood}, try to guide them towards {target_emotion}.{last_input_context}

Character insights based on their choices:
{personalization_string}

Current personality scores:
{personality_scores}

{allowed_emotions}

Write the FINAL part of the story:
- Create a powerful emotional breakthrough moment that finally allows the character to fully experience {target_emotion}
- This should be a specific, concrete event (not just an internal realization)
- The event should feel like the culmination of the character's journey
- Show how this event transforms the character's perspective
- Tailor the nature of this breakthrough to match the character's established preferences and tendencies
- Don't explicitly state the emotion - show it through the character's reactions, sensations, and thoughts
- Keep it short and powerful
- End with a sense of resolution or new beginning that feels earned
- Use simple yet powerful words
- Use the correct pronouns ({pronouns})
- Acknowledge and build upon the user's last response in the story

Structure:
- short paragraph
- ~~~~
- 20-word story summary
- ~~~~
- Current character mood: [MUST be one of the 10 allowed emotions]
- ~~~~
- Current user mood: [MUST be one of the 10 allowed emotions]
- ~~~~
- Updated personality scores: [list each score on a new line in the format "Trait Name: X/5"]
Example personality scores format:
Risk Taker: 3/5
Optimism: -2/5
Social: 1/5
Analytical: 4/5
Fantasy Interest: 0/5
Introspective: -1/5

IMPORTANT: Each personality score must be on its own line and follow the exact format "Trait Name: X/5" where X is a number between -5 and 5.
"""
    elif approaching_climax:
        return f"""
{genre_reinforce}
Story so far: {base_summary}
Main Character is {name} ({pronouns}), a {age}-year-old character.
World: {genre}.
The character began feeling {current_emotion} and is approaching a pivotal moment that will lead to experiencing {target_emotion}.
The user is currently feeling {user_mood}, try to guide them towards {target_emotion}.{last_input_context}

Character insights based on their choices:
{personalization_string}

Current personality scores:
{personality_scores}

{allowed_emotions}

Write the next part of the story:
- Set up the conditions for an emotional breakthrough in the next turn
- Create a situation that challenges the character's current perspective
- Use simple language for the story, simple and the kind of language that draws the user into the story.
- Plant the seeds for a significant event that will transform how they feel
- Don't rush the emotional change yet - build anticipation
- {'Include subtle fantasy elements if they enhance the emotional journey' if use_fantasy else 'Keep the narrative grounded in human experience with a touch of wonder'}
- Add meaningful dialogue that reveals something important
- Tailor this part to align with the character's established preferences and tendencies
- Use the correct pronouns ({pronouns})
- Acknowledge and build upon the user's last response in the story
- End with either:
  * A meaningful situation that forces the character to make a significant choice
  * A deep, personal question from another character that:
    - Is connected to the current situation
    - Helps the main character reflect on their journey
    - Reveals something important about their inner world
    - Feels natural in the conversation
    - Leads to self-discovery
    - Moves the story toward the emotional breakthrough

Structure:
- short paragraph
- ~~~~
- either a situation or a personal question that feels natural in the conversation
- ~~~~
- 20-word story summary
- ~~~~
- Current character mood: [MUST be one of the 10 allowed emotions]
- ~~~~
- Current user mood: [MUST be one of the 10 allowed emotions]
- ~~~~
- Updated personality scores: [list each score on a new line in the format "Trait Name: X/5"]
Example personality scores format:
Risk Taker: 3/5
Optimism: -2/5
Social: 1/5
Analytical: 4/5
Fantasy Interest: 0/5
Introspective: -1/5

IMPORTANT: Each personality score must be on its own line and follow the exact format "Trait Name: X/5" where X is a number between -5 and 5.
"""
    else:
        # Determine the type of interaction based on story phase
        if story_phase == "beginning":
            interaction_type = """
- End with either:
  * A light, engaging situation that introduces the world and characters
  * A simple question about preferences or observations
  * A choice between two interesting options
  * A chance to explore the environment
  * A casual conversation starter
  * A small challenge or opportunity
  * A moment of curiosity or wonder
  * A chance to show personality through action
  * A simple decision that reveals character
  * A basic interaction with another character"""
        elif story_phase == "middle":
            interaction_type = """
- End with either:
  * A situation that challenges the character's comfort zone
  * A meaningful choice with clear consequences
  * A conversation that reveals more about the character
  * A moment of connection with another character
  * A decision that affects the story's direction
  * A question that makes the character think
  * A small conflict or tension
  * A moment of growth or change
  * A situation that tests the character's values
  * A choice that reveals priorities"""
        else:  # climax phase
            interaction_type = """
- End with either:
  * A significant situation that forces deep reflection
  * A meaningful choice that reveals true character
  * A conversation that touches on core values
  * A moment that challenges beliefs
  * A decision that affects relationships
  * A question about personal growth
  * A situation that tests resolve
  * A moment of truth or realization
  * A choice that defines character
  * A question that leads to self-discovery"""

        return f"""
{genre_reinforce}
Story so far: {base_summary}
You are {name} ({pronouns}), a {age}-year-old character.
World: {genre}.
The character began feeling {current_emotion} and is on a journey that will gradually lead to feeling {target_emotion}.
The user is currently feeling {user_mood}, try to guide them towards {target_emotion}.{last_input_context}

Character insights based on their choices so far:
{personalization_string}

Current personality scores:
{personality_scores}

{allowed_emotions}

Write the next part of the story:
- Show subtle shifts in the character's emotional state through their perceptions and actions
- Don't explicitly mention the target emotion - create situations that move toward it indirectly
- Use simple language for the story, simple and the kind of language that draws the user into the story.
- Start with human characters in the first turn, only introducing fantasy elements if the player's choices suggest they want that.' if turn_count == 0 else ('Adjust the level of fantasy elements based on the character\'s preferences shown through their choices' if use_fantasy else 'Focus on human characters and real-world situations with authentic emotional depth.'
- Include meaningful dialogue that reveals character and advances the emotional journey
- Always act on user's prompt. Try to mirror the language they are using with the personality of the main character
- Tailor the scene to align with the character's established preferences and tendencies
- Use the correct pronouns ({pronouns}) throughout the story
- Acknowledge and build upon the user's last response in the story
{interaction_type}

Structure:
- short paragraph
- ~~~~
- either a situation or a question that feels natural in the conversation
- ~~~~
- 20-word story summary
- ~~~~
- Current character mood: [MUST be one of the 10 allowed emotions]
- ~~~~
- Current user mood: [MUST be one of the 10 allowed emotions]
- ~~~~
- Updated personality scores: [list each score on a new line in the format "Trait Name: X/5"]
Example personality scores format:
Risk Taker: 3/5
Optimism: -2/5
Social: 1/5
Analytical: 4/5
Fantasy Interest: 0/5
Introspective: -1/5

IMPORTANT: Each personality score must be on its own line and follow the exact format "Trait Name: X/5" where X is a number between -5 and 5.
"""

# Function to display emotional analytics
def display_emotional_analytics():
    """Display real-time analytics of emotional data and allow user validation"""
    # Only display analytics if the story is completed
    if not st.session_state.story_state.get("completed", False):
        return

    st.subheader("Emotional Journey Analytics")

    story_state = st.session_state.story_state
    character_mood_arc = story_state.get("character_mood_arc", {})
    user_mood_arc = story_state.get("user_mood_arc", {})
    validation_errors = story_state.get("validation_errors", {})
    target_emotion = story_state.get("target_emotion", "neutral").lower()
    total_turns = story_state.get("total_turns", 10) # Use total_turns for scaling ideal arc

    if not character_mood_arc and not user_mood_arc:
        st.error("No emotional data found for this story.")
        return

    # --- Prepare Data for Visualization ---

    # Define the 10 core emotions and their plotting order
    core_emotions = ['joy', 'anticipation', 'trust', 'surprise', 'neutral', 'confusion', 'fear', 'sadness', 'disgust', 'anger']
    emotion_to_num = {emotion: i for i, emotion in enumerate(core_emotions)}
    num_to_emotion = {i: emotion for i, emotion in enumerate(core_emotions)}

    # Create DataFrame for plotting
    plot_data = []
    all_turns = sorted(list(set(character_mood_arc.keys()) | set(user_mood_arc.keys())))

    for turn in all_turns:
        char_mood = character_mood_arc.get(turn)
        user_mood = user_mood_arc.get(turn)
        has_error = turn in validation_errors

        plot_data.append({
            'turn': turn,
            'character_mood': char_mood.lower() if char_mood else None,
            'user_mood': user_mood.lower() if user_mood else None,
            'character_mood_num': emotion_to_num.get(char_mood.lower() if char_mood else None, None),
            'user_mood_num': emotion_to_num.get(user_mood.lower() if user_mood else None, None),
            'has_error': has_error
        })

    df_plot = pd.DataFrame(plot_data).dropna(subset=['character_mood_num', 'user_mood_num'], how='all')
    df_plot = df_plot.sort_values('turn').reset_index(drop=True)

    if df_plot.empty:
        st.error("No valid mood data points to plot.")
        return

    # --- Generate Ideal Character Mood Arc Data ---
    ideal_arc_data = []
    # This is a simplified interpretation based on flexible phases and aiming for target emotion
    # It assumes a general progression towards the target emotion.
    # A more complex ideal arc would require more detailed rules.
    initial_mood = df_plot['character_mood'].iloc[0] if not df_plot.empty else 'neutral'

    for turn in all_turns:
        ideal_mood = initial_mood # Default
        # Simple logic: stay in initial category, move towards target category, reach target emotion
        initial_category = emotional_validator.emotion_categories.get(initial_mood, 'neutral')
        target_category = emotional_validator.emotion_categories.get(target_emotion, 'neutral')

        # Placeholder for more sophisticated ideal arc logic
        # For now, let's just aim to show a general trend towards the target emotion's 'num' value
        ideal_mood_num = emotion_to_num.get(initial_mood, emotion_to_num.get('neutral'))

        # Simple linear progression towards target emotion's numerical value across turns
        if len(all_turns) > 1:
            initial_num = emotion_to_num.get(initial_mood, emotion_to_num.get('neutral'))
            target_num = emotion_to_num.get(target_emotion, emotion_to_num.get('neutral'))
            # Interpolate linearly
            ideal_mood_num = initial_num + (target_num - initial_num) * (turn / (max(all_turns) if max(all_turns) > 0 else 1))
            # Find the closest emotion number
            closest_num = min(num_to_emotion.keys(), key=lambda x:abs(x - ideal_mood_num))
            ideal_mood = num_to_emotion.get(closest_num)

        ideal_arc_data.append({'turn': turn, 'ideal_mood_num': emotion_to_num.get(ideal_mood, emotion_to_num.get('neutral'))})

    df_ideal = pd.DataFrame(ideal_arc_data).sort_values('turn').reset_index(drop=True)

    # --- Plotting ---
    import plotly.graph_objects as go

    fig = go.Figure()

    # Character Mood Trace
    fig.add_trace(go.Scatter(
        x=df_plot['turn'],
        y=df_plot['character_mood_num'],
        mode='lines+markers',
        name='Character Mood',
        text=df_plot['character_mood'].str.capitalize(),
        marker=dict(
            color=df_plot['has_error'].apply(lambda x: 'red' if x else 'blue'),
            size=10
        ),
        hovertemplate='Character: %{text}<br>Turn: %{x}<br>Error: %{customdata}<extra></extra>',
        customdata=df_plot['turn'].apply(lambda turn: validation_errors.get(turn, 'None')) # Add error message to hover
    ))

    # User Mood Trace
    fig.add_trace(go.Scatter(
        x=df_plot['turn'],
        y=df_plot['user_mood_num'],
        mode='lines+markers',
        name='User Mood (Model)',
        text=df_plot['user_mood'].str.capitalize(),
        marker=dict(color='green', size=10),
        hovertemplate='User: %{text}<br>Turn: %{x}<extra></extra>'
    ))

    # Ideal Character Mood Trace
    fig.add_trace(go.Scatter(
        x=df_ideal['turn'],
        y=df_ideal['ideal_mood_num'],
        mode='lines',
        name='Ideal Character Mood (Conceptual)',
        line=dict(color='gray', dash='dot'),
        hovertemplate='Ideal: %{y}<br>Turn: %{x}<extra></extra>'
    ))

    # Update y-axis to show emotion names
    fig.update_layout(
        yaxis=dict(
            tickvals=list(num_to_emotion.keys()),
            ticktext=[emotion.capitalize() for emotion in num_to_emotion.values()]
        ),
        title='Emotional Progression and Validation',
        xaxis_title='Turn Number',
        yaxis_title='Mood',
        hovermode='closest'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display validation errors separately
    if validation_errors:
        st.markdown("**Validation Errors:**")
        for turn, error in validation_errors.items():
            st.error(f"Turn {turn + 1}: {error}")

    # Keep other analytics for now
    # --- PERSONALITY CHANGES ---
    try:
        if story_state.get("user_preferences") and len(story_state["character_mood_arc"]) > 1:
             # Reconstruct personality score history from session state or saved data if available
             # For now, we only have the final preferences in session state, need to save history per turn
             # Skipping personality chart for now until history is saved.
             pass # Placeholder

    except Exception as e:
         st.warning(f"Could not display personality changes: {str(e)}")

    # --- STORY PHASES ---
    try:
        if character_mood_arc:
             phase_counts = pd.Series([emotional_validator.get_phase_for_turn(turn, total_turns) for turn in character_mood_arc.keys()]).value_counts()
             if not phase_counts.empty:
                  st.markdown("**Story Phases:**")
                  st.bar_chart(phase_counts)
             else:
                 st.info("No story phase data to display.")

    except Exception as e:
         st.warning(f"Could not display story phases: {str(e)}")

# Function to play a turn of the story
def play_turn(final=False):
    """Play a single turn of the story"""
    if "story_state" not in st.session_state:
        st.error("Please start a new story first!")
        return False

    story_state = st.session_state.story_state
    current_turn = story_state["turn_count"]
    total_turns = story_state["total_turns"]
    
    # Determine if this turn should be final based on reaching target emotion (for Long stories)
    is_final_turn = final or (story_state.get("story_length_option") == "Long (up to 17 turns, aims for target emotion)" and story_state.get("character_mood", "").lower() == story_state["target_emotion"].lower() and current_turn >= story_state["total_turns"] // 2)

    # Build the prompt
    prompt = build_prompt(final=is_final_turn)
    raw_response = openai_call(prompt)
    
    if raw_response:
        # Split response into parts, handling potential missing delimiters
        parts = raw_response.split("~~~~")
        
        # Ensure we have all parts, if not, create empty defaults
        while len(parts) < 6:
            parts.append("")
        
        story_output = parts[0].strip()
        question = parts[1].strip() if parts[1].strip() else "What are you feeling in this moment?"
        summary = parts[2].strip()
        character_mood = parts[3].strip().replace("Current character mood: ", "").strip()
        user_mood = parts[4].strip().replace("Current user mood: ", "").strip()
        personality_scores_text = parts[5].strip().replace("Updated personality scores:", "").strip()

        # Store paragraph and question in session state
        st.session_state.story_paragraphs.append(story_output)
        if not is_final_turn:
            st.session_state.story_questions.append(question)

        # --- Data Collection and Validation ---        
        # Store moods in the arc dictionaries
        st.session_state.story_state['character_mood_arc'][current_turn] = character_mood
        st.session_state.story_state['user_mood_arc'][current_turn] = user_mood

        # Parse personality scores
        parsed_personality_scores = st.session_state.story_state['user_preferences'].copy() # Start with existing
        try:
            for line in personality_scores_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    trait, score = line.split(':', 1)
                    trait = trait.strip().lower().replace(' ', '_')
                    try:
                        score = int(score.strip().split('/')[0])
                        if trait in parsed_personality_scores:
                            parsed_personality_scores[trait] = score
                    except ValueError:
                        print(f"Debug: Could not parse personality score for line: {line}")
        except Exception as e:
             print(f"Debug: Error parsing personality scores: {e}\nRaw scores: {personality_scores_text}")
        
        # Update session state personality scores
        st.session_state.story_state['user_preferences'] = parsed_personality_scores

        # Validate the character turn and emotional progression
        validation_error = emotional_validator.validate_turn(
            turn_number=current_turn,
            character_mood_arc=st.session_state.story_state['character_mood_arc'],
            # We will pass the whole arc to the validator now
            story_phase="beginning" if current_turn < total_turns // 3 else "middle" if current_turn < (total_turns * 2) // 3 else "climax",
            personality_scores=list(st.session_state.story_state['user_preferences'].values()),
            is_final=is_final_turn
        )
        
        if validation_error:
            st.session_state.story_state['validation_errors'][current_turn] = validation_error
            st.warning(f"Validation Warning (Turn {current_turn + 1}): {validation_error}")

        # Update summary and turn count
        if summary:
            st.session_state.story_state['summary'].append(summary)
        st.session_state.story_state['turn_count'] += 1
        
        # Collect emotional data for this turn (will be saved later or all at once at the end)
        # For now, just focus on saving the arc and errors in session state

        # Set completed flag if it's the final turn
        if is_final_turn:
             st.session_state.story_state["completed"] = True

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
    
    # If we've reached the end, play the final turn or complete
    if st.session_state.story_state["turn_count"] >= st.session_state.story_state["total_turns"] or st.session_state.story_state.get("completed", False):
        if "completed" not in st.session_state.story_state:
             # Mark as completed and play final turn if not already final
            st.session_state.story_state["completed"] = True
            if st.session_state.story_state["turn_count"] < st.session_state.story_state["total_turns"]:
                 play_turn(final=True)
            st.rerun()  # Rerun to show the final paragraph and analytics
        else:
            # Show completion message and options
            st.success("🌟 Story complete!")
            
            # Create columns for the buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Leave Feedback"): # Assuming this button navigates away or opens a modal
                    # Replace with actual feedback link or modal trigger
                    st.markdown('<meta http-equiv="refresh" content="0;url=https://7umut23yse8.typeform.com/to/bSuQeV0L">', unsafe_allow_html=True)
            
            with col2:
                if st.button("Start a new story"):
                    # Reset all session state to start a new story
                    for key in st.session_state.keys():
                        del st.session_state[key]
                    st.rerun()

    # Continue with the next turn after user input
    elif st.session_state.story_state["turn_count"] > 0:
        # Display the most recent question
        if len(st.session_state.story_questions) > 0:
            st.markdown(f'<div class="story-question">{st.session_state.story_questions[-1]}</div>', unsafe_allow_html=True)
            user_response = st.text_input("Your response", key=f"response_{st.session_state.story_state['turn_count']}", placeholder="Share your thoughts and feelings...", label_visibility="collapsed")
            if user_response:
                # Store the user's response
                st.session_state.story_state['last_user_input'] = user_response

                # Analyze the user's response to update preferences
                analyze_user_choice(user_response, st.session_state.story_questions[-1])

                # Add the response to the story summary
                st.session_state.story_state['summary'].append(f"{st.session_state.story_state['name']} reflected: {user_response}")

                # Generate next paragraph
                turn_complete = play_turn()
                st.rerun()

    # Display personality scores
    display_personality_scores()
    
    # Add analytics if story is completed
    if st.session_state.story_state.get("completed", False):
        display_emotional_analytics()

# Close main app container
st.markdown('</div>', unsafe_allow_html=True)