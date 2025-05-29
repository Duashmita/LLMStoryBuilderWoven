-- Create stories table
CREATE TABLE IF NOT EXISTS stories (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    pronouns TEXT NOT NULL,
    age INTEGER NOT NULL,
    genre TEXT NOT NULL,
    current_emotion TEXT NOT NULL,
    target_emotion TEXT NOT NULL,
    model_choice TEXT NOT NULL,
    total_turns INTEGER NOT NULL,
    turn_count INTEGER NOT NULL,
    completed BOOLEAN DEFAULT FALSE,
    user_preferences JSONB NOT NULL DEFAULT '{}',
    character_mood_arc JSONB NOT NULL DEFAULT '{}',
    user_mood_arc JSONB NOT NULL DEFAULT '{}',
    story_paragraphs JSONB NOT NULL DEFAULT '[]',
    story_questions JSONB NOT NULL DEFAULT '[]',
    research_email TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on research_email for faster lookups
CREATE INDEX IF NOT EXISTS idx_stories_research_email ON stories(research_email);

-- Create index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_stories_created_at ON stories(created_at);

-- Enable Row Level Security (RLS)
ALTER TABLE stories ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (you may want to restrict this based on your needs)
CREATE POLICY "Allow all operations" ON stories
    FOR ALL
    USING (true)
    WITH CHECK (true); 