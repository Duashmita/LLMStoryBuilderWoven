% Emotional tag validator for Woven story data
% This file contains rules for validating emotional progression and relationships

% Basic emotional categories
emotion_category(joy, positive).
emotion_category(sadness, negative).
emotion_category(anger, negative).
emotion_category(fear, negative).
emotion_category(surprise, neutral).
emotion_category(disgust, negative).
emotion_category(trust, positive).
emotion_category(anticipation, positive).

% Emotional intensity levels
intensity_level(low, 1).
intensity_level(medium, 2).
intensity_level(high, 3).

% Valid emotional transitions
valid_transition(From, To) :-
    emotion_category(From, FromCategory),
    emotion_category(To, ToCategory),
    (
        % Allow transitions within same category
        FromCategory = ToCategory;
        % Allow transitions from negative to positive
        FromCategory = negative, ToCategory = positive;
        % Allow transitions from neutral to any
        FromCategory = neutral;
        % Allow transitions to neutral
        ToCategory = neutral
    ).

% Validate story phase progression
valid_phase_progression(beginning, middle).
valid_phase_progression(middle, climax).
valid_phase_progression(climax, final).

% Validate emotional progression through phases
valid_emotional_progression(Phase, Emotion) :-
    (
        Phase = beginning,
        emotion_category(Emotion, _);
        Phase = middle,
        (emotion_category(Emotion, positive); emotion_category(Emotion, negative));
        Phase = climax,
        emotion_category(Emotion, positive)
    ).

% Validate personality score ranges
valid_personality_score(Score) :-
    Score >= -5,
    Score =< 5.

% Validate a complete story turn
validate_turn(Turn) :-
    Turn = turn(
        TurnNumber,
        CharacterMood,
        UserMood,
        StoryPhase,
        PersonalityScores,
        IsFinal
    ),
    % Validate turn number is positive
    TurnNumber > 0,
    % Validate moods are valid emotions
    emotion_category(CharacterMood, _),
    emotion_category(UserMood, _),
    % Validate story phase
    member(StoryPhase, [beginning, middle, climax, final]),
    % Validate personality scores
    forall(member(Score, PersonalityScores), valid_personality_score(Score)),
    % Validate final turn
    (IsFinal = true; IsFinal = false).

% Validate emotional progression between turns
validate_emotional_progression(Turn1, Turn2) :-
    Turn1 = turn(_, CharacterMood1, UserMood1, Phase1, _, _),
    Turn2 = turn(_, CharacterMood2, UserMood2, Phase2, _, _),
    % Validate phase progression
    valid_phase_progression(Phase1, Phase2),
    % Validate emotional transitions
    valid_transition(CharacterMood1, CharacterMood2),
    valid_transition(UserMood1, UserMood2).

% Validate the character mood arc for the whole story
validate_character_arc :-
    findall(turn(N, Mood, Phase), turn(N, Mood, Phase), Turns),
    validate_character_arc_sequence(Turns).

validate_character_arc_sequence([_]).
validate_character_arc_sequence([turn(N1, Mood1, Phase1), turn(N2, Mood2, Phase2)|Rest]) :-
    valid_phase_progression(Phase1, Phase2),
    valid_transition(Mood1, Mood2),
    validate_character_arc_sequence([turn(N2, Mood2, Phase2)|Rest]).

% Example usage:
% ?- validate_turn(turn(1, joy, trust, beginning, [0,0,0,0,0,0], false)).
% ?- validate_emotional_progression(
%     turn(1, joy, trust, beginning, [0,0,0,0,0,0], false),
%     turn(2, anticipation, joy, middle, [1,1,0,0,0,0], false)
% ). 