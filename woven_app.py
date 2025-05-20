import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import json
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

def init_supabase():
    """Initialize Supabase client"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

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
        "total_turns": 5,
        "started": False,
        "character_mood": None,  # Track character's current mood
        "user_mood": None,      # Track user's current mood
        "last_user_input": None,  # Add field to store last user input
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
            ["Short", "Medium", "Long"],
            index=1
        )
        turns_map = {"Short": 5, "Medium": 10, "Long": 15}
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
                    "started": True
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
- Use the correct pronouns ({pronouns}) throughout the story
- Acknowledge and build upon the user's last response in the story

Structure:
- short paragraph
- ~~~~
- 20-word story summary
- ~~~~
- Current character mood: [describe the character's emotional state in one word, using the emotional wheel]
- ~~~~
- Current user mood: [describe how the user might be feeling based on their choices in one word, using the emotional wheel]
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

Write the next part of the story:
- Set up the conditions for an emotional breakthrough in the next turn
- Create a situation that challenges the character's current perspective
- Use simple language for the story, simple and the kind of language that draws the user into the story.
- Plant the seeds for a significant event that will transform how they feel
- Don't rush the emotional change yet - build anticipation
- {'Include subtle fantasy elements if they enhance the emotional journey' if use_fantasy else 'Keep the narrative grounded in human experience with a touch of wonder'}
- Add meaningful dialogue that reveals something important
- Tailor this part to align with the character's established preferences and tendencies
- Use the correct pronouns ({pronouns}) throughout the story
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
- Current character mood: [describe the character's emotional state in one word, using the emotional wheel]
- ~~~~
- Current user mood: [describe how the user might be feeling based on their choices in one word, using the emotional wheel]
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
- Current character mood: [describe the character's emotional state in one word, using the emotional wheel]
- ~~~~
- Current user mood: [describe how the user might be feeling based on their choices in one word, using the emotional wheel]
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

# Add this after the imports
def save_emotional_data(story_data):
    """Save emotional data to Supabase"""
    try:
        supabase = init_supabase()
        
        # If this is the first turn, create a new story entry
        if story_data["turn_number"] == 1:
            story_meta = {
                "name": st.session_state.story_state["name"],
                "genre": st.session_state.story_state["genre"],
                "total_turns": st.session_state.story_state["total_turns"],
                "start_time": datetime.now().isoformat(),
                "research_email": st.session_state.story_state.get("research_email")
            }
            try:
                result = supabase.table('stories').insert(story_meta).execute()
                if not result.data:
                    st.error("Failed to create story entry. Please check your database connection.")
                    return
                story_id = result.data[0]['id']
            except Exception as e:
                st.error(f"Error creating story entry: {str(e)}")
                return
        else:
            try:
                # Get the latest story_id
                result = supabase.table('stories').select('id').order('id', desc=True).limit(1).execute()
                if not result.data:
                    st.error("Could not find story ID. Please check your database connection.")
                    return
                story_id = result.data[0]['id']
            except Exception as e:
                st.error(f"Error retrieving story ID: {str(e)}")
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
        
        # Insert emotional data
        try:
            supabase.table('emotional_data').insert(emotional_data).execute()
        except Exception as e:
            st.error(f"Error saving emotional data: {str(e)}")
            return
            
    except Exception as e:
        st.error(f"Unexpected error in save_emotional_data: {str(e)}")
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

def display_emotional_analytics():
    """Display real-time analytics of emotional data and allow user validation"""
    if st.session_state.story_state.get("completed", False):
        supabase = init_supabase()
        result = supabase.table('emotional_data')\
            .select('*, stories(name, genre)')\
            .eq('stories.name', st.session_state.story_state["name"])\
            .order('turn_number')\
            .execute()
        if result.data:
            df = pd.DataFrame(result.data)
            st.subheader("Emotional Journey Analytics")
            mood_wheel = [
                'ecstatic', 'joyful', 'happy', 'content', 'calm', 'relieved', 'curious', 'interested', 'intrigued',
                'neutral', 'weary', 'sad', 'angry', 'afraid', 'disgusted', 'surprised', 'trusting', 'anticipating'
            ]
            mood_to_num = {mood: i for i, mood in enumerate(mood_wheel)}
            num_to_mood = {i: mood for i, mood in enumerate(mood_wheel)}
            
            # Filter out None values and clean up mood strings
            df = df[df['character_mood'].notna() & df['user_mood'].notna()]
            
            # Clean up mood strings by removing any extra text and standardizing case
            def clean_mood(mood):
                if not isinstance(mood, str):
                    return None
                # Remove any text after "Current" or "Updated"
                mood = mood.split('Current')[0].split('Updated')[0].strip()
                # Remove any personality scores
                mood = mood.split('Risk taker')[0].strip()
                # Convert to lowercase for consistency
                mood = mood.lower()
                # Only keep if it's a valid mood
                return mood if mood in mood_wheel else None
            
            df['character_mood'] = df['character_mood'].apply(clean_mood)
            df['user_mood'] = df['user_mood'].apply(clean_mood)
            
            # Remove rows where moods couldn't be cleaned
            df = df[df['character_mood'].notna() & df['user_mood'].notna()]
            
            # Map moods to numbers for plotting
            df['character_mood_num'] = df['character_mood'].map(lambda m: mood_to_num.get(m, None))
            df['user_mood_num'] = df['user_mood'].map(lambda m: mood_to_num.get(m, None))

            # --- MOOD ARC VALIDATION ---
            st.markdown('#### Mood Arc Validation')
            
            # Define significant mood changes (e.g., positive to negative, or major intensity changes)
            def is_significant_change(mood1, mood2):
                if not mood1 or not mood2:
                    return False
                # Get mood indices
                idx1 = mood_wheel.index(mood1)
                idx2 = mood_wheel.index(mood2)
                # Consider it significant if it's more than 3 positions away on the wheel
                return abs(idx1 - idx2) > 3
            
            # Filter for significant mood changes
            filtered_character_moods = []
            last_char_mood = None
            for mood in df['character_mood']:
                if not last_char_mood or is_significant_change(last_char_mood, mood):
                    filtered_character_moods.append(mood.capitalize())
                    last_char_mood = mood
                    
            filtered_user_moods = []
            last_user_mood = None
            for mood in df['user_mood']:
                if not last_user_mood or is_significant_change(last_user_mood, mood):
                    filtered_user_moods.append(mood.capitalize())
                    last_user_mood = mood

            # Ensure we have at least the first and last mood
            if filtered_character_moods and df['character_mood'].iloc[-1] not in filtered_character_moods:
                filtered_character_moods.append(df['character_mood'].iloc[-1].capitalize())
            if filtered_user_moods and df['user_mood'].iloc[-1] not in filtered_user_moods:
                filtered_user_moods.append(df['user_mood'].iloc[-1].capitalize())

            character_arc_display = ' → '.join(filtered_character_moods)
            user_arc_display = ' → '.join(filtered_user_moods)
            
            st.markdown(f"**Character Mood Arc:** {character_arc_display}")
            st.markdown(f"**Your Mood Arc (Model Interpretation):** {user_arc_display}")
            
            with st.form(key='mood_arc_validation_form'):
                st.markdown('**Does this sequence of moods feel correct?**')
                arc_right = st.radio('Select validation:', ['Yes', 'No'], key='arc_right', label_visibility="collapsed")
                comments = st.text_area('Optional comments:', key='arc_validation_comments')
                submit_validation = st.form_submit_button('Submit Validation')
                
                if submit_validation:
                    # Get the story_id
                    story_result = supabase.table('stories')\
                        .select('id')\
                        .eq('name', st.session_state.story_state["name"])\
                        .execute()
                    if story_result.data:
                        story_id = story_result.data[0]['id']
                        # Save validation data
                        save_validation_data(story_id, arc_right, comments)
                        if arc_right == 'No':
                            st.info(f'Thank you for your feedback! Your comments: {comments}')
                        else:
                            st.success('Great! Your validation helps us improve.')

            # --- MOOD PROGRESSION PLOT ---
            tab1, tab2, tab3 = st.tabs(["Mood Progression", "Personality Changes", "Story Phases"])
            with tab1:
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['turn_number'],
                    y=df['character_mood_num'],
                    mode='lines+markers',
                    name='Character Mood',
                    text=df['character_mood'],
                    hovertemplate='Character: %{text}<br>Turn %{x}'
                ))
                fig.add_trace(go.Scatter(
                    x=df['turn_number'],
                    y=df['user_mood_num'],
                    mode='lines+markers',
                    name='User Mood (Model)',
                    text=df['user_mood'],
                    hovertemplate='User: %{text}<br>Turn %{x}'
                ))
                fig.update_yaxes(
                    tickvals=list(num_to_mood.keys()),
                    ticktext=list(num_to_mood.values())
                )
                fig.update_layout(title='Mood Progression', xaxis_title='Turn', yaxis_title='Mood')
                st.plotly_chart(fig, use_container_width=True)
            with tab2:
                personality_scores = pd.json_normalize(df['personality_scores'].apply(json.loads))
                st.line_chart(personality_scores)
            with tab3:
                phase_counts = df['story_phase'].value_counts()
                st.bar_chart(phase_counts)
            # --- PROLOG EXPORT ---
            st.markdown('#### Download for Prolog Validation')
            prolog_facts = []
            for i, row in df.iterrows():
                prolog_facts.append(f"turn({row['turn_number']}, {str(row['character_mood']).lower()}, {str(row['story_phase']).lower()}).")
            prolog_export = '\n'.join(prolog_facts)
            st.download_button(
                label="Download Character Mood Progression for Prolog",
                data=prolog_export,
                file_name=f"character_mood_progression_{st.session_state.story_state['name']}.pl",
                mime="text/plain"
            )
            st.info('''To validate the character mood arc, load this file in SWI-Prolog along with your validator and run:\n?- validate_character_arc.\n''')

def save_research_email(story_id, email):
    """Save research email to Supabase"""
    supabase = init_supabase()
    supabase.table('stories').update({"research_email": email}).eq("id", story_id).execute()

# Function to play a turn of the story
def play_turn(final=False):
    prompt = build_prompt(final=final)
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
        personality_scores = parts[5].strip().replace("Updated personality scores:", "").strip()
        
        # Parse and update personality scores with more robust error handling
        try:
            for line in personality_scores.split('\n'):
                line = line.strip()
                if ':' in line:
                    trait, score = line.split(':', 1)
                    trait = trait.strip().lower().replace(' ', '_')
                    try:
                        score = int(score.strip().split('/')[0])
                        if trait in st.session_state.story_state['user_preferences']:
                            st.session_state.story_state['user_preferences'][trait] = score
                    except ValueError:
                        continue  # Skip invalid score formats
        except Exception as e:
            # Log the error but don't show it to the user
            print(f"Personality score parsing error: {e}\nRaw scores: {personality_scores}")
            # Keep existing personality scores instead of showing an error

        # Store paragraph and question in session state
        st.session_state.story_paragraphs.append(story_output)
        if not final:
            st.session_state.story_questions.append(question)

        # Only update moods if there was user input (i.e., not the first turn)
        if st.session_state.story_state['last_user_input'] is not None:
            st.session_state.story_state['character_mood'] = character_mood
            st.session_state.story_state['user_mood'] = user_mood

        if summary:
            st.session_state.story_state['summary'].append(summary)
        st.session_state.story_state['turn_count'] += 1
        
        # Collect emotional data for this turn
        emotional_data = {
            "turn_number": st.session_state.story_state['turn_count'],
            "character_mood": character_mood if st.session_state.story_state['last_user_input'] is not None else None,
            "user_mood": user_mood if st.session_state.story_state['last_user_input'] is not None else None,
            "story_summary": summary,
            "question": question,
            "personality_scores": st.session_state.story_state['user_preferences'].copy(),
            "story_phase": "beginning" if st.session_state.story_state['turn_count'] < st.session_state.story_state['total_turns'] // 3 
                          else "middle" if st.session_state.story_state['turn_count'] < (st.session_state.story_state['total_turns'] * 2) // 3 
                          else "climax",
            "is_final": final
        }
        
        # Save emotional data
        save_emotional_data(emotional_data)
        
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
        if "completed" not in st.session_state.story_state:
            # Play final turn and mark as completed
            play_turn(final=True)
            st.session_state.story_state["completed"] = True
            st.rerun()  # Rerun to show the final paragraph
        else:
            # Show completion message and options
            st.success("🌟 Story complete!")
            
            # Create columns for the buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Leave Feedback"):
                    st.markdown('<meta http-equiv="refresh" content="0;url=https://7umut23yse8.typeform.com/to/bSuQeV0L">', unsafe_allow_html=True)
            
            with col2:
                if st.button("Start a new story"):
                    # Reset all session state
                    st.session_state.story_state = {
                        "genre": None,
                        "name": None,
                        "pronouns": None,
                        "age": None,
                        "current_emotion": None,
                        "target_emotion": None,
                        "summary": [],
                        "turn_count": 0,
                        "total_turns": 5,
                        "started": False,
                        "character_mood": None,
                        "user_mood": None,
                        "last_user_input": None,
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