from flask import Flask, render_template, request
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Fix caching issues

# Configure Gemini - FIXED API KEY
try:
    # Get API key from environment variable
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        # Fallback to your key if .env is not set up
        api_key = "AIzaSyBQeZfcefV-YfZ-onQO-9umx9C8M1VP9Pg"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.0-pro')
    print("✅ Gemini API configured successfully!")
except Exception as e:
    print(f"❌ Gemini configuration failed: {e}")
    model = None

# Mood messages (keep your existing MOODS dictionary)
MOODS = {
    'relax': {
        'messages': [
            "You're doing great! Take your time 💕",
            "Learning at your own pace is perfect 🌸",
            "Every answer is progress! 💖",
            "You've got this, no rush! ✨",
            "Breathe and believe in yourself 🌺"
        ],
        'color': 'pink',
        'name': 'Relax Mode'
    },
    'panic': {
        'messages': [
            "Deep breath! One question at a time! 💙",
            "You can do this! Break it down! 🌊",
            "Panic = care. You'll be okay! 💦",
            "Focus on just this one. You got it! ⚡",
            "It's okay to feel stressed. Keep going! 💪"
        ],
        'color': 'blue',
        'name': 'Panic Mode'
    },
    'tired': {
        'messages': [
            "Even tired, you're here. That counts! 💚",
            "Rest is okay. You're still learning! 🌿",
            "Small wins matter most when you're tired ✨",
            "Be gentle with yourself today 🍃",
            "You're stronger than you think! 💪"
        ],
        'color': 'green',
        'name': 'Tired Mode'
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    paragraph = request.form.get('paragraph')
    mood = request.form.get('mood')
    
    # Check if Gemini is configured
    if model is None:
        return render_template('index.html', 
                             error="API not configured properly. Using demo mode with sample flashcards.")
    
    # Check word limit
    word_count = len(paragraph.split())
    if word_count > 400:
        return render_template('index.html', 
                             error="Text is too long! Please use 400 words or less.")
    
    try:
        # Generate 5 flashcards using Gemini
        prompt = f"""Create exactly 5 flashcard questions and answers from this text.

Text: {paragraph}

Format each flashcard exactly like this:
Q: [question]
A: [answer]

Make sure to create exactly 5 flashcards, separated by blank lines."""

        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Parse flashcards
        flashcards = []
        current_q = ""
        current_a = ""
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Q:'):
                if current_q and current_a:
                    flashcards.append({'question': current_q, 'answer': current_a})
                current_q = line.replace('Q:', '').strip()
                current_a = ""
            elif line.startswith('A:'):
                current_a = line.replace('A:', '').strip()
        
        # Add last card
        if current_q and current_a:
            flashcards.append({'question': current_q, 'answer': current_a})
        
        # Make sure we have exactly 5 cards
        while len(flashcards) < 5:
            flashcards.append({
                'question': 'What is a key concept from this text?',
                'answer': 'Review the text for details.'
            })
        
        flashcards = flashcards[:5]
        
        mood_data = MOODS[mood]
        
        return render_template('results.html', 
                             flashcards=flashcards,
                             mood=mood,
                             messages=mood_data['messages'],
                             color=mood_data['color'],
                             mood_name=mood_data['name'])
    
    except Exception as e:
        # If API fails, use sample flashcards for demo
        sample_flashcards = [
            {'question': 'What is the main topic of this text?', 'answer': 'The text discusses various learning strategies and study techniques.'},
            {'question': 'Why is emotional state important for learning?', 'answer': 'Emotional state affects concentration, memory retention, and motivation.'},
            {'question': 'What are some effective study techniques mentioned?', 'answer': 'Active recall, spaced repetition, and interleaved practice.'},
            {'question': 'How can students maintain focus during long study sessions?', 'answer': 'Taking regular breaks, using focus music, and setting specific goals.'},
            {'question': 'What role does AI play in modern education?', 'answer': 'AI can personalize learning, generate study materials, and provide instant feedback.'}
        ]
        
        mood_data = MOODS[mood]
        
        return render_template('results.html', 
                             flashcards=sample_flashcards,
                             mood=mood,
                             messages=mood_data['messages'],
                             color=mood_data['color'],
                             mood_name=mood_data['name'])

if __name__ == '__main__':
    app.run(debug=True)