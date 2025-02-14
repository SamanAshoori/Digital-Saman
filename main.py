import os
from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Configure generation parameters
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    return file

# Initialize model with training data
training_file = upload_to_gemini("training_data.csv", mime_type="text/csv")
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
    system_instruction="use training_data.csv for my tone and style")

# Store chat sessions
chat_sessions = {}

# Initial chat history
initial_chat_history = [
    {
        "role": "user",
        "parts": [
            training_file,
            "Hello - You are a chatbot called Digital Saman. Based of the programmer called Saman.\nStyle and Tone based on the attached file - training_data.csv\nPlease ask the user their name after the next message from the user input.\nI am pro-swearing but keep it mostly professional \nPlain Text Only",
        ],
    },
    {
        "role": "model",
        "parts": [
            "Alright, I'm Digital Saman, ready to assist. Fire away with your questions or requests. And after this, I'll need to know your name.\n",
        ],
    },
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Digital Saman Chat</title>
    <style>
        body {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-family: Arial;
            background-color: #121212; /* Dark background */
            color: #e0e0e0;         /* Light text color */
        }

        #chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #333; /* Darker border */
            padding: 10px;
            margin-bottom: 10px;
            background-color: rgba(25, 25, 25, 0.9); /* Semi-transparent background */
            border-radius: 8px;
        }

        .user-message {
            color: white;
            text-align: right;
            margin-bottom: 5px;
            padding: 8px;
            background-color: #333;
            border-radius: 8px;
            float: right;
            clear: both;
        }

        .bot-message {
            color: #00ff88; /* Green */
            text-align: left;
            margin-bottom: 5px;
            padding: 8px;
            background-color: #222;
            border-radius: 8px;
            float: left;
            clear: both;
        }

        #chat-container div {
            clear: both; /* Crucial for correct chat flow */
        }

        #user-input {
            width: calc(80% - 10px);
            padding: 10px;
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid #333;
            color: #e0e0e0;
            border-radius: 8px;
        }

        button {
            width: 20%;
            padding: 10px;
            background: linear-gradient(135deg, #00ff88, #00cc66);
            color: #121212;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            margin-left: 10px;
        }
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

            addMessage('User: ' + message, true); // Add user message
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
            addMessage('Digital Saman: ' + data.response, false); // Add bot message
        }

        function addMessage(message, isUser) {
            const container = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = isUser ? 'user-message' : 'bot-message';
            messageDiv.textContent = message; // Important for security
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }

        document.getElementById('user-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    session_id = request.json.get('session_id')

    try:
        if not session_id:
            chat = model.start_chat(history=initial_chat_history)
            session_id = str(len(chat_sessions) + 1)
            chat_sessions[session_id] = chat

        chat = chat_sessions[session_id]
        response = chat.send_message(user_message)

        return jsonify({'response': response.text, 'session_id': session_id})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}", 'session_id': None})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,
            debug=True)  # debug=True for easier development
