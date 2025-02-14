
import os
from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
from google.ai.generativelanguage_v1beta.types import content

app = Flask(__name__)
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

def load_training_data(csv_path):
    try:
        file = genai.upload_file(csv_path, mime_type="text/csv")
        return file
    except Exception as e:
        print(f"Error loading training data: {e}")
        return None

# Initialize model with configuration
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction="use training_data.csv for my tone and style"
)

# Store chat sessions
chat_sessions = {}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Digital Saman Chat</title>
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
    let sessionId = null;

    async function sendMessage() {
        const input = document.getElementById('user-input');
        const message = input.value;
        if (!message) return;

        addMessage('User: ' + message);
        input.value = '';

        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        const data = await response.json();
        sessionId = data.session_id;
        addMessage('Digital Saman: ' + data.response);
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

@app.route('/embed')
def embed():
    embedded_template = HTML_TEMPLATE.replace('<body>', '<body style="margin: 0; padding: 10px;">')
    return render_template_string(embedded_template)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    session_id = request.json.get('session_id')
    
    try:
        if not session_id:
            training_file = load_training_data('training_data.csv')
            chat = model.start_chat(history=[
                {
                    "role": "user",
                    "parts": [
                        training_file,
                        "Hello - You are a chatbot called Digital Saman. I as the original saman want a digital me to upload as portfolio project. your job is to emulate my style of talking",
                    ],
                },
                {
                    "role": "model",
                    "parts": [
                        "Understood. I'm Digital Saman, ready to emulate your style! Let's do this. What's on your mind?\n",
                    ],
                }
            ])
            session_id = str(len(chat_sessions) + 1)
            chat_sessions[session_id] = chat
        
        chat = chat_sessions[session_id]
        response = chat.send_message(user_message)
        
        return jsonify({
            'response': response.text,
            'session_id': session_id
        })
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}", 'session_id': None})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
