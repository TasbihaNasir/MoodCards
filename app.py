from flask import Flask, render_template, request
import google.generativeai as genai
from dotenv import load_dotenv
import os
import requests


load_dotenv()

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 #cache clear krne ke lye


gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    gemini_api_key = "YOUR_GEMINI_KEY_HERE"

model = None

try:
    print("🔧 Configuring Gemini API...")
    genai.configure(api_key=gemini_api_key)
    
    
    flash_models = ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-flash-latest']
    
    for model_name in flash_models:
        try:
            print(f"  Trying {model_name}...")
            model = genai.GenerativeModel(model_name)
            test = model.generate_content("hi")
            print(f"  ✅ {model_name} works! (15 req/min)")
            break
        except:
            continue
            
except Exception as e:
    print(f"  ❌ Gemini not available: {str(e)[:80]}")


GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    GROQ_API_KEY = "YOUR_GROQ_KEY_HERE"  

def generate_with_groq(text):
    
    try:
        print("🚀 Using Groq AI (FREE, unlimited for hackathons)...")
        
        prompt = f"""Create exactly 5 high-quality flashcard questions from this text for students.

Text: {text}

Requirements:
- Questions must test deep understanding of THIS specific text
- Make diverse questions (definitions, explanations, applications)
- Answers should be 1-3 sentences from the text
- Perfect for students studying for exams

Format EXACTLY:
Q: [question]
A: [answer]

Q: [question]
A: [answer]

(5 total flashcards)"""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile", 
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"Groq error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Groq failed: {e}")
        return None

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
    
  
    print(f"🔍 Received mood: {mood}")
    print(f"🔍 Paragraph length: {len(paragraph.split())} words")
    
   
    word_count = len(paragraph.split())
    if word_count > 400:
        return render_template('index.html', 
                             error="Text is too long! Please use 400 words or less.")
    
    
    if mood not in MOODS:
        print(f"⚠️ Invalid mood '{mood}', defaulting to 'relax'")
        mood = 'relax'
    
    try:
        ai_response = None
        
        # Gemini nhi chal rha groq add kara ha BS CHAL JAYENSDdjb
        if model:
            try:
                print("🤖 Trying Gemini...")
                prompt = f"""Create exactly 5 comprehensive flashcard questions from this text.

Text: {paragraph}

Requirements:
- Questions test deep understanding of THIS text
- Diverse question types (definitions, explanations, applications)
- Answers 1-3 sentences from the text
- Perfect for exam preparation

Format:
Q: [question]
A: [answer]

(5 flashcards total)"""
                
                response = model.generate_content(prompt)
                ai_response = response.text
                print("✅ Gemini worked!")
            except Exception as e:
                print(f"Gemini quota exceeded: {str(e)[:80]}")
        
        # Try Groq if Gemini failed
        if not ai_response:
            ai_response = generate_with_groq(paragraph)
        
       
        if ai_response:
            flashcards = []
            lines = ai_response.split('\n')
            current_q = ""
            current_a = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('Q:') or line.startswith('**Q:'):
                    if current_q and current_a:
                        flashcards.append({'question': current_q, 'answer': current_a})
                    current_q = line.replace('Q:', '').replace('**Q:', '').replace('**', '').strip()
                    current_a = ""
                elif line.startswith('A:') or line.startswith('**A:'):
                    current_a = line.replace('A:', '').replace('**A:', '').replace('**', '').strip()
            
            if current_q and current_a:
                flashcards.append({'question': current_q, 'answer': current_a})
            
            print(f"📝 Created {len(flashcards)} flashcards")
            
           
            while len(flashcards) < 5:
                flashcards.append({
                    'question': 'What is a key concept from this text?',
                    'answer': 'Review the main ideas and important details.'
                })
            
            flashcards = flashcards[:5]
        else:
            raise Exception("All AI APIs failed")
        
       
        mood_data = MOODS.get(mood, MOODS['relax'])
        
        print(f"✅ Rendering with mood: {mood}, color: {mood_data['color']}")
        
        return render_template('results.html', 
                             flashcards=flashcards,
                             mood=mood,
                             messages=mood_data['messages'],
                             color=mood_data['color'],
                             mood_name=mood_data['name'])
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return render_template('index.html', 
                             error="Unable to generate flashcards. Please try again in a moment.")

if __name__ == '__main__':
    app.run(debug=True)