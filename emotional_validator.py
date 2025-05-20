class EmotionalValidator:
    def __init__(self):
        # Define core emotion categories - 10 specific emotions
        self.emotion_categories = {
            'joy': 'positive',      # Happiness, delight
            'sadness': 'negative',  # Grief, sorrow
            'anger': 'negative',    # Rage, frustration
            'fear': 'negative',     # Anxiety, terror
            'trust': 'positive',    # Confidence, faith
            'surprise': 'neutral',  # Amazement, wonder
            'anticipation': 'positive', # Expectation, hope
            'disgust': 'negative',  # Aversion, repulsion
            'neutral': 'neutral',   # Balanced, calm
            'confusion': 'neutral'  # Uncertainty, doubt
        }

        # Define valid phase progressions based on turn ranges
        # These are flexible guidelines for validation
        self.phase_ranges = [
            (1, 3, 'initial'),
            (4, 6, 'transitional 1'),
            (7, 8, 'transitional 2'),
            (9, 10, 'transitional 3'),
            (11, 12, 'target emotion') # This range is for reaching the target emotion in longer stories
        ]

        # Define basic valid transitions between emotion categories (simplified)
        self.valid_category_transitions = {
            'positive': ['positive', 'neutral', 'surprise', 'anticipation'],
            'negative': ['negative', 'neutral', 'surprise', 'fear', 'anger', 'sadness', 'disgust'],
            'neutral': list(self.emotion_categories.values()), # Can transition to any category from neutral
        }

    def get_phase_for_turn(self, turn_number, total_turns):
         # Determine story phase based on turn number and total turns
        if turn_number < total_turns // 3:
            return "beginning"
        elif turn_number < (total_turns * 2) // 3:
            return "middle"
        elif turn_number <= total_turns:
            return "climax"
        else:
            return "final" # For turns beyond the initial total_turns in long stories


    def validate_turn(self, turn_number, character_mood_arc, story_phase, personality_scores, is_final):
        """Validate a single story turn and its progression from the previous turn"""
        try:
            print(f"Validating turn: {turn_number}, Story Phase: {story_phase}")

            current_mood = character_mood_arc.get(turn_number)

            # 1. Validate current character mood
            if not isinstance(current_mood, str) or current_mood.lower() not in self.emotion_categories:
                 valid_emotions_list = ', '.join(self.emotion_categories.keys())
                 error_msg = f"Invalid character mood '{current_mood}'. Must be one of: {valid_emotions_list}."
                 print(f"Validation Error (Turn {turn_number}): {error_msg}")
                 return error_msg

            # 2. Validate emotional progression (if not the first turn)
            if turn_number > 0:
                previous_mood = character_mood_arc.get(turn_number - 1)

                if previous_mood and current_mood:
                     previous_mood_lower = previous_mood.lower()
                     current_mood_lower = current_mood.lower()

                     prev_category = self.emotion_categories.get(previous_mood_lower, 'neutral')
                     curr_category = self.emotion_categories.get(current_mood_lower, 'neutral')

                     # Basic category transition check
                     if curr_category not in self.valid_category_transitions.get(prev_category, []):
                          error_msg = f"Invalid emotional transition from '{previous_mood}' ({prev_category}) to '{current_mood}' ({curr_category})."
                          print(f"Validation Error (Turn {turn_number}): {error_msg}")
                          # return error_msg # We will log this but not return as error for now

            # 3. Validate against flexible phase guidelines (for character mood)
            current_mood_lower = current_mood.lower()
            expected_phase_category = None

            for start, end, phase_name in self.phase_ranges:
                 if start <= turn_number <= end:
                      # For simplicity, let's assume 'initial', 'transitional', 'target emotion' phases
                      # have associated emotional expectations.
                      # This part needs to be refined based on specific emotional rules for each phase.
                      # For now, we'll just check if the mood's category aligns with a simplified expectation.
                      # Example: In 'target emotion' phase, character mood should ideally be 'positive'
                      if phase_name == 'target emotion' and self.emotion_categories.get(current_mood_lower) != 'positive':
                          error_msg = f"Mood '{current_mood}' ({self.emotion_categories.get(current_mood_lower, 'unknown')}) doesn't align with the '{phase_name}' phase expectation (ideally positive).";
                          print(f"Validation Error (Turn {turn_number}): {error_msg}")
                          # return error_msg # Log but don't strictly enforce for now

            # 4. Validate personality scores (basic check)
            if not isinstance(personality_scores, list) or len(personality_scores) != 6:
                 error_msg = f"Invalid personality scores format or count."
                 print(f"Validation Error (Turn {turn_number}): {error_msg}")
                 # return error_msg # Log but don't strictly enforce for now
            else:
                 for score in personality_scores:
                     if not isinstance(score, (int, float)) or score < -5 or score > 5:
                         error_msg = f"Invalid personality score value: {score}. Must be between -5 and 5."
                         print(f"Validation Error (Turn {turn_number}): {error_msg}")
                         # return error_msg # Log but don't strictly enforce for now

            # If no strict errors were found, return None
            print(f"Validation for turn {turn_number} completed with no strict errors.")
            return None # Return None if validation passes (or only logs warnings)

        except Exception as e:
            error_msg = f"Error during validation for turn {turn_number}: {str(e)}";
            print(f"Validation Error (Turn {turn_number}): {error_msg}")
            return error_msg # Return error message in case of unexpected exceptions

    # We will keep these methods but update them to work with the mood arc dictionary
    # and potentially implement more sophisticated rules later.

    def validate_emotional_progression(self, character_mood_arc):
        """Validate emotional progression across the entire character arc"""
        try:
            print(f"Validating emotional progression for arc with {len(character_mood_arc)} turns")
            # Implement arc-level validation rules here later
            return None # Return None if validation passes
        except Exception as e:
            error_msg = f"Error during emotional arc validation: {str(e)}";
            print(f"Validation Error (Arc): {error_msg}")
            return error_msg # Return error message in case of unexpected exceptions

    def validate_character_arc(self, character_mood_arc):
        """Validate the entire character arc for overall coherence"""
        try:
            print(f"Validating character arc coherence for {len(character_mood_arc)} turns")
            # Implement overall arc coherence rules here later
            return None # Return None if validation passes
        except Exception as e:
            error_msg = f"Error during character arc coherence validation: {str(e)}";
            print(f"Validation Error (Arc Coherence): {error_msg}")
            return error_msg # Return error message in case of unexpected exceptions

# Example usage:
if __name__ == "__main__":
    validator = EmotionalValidator()
    
    # Test a single turn
    turn_valid = validator.validate_turn(
        turn_number=1,
        character_mood_arc={1: "joy"},
        story_phase="beginning",
        personality_scores=[0, 0, 0, 0, 0, 0],
        is_final=False
    )
    print(f"Turn valid: {turn_valid}")
    
    # Test emotional progression
    turn1 = "turn(1, joy, trust, beginning, [0,0,0,0,0,0], false)"
    turn2 = "turn(2, anticipation, joy, middle, [1,1,0,0,0,0], false)"
    progression_valid = validator.validate_emotional_progression({1: "joy", 2: "anticipation"})
    print(f"Progression valid: {progression_valid}") 