from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from modules import auth, chat
from modules.database import test_connection
import logging
import os
from datetime import timedelta

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
csrf = CSRFProtect(app)

# Set the secret key
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_development_secret_key_here')

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.before_request
def log_request_info():
    logger.debug('Headers: %s', request.headers)
    logger.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    logger.debug('Response Status: %s', response.status)
    logger.debug('Response Headers: %s', response.headers)
    logger.debug('Response Body: %s', response.get_data())
    return response

@app.route('/')
def hello():
    return jsonify({"message": "Welcome to WebCoach AI!"})

@app.route('/api/register', methods=['POST'])
def register():
    try:
        result = auth.register()
        logger.info(f"User registered: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        result = auth.login()
        logger.info(f"User logged in: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        result = auth.logout()
        logger.info("User logged out")
        return result
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return jsonify({"error": "Logout failed"}), 500

@app.route('/api/chat', methods=['POST'])
def create_chat():
    try:
        result = chat.create_chat()
        logger.info(f"Chat created: {result}")
        return result
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        return jsonify({"error": "Failed to create chat"}), 500

@app.route('/api/chat/<chat_id>/message', methods=['POST'])
def send_message(chat_id):
    try:
        result = chat.send_message(chat_id)
        logger.info(f"Message sent in chat {chat_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error sending message in chat {chat_id}: {str(e)}")
        return jsonify({"error": "Failed to send message"}), 500

@app.route('/api/chat/<chat_id>/history', methods=['GET'])
def get_chat_history(chat_id):
    try:
        result = chat.get_chat_history(chat_id)
        logger.info(f"Retrieved chat history for chat {chat_id}")
        return result
    except Exception as e:
        logger.error(f"Error retrieving chat history for chat {chat_id}: {str(e)}")
        return jsonify({"error": "Failed to retrieve chat history"}), 500

@app.route('/api/chats', methods=['GET'])
def list_chats_route():
    try:
        result = chat.list_chats()
        logger.info("Retrieved list of chats")
        return result
    except Exception as e:
        logger.error(f"Error retrieving list of chats: {str(e)}")
        return jsonify({"error": "Failed to retrieve chats"}), 500

@app.route('/api/chat/<chat_id>', methods=['DELETE'])
def delete_chat_route(chat_id):
    try:
        result = chat.delete_chat(chat_id)
        logger.info(f"Deleted chat {chat_id}")
        return result
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {str(e)}")
        return jsonify({"error": "Failed to delete chat"}), 500

@app.route('/api/test_openai', methods=['GET'])
def test_openai():
    try:
        result = chat.test_openai_connection()
        logger.info("Tested OpenAI connection")
        return jsonify({"result": result})
    except Exception as e:
        logger.error(f"Error testing OpenAI connection: {str(e)}")
        return jsonify({"error": "Failed to test OpenAI connection"}), 500

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        logger.info(f"Auth check: User {session['user_id']} is authenticated")
        return jsonify({"authenticated": True}), 200
    logger.info("Auth check: No user authenticated")
    return jsonify({"authenticated": False}), 401

if __name__ == '__main__':
    logger.info("Starting the application...")
    test_connection()
    app.run(debug=True)