from flask import Flask, render_template, request, redirect, url_for, session
import openai
import google.generativeai as genai
import os
from datetime import datetime
import json
from emotional_validator import EmotionalValidator
from supabase import create_client, Client
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize Gemini client
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-lite-preview')

# Initialize the emotional validator
emotional_validator = EmotionalValidator()

def init_supabase():
    """Initialize Supabase client"""
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        client = create_client(url, key)
        return client
    except Exception as e:
        print(f"Error initializing Supabase: {str(e)}")
        raise

@app.route('/')
def index():
    # Add default test values for development
    if os.getenv('FLASK_ENV') == 'development':
        return render_template('index.html', 
                            story_started=False,
                            default_values={
                                'name': 'Test User',
                                'pronouns': 'they/them',
                                'age': 25,
                                'genre': 'fantasy',
                                'current_emotion': 'neutral',
                                'target_emotion': 'joy',
                                'model_choice': 'gemini',
                                'story_length': 'short',
                                'research_email': 'test@example.com'
                            })
    return render_template('index.html', story_started=False)

@app.route('/start_story', methods=['POST'])
def start_story():
    try:
        # Get form data
        name = request.form.get('name')
        pronouns = request.form.get('pronouns')
        if pronouns == 'other':
            pronouns = request.form.get('custom_pronouns')
        age = int(request.form.get('age'))
        genre = request.form.get('genre')
        current_emotion = request.form.get('current_emotion')
        target_emotion = request.form.get('target_emotion')
        model_choice = request.form.get('model_choice')
        story_length = request.form.get('story_length')
        research_email = request.form.get('research_email')

        # Validate required fields
        if not all([name, pronouns, age, genre, current_emotion, target_emotion, model_choice, story_length]):
            return render_template('index.html', 
                                story_started=False, 
                                error="Please fill in all required fields")

        # Initialize story state with proper types
        session['story_state'] = {
            'name': str(name),
            'pronouns': str(pronouns),
            'age': int(age),
            'genre': str(genre),
            'current_emotion': str(current_emotion),
            'target_emotion': str(target_emotion),
            'model_choice': str(model_choice),
            'total_turns': int(17 if story_length == 'long' else 10),
            'turn_count': 0,
            'started': True,
            'user_preferences': {
                'risk_taker': 0,
                'optimism': 0,
                'social': 0,
                'analytical': 0,
                'fantasy_interest': 0,
                'introspective': 0
            },
            'character_mood_arc': {},
            'user_mood_arc': {},
            'validation_errors': {},
            'summary': []
        }

        # Initialize story paragraphs and questions
        session['story_paragraphs'] = []
        session['story_questions'] = []
        session['choice_patterns'] = []
        session.modified = True

        # Save research email if provided
        if research_email:
            session['story_state']['research_email'] = str(research_email)
            try:
                supabase = init_supabase()
                result = supabase.table('stories').select('id').order('id', desc=True).limit(1).execute()
                if result.data:
                    story_id = result.data[0]['id']
                    save_research_email(story_id, research_email)
            except Exception as e:
                print(f"Error saving research email: {str(e)}")

        # Start the first turn
        success = play_turn()
        if not success:
            return render_template('index.html', 
                                story_started=False, 
                                error="Failed to generate story. Please try again.")

        # Return the story view
        return render_template('index.html',
                            story_started=True,
                            story_state=session['story_state'],
                            story_paragraphs=session['story_paragraphs'],
                            story_questions=session['story_questions'],
                            current_question=session['story_questions'][-1] if session['story_questions'] else None,
                            story_completed=session['story_state'].get('completed', False))

    except Exception as e:
        print(f"Error in start_story: {str(e)}")
        return render_template('index.html', 
                            story_started=False, 
                            error="An error occurred. Please try again.")

@app.route('/submit_response', methods=['POST'])
def submit_response():
    try:
        user_response = request.form.get('user_response')
        if not user_response:
            # If no response, re-render with error but preserve state
            story_state = session.get('story_state', {}) # Get existing state or empty dict
            story_paragraphs = session.get('story_paragraphs', [])
            story_questions = session.get('story_questions', [])
            current_question = story_questions[-1] if story_questions else None
            story_completed = story_state.get('completed', False)
            return render_template('index.html', 
                                story_started=True,
                                story_state=story_state,
                                story_paragraphs=story_paragraphs,
                                story_questions=story_questions,
                                current_question=current_question,
                                story_completed=story_completed,
                                error="Please provide a response")
        
        # Get current state
        story_state = session.get('story_state', {}) 
        story_paragraphs = session.get('story_paragraphs', [])
        story_questions = session.get('story_questions', [])

        # Store the user's response
        story_state['last_user_input'] = user_response

        # Analyze the user's response to update preferences
        # Ensure there is a previous question before analyzing
        if story_questions:
             analyze_user_choice(user_response, story_questions[-1])

        # Add the user's response to the paragraphs to be displayed
        # Using a simple <p> tag with a class for potential future styling
        story_paragraphs.append(f"<div class=\"user-response\"><b>Your response:</b> {user_response}</div>")
        
        # Add the response to the story summary (optional, keeping summary concise is better)
        # story_state['summary'].append(f"{story_state.get('name', 'You')} responded: {user_response}")

        # Update session state before calling play_turn
        session['story_state'] = story_state
        session['story_paragraphs'] = story_paragraphs
        # session['story_questions'] will be updated in play_turn
        session.modified = True # Mark session as modified

        # Generate next paragraph
        success = play_turn()

        # Re-fetch potentially updated state after play_turn
        story_state = session.get('story_state', {}) 
        story_paragraphs = session.get('story_paragraphs', [])
        story_questions = session.get('story_questions', [])
        current_question = story_questions[-1] if story_questions else None
        story_completed = story_state.get('completed', False)

        if not success:
            return render_template('index.html', 
                                story_started=True,
                                story_state=story_state,
                                story_paragraphs=story_paragraphs,
                                story_questions=story_questions,
                                current_question=current_question,
                                story_completed=story_completed, 
                                error="Failed to generate next part of the story. Please try again.")

        return render_template('index.html',
                            story_started=True,
                            story_state=story_state,
                            story_paragraphs=story_paragraphs,
                            story_questions=story_questions,
                            current_question=current_question,
                            story_completed=story_completed)
    except Exception as e:
        print(f"Error in submit_response: {str(e)}")
        # Re-fetch potentially updated state even on error
        story_state = session.get('story_state', {}) 
        story_paragraphs = session.get('story_paragraphs', [])
        story_questions = session.get('story_questions', [])
        current_question = story_questions[-1] if story_questions else None
        story_completed = story_state.get('completed', False)
        return render_template('index.html', 
                            story_started=True,
                            story_state=story_state,
                            story_paragraphs=story_paragraphs,
                            story_questions=story_questions,
                            current_question=current_question,
                            story_completed=story_completed, 
                            error="An error occurred. Please try again.")

@app.route('/reset_story')
def reset_story():
    session.clear()
    return redirect(url_for('index'))

def play_turn(final=False):
    """Play a single turn of the story"""
    try:
        story_state = session.get('story_state')
        if not story_state:
            print("Debug: No story state found in session")
            return False

        current_turn = int(story_state['turn_count'])
        total_turns = int(story_state['total_turns'])
        
        # Check if we've reached the maximum number of turns
        if current_turn >= total_turns:
            story_state["completed"] = True
            session['story_state'] = story_state
            session.modified = True
            return True

        # Determine if this turn should be final
        is_final_turn = final or (
            story_state.get('story_length') == 'long' and
            story_state.get('character_mood', '').lower() == story_state['target_emotion'].lower() and
            current_turn >= total_turns // 2
        )

        # Build the prompt
        prompt = build_prompt(final=is_final_turn)
        raw_response = openai_call(prompt, model_choice=story_state['model_choice'])
        
        if not raw_response:
            print("Debug: No response from API")
            return False

        # Split response into parts
        parts = raw_response.split('~~~~')
        while len(parts) < 6:
            parts.append('')
        
        # Extract and clean each part
        story_output = parts[0].strip()
        question = parts[1].strip() if parts[1].strip() else "What are you feeling in this moment?"
        summary = parts[2].strip()
        character_mood = parts[3].strip().replace("Current character mood:", "").strip()
        user_mood = parts[4].strip().replace("Current user mood:", "").strip()
        personality_scores_text = parts[5].strip().replace("Updated personality scores:", "").strip()

        # Validate required parts
        if not all([story_output, character_mood, user_mood]):
            print("Debug: Missing required story parts")
            return False

        # Store paragraph and question
        if 'story_paragraphs' not in session:
            session['story_paragraphs'] = []
        if 'story_questions' not in session:
            session['story_questions'] = []

        session['story_paragraphs'].append(story_output)
        if not is_final_turn:
            session['story_questions'].append(question)

        # Store moods
        story_state['character_mood_arc'][str(current_turn)] = character_mood
        story_state['user_mood_arc'][str(current_turn)] = user_mood

        # Parse personality scores
        parsed_personality_scores = {}
        try:
            for line in personality_scores_text.split('\n'):
                line = line.strip()
                if ':' in line:
                    trait, score = line.split(':', 1)
                    trait = trait.strip().lower().replace(' ', '_')
                    try:
                        score = int(score.strip().split('/')[0])
                        parsed_personality_scores[trait] = score
                    except ValueError:
                        print(f"Debug: Could not parse personality score for line: {line}")
        except Exception as e:
            print(f"Debug: Error parsing personality scores: {e}\nRaw scores: {personality_scores_text}")
        
        # Update personality scores, ensuring all values are integers
        for trait in story_state['user_preferences']:
            story_state['user_preferences'][trait] = int(parsed_personality_scores.get(trait, 0))

        # Update summary and turn count
        if summary:
            story_state['summary'].append(summary)
        story_state['turn_count'] = current_turn + 1
        
        # Set completed flag if it's the final turn
        if is_final_turn or story_state['turn_count'] >= total_turns:
            story_state["completed"] = True

        # Convert all numeric values to integers
        story_state['total_turns'] = int(story_state['total_turns'])
        story_state['age'] = int(story_state['age'])

        # Save the updated session
        session['story_state'] = story_state
        session.modified = True
        return True

    except Exception as e:
        print(f"Debug: Error in play_turn: {str(e)}")
        return False

def build_prompt(final=False):
    """Build the prompt for the AI model"""
    story_state = session['story_state']
    base_summary = ", ".join(story_state['summary'])
    
    # Build personalization string based on user preferences
    personalization = []
    preferences = story_state['user_preferences']
    
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
    
    personalization_string = " ".join(personalization)
    
    # Create personality score string
    personality_scores = "\n".join([f"{trait.replace('_', ' ').title()}: {score}/5" for trait, score in preferences.items()])
    
    # Determine if fantasy elements should be introduced
    use_fantasy = preferences['fantasy_interest'] > 0
    
    # Add last user input to the prompt if it exists
    last_input_context = f"\nLast user response: {story_state.get('last_user_input', '')}" if story_state.get('last_user_input') else ""

    # Determine the current phase of the story
    story_phase = "beginning" if story_state['turn_count'] < story_state['total_turns'] // 3 else "middle" if story_state['turn_count'] < (story_state['total_turns'] * 2) // 3 else "climax"

    genre_reinforce = f"This is a {story_state['genre']} story."

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
You are {story_state['name']} ({story_state['pronouns']}), a {story_state['age']}-year-old character.
World: {story_state['genre']}.
The character began feeling {story_state['current_emotion']} and has been experiencing a journey toward {story_state['target_emotion']}.
The user is currently feeling {story_state.get('user_mood', 'neutral')}, try to guide them towards {story_state['target_emotion']}.{last_input_context}

Character insights based on their choices:
{personalization_string}

Current personality scores:
{personality_scores}

{allowed_emotions}

Write the FINAL part of the story:
- Create a powerful emotional breakthrough moment that finally allows the character to fully experience {story_state['target_emotion']}
- This should be a specific, concrete event (not just an internal realization)
- The event should feel like the culmination of the character's journey
- Show how this event transforms the character's perspective
- Tailor the nature of this breakthrough to match the character's established preferences and tendencies
- Don't explicitly state the emotion - show it through the character's reactions, sensations, and thoughts
- Keep it short and powerful
- End with a sense of resolution or new beginning that feels earned
- Use simple yet powerful words
- Use the correct pronouns ({story_state['pronouns']})
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
"""
    else:
        return f"""
{genre_reinforce}
Story so far: {base_summary}
You are {story_state['name']} ({story_state['pronouns']}), a {story_state['age']}-year-old character.
World: {story_state['genre']}.
The character began feeling {story_state['current_emotion']} and is on a journey that will gradually lead to feeling {story_state['target_emotion']}.
The user is currently feeling {story_state.get('user_mood', 'neutral')}, try to guide them towards {story_state['target_emotion']}.{last_input_context}

Character insights based on their choices:
{personalization_string}

Current personality scores:
{personality_scores}

{allowed_emotions}

Write the next part of the story:
- Show subtle shifts in the character's emotional state through their perceptions and actions
- Don't explicitly mention the target emotion - create situations that move toward it indirectly
- Use simple language for the story, simple and the kind of language that draws the user into the story.
- {'Include subtle fantasy elements if they enhance the emotional journey' if use_fantasy else 'Keep the narrative grounded in human experience with a touch of wonder'}
- Include meaningful dialogue that reveals character and advances the emotional journey
- Always act on user's prompt. Try to mirror the language they are using with the personality of the main character
- Tailor the scene to align with the character's established preferences and tendencies
- Use the correct pronouns ({story_state['pronouns']}) throughout the story
- Acknowledge and build upon the user's last response in the story

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
"""

def openai_call(prompt, model_choice="gemini"):
    """Make API call to either OpenAI or Gemini based on user choice"""
    retries = 5
    base_wait = 2
    
    # Add system message for both models
    system_message = "You are a creative storytelling assistant that helps users write emotional stories. You MUST follow the exact output format specified in the prompt, including all sections separated by ~~~~."
    
    for attempt in range(retries):
        try:
            if model_choice == "openai":
                response = openai.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:  # gemini
                # Add system message to the prompt for Gemini
                full_prompt = f"{system_message}\n\n{prompt}"
                response = model.generate_content(full_prompt)
                if response and hasattr(response, 'text'):
                    return response.text
                else:
                    print(f"Debug: Invalid response from Gemini: {response}")
                    return None
        except Exception as e:
            error_msg = str(e)
            print(f"Debug: Error in API call: {error_msg}")
            if "429" in error_msg:
                print(f"Rate limit details: {error_msg}")
                wait_time = base_wait * (2 ** attempt)
                print(f"Attempt {attempt + 1}/{retries}. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Error calling {model_choice.upper()} API: {error_msg}")
                if attempt == retries - 1:  # Last attempt
                    return None
    
    print("Failed to get response after multiple retries. Please try again later.")
    return None

def analyze_user_choice(choice, question):
    """Analyze user's choice to update their preference profile"""
    choice_text = choice.lower()
    question_text = question.lower()
    
    # Default choice patterns to look for
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
    
    # Record the choice pattern
    session['choice_patterns'].append(choice_text)
    
    # Check for pattern matches in the choice
    for trait, keywords in patterns.items():
        # Check for increases
        for keyword in keywords["increase"]:
            if keyword in choice_text:
                session['story_state']['user_preferences'][trait] += 1
                break
                
        # Check for decreases
        for keyword in keywords["decrease"]:
            if keyword in choice_text:
                session['story_state']['user_preferences'][trait] -= 1
                break
    
    # Cap values between -5 and 5
    for trait in session['story_state']['user_preferences']:
        session['story_state']['user_preferences'][trait] = max(-5, min(5, session['story_state']['user_preferences'][trait]))
    
    return session['story_state']['user_preferences']

def save_research_email(story_id, email):
    """Save research email to Supabase"""
    try:
        supabase = init_supabase()
        supabase.table('stories').update({"research_email": email}).eq("id", story_id).execute()
    except Exception as e:
        print(f"Error saving research email: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True) 