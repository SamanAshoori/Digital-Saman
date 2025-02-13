
import os
from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

# Load training data
def load_training_data(csv_path):
    try:
        df = pd.read_csv(csv_path)
        context = "\n".join([
            f"Q: {row['question']} A: {row['answer']}"
            for _, row in df.iterrows()
        ])
        return context
    except:
        return "No training data available."

TRAINING_CONTEXT = load_training_data('training_data.csv')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AI Chat</title>
    <style>
        body { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial; }
        #chat-container { height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }
        #user-input { width: 80%; padding: 5px; }
        button { padding: 5px 15px; }
    </style>
</head>
<body>
    <div id="chat-container"></div>
    <input type="text" id="user-input" placeholder="Type your message...">
    <button onclick="sendMessage()">Send</button>

    <script>
    async function sendMessage() {
        const input = document.getElementById('user-input');
        const message = input.value;
        if (!message) return;

        // Display user message
        addMessage('User: ' + message);
        input.value = '';

        // Get bot response
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: message})
        });
        const data = await response.json();
        addMessage('Bot: ' + data.response);
    }

    function addMessage(message) {
        const container = document.getElementById('chat-container');
        container.innerHTML += '<div>' + message + '</div>';
        container.scrollTop = container.scrollHeight;
    }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    
    # Combine training context with user message
    prompt = f"{TRAINING_CONTEXT}\nNow respond in my style to: {user_message}"
    
    try:
        response = model.generate_content(prompt)
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
