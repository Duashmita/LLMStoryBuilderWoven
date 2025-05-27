# Woven: Interactive Story Builder

An interactive storytelling application that uses AI to create personalized emotional journeys. The application supports both OpenAI's GPT-4 and Google's Gemini models for story generation.

## Features

- Interactive storytelling with emotional progression
- Support for both OpenAI GPT-4 and Google Gemini models
- Dynamic character development based on user choices
- Emotional validation and personality tracking
- Beautiful and responsive web interface
- Research data collection capabilities

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Google Gemini API key
- Supabase account (for data storage)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd LLMStoryBuilderWoven
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root directory with the following variables:
```
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
FLASK_SECRET_KEY=your_flask_secret_key_here
```

## Running the Application

1. Make sure your virtual environment is activated
2. Run the Flask application:
```bash
python app.py
```
3. Open your web browser and navigate to `http://localhost:5000`

## Project Structure

```
LLMStoryBuilderWoven/
├── app.py                 # Main Flask application
├── emotional_validator.py # Emotional validation logic
├── requirements.txt       # Python dependencies
├── static/               # Static files
│   ├── css/             # CSS stylesheets
│   └── js/              # JavaScript files
├── templates/            # HTML templates
│   └── index.html       # Main template
└── .env                 # Environment variables (create this file)
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.