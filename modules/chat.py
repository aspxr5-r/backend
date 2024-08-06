from flask import jsonify, request, session
from modules.database import chat_sessions
from datetime import datetime, timezone
from bson.objectid import ObjectId
from openai import OpenAI
from config import OPENAI_API_KEY
import logging
from openai import OpenAIError, APIError, APIConnectionError, RateLimitError, AuthenticationError

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_chat():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    chat = {
        "user_id": session['user_id'],
        "messages": [],
        "created_at": datetime.now(timezone.utc)
    }
    result = chat_sessions.insert_one(chat)
    return jsonify({"chat_id": str(result.inserted_id)}), 201

def send_message(chat_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    
    chat = chat_sessions.find_one({"_id": ObjectId(chat_id), "user_id": session['user_id']})
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    
    system_prompts = """You are the first AI Coach of WebCoach AI. You help potential clients learn more about the future and potential of webcoach ai. 
    Follow this content for coaching and guiding the users about WebCoach.

    Content:
    How it Works:
    - WebCoach AI is a platform that offers LLM based AI Coaches to course students.
    - Coaches can be customised for the online courses using course video and text material as well as a list of questions to be asked.
    - We figure out the users personal needs for their course in the course of a few emails.
    - Your custom AI Coach will be built by standards set by the user.
    - The LLM is trained on the course material as well as questions tailored to the course.
    - The user will be able to review the coach and further improve the responses.
    - The team is continuously supporting and improving the coach using past conversations and feedback.
    
    Benefits and Offer:
    - By being able to coach multiple times more students simultaneously the course provider is able to help more students with less time and effort.
    - Increase course revenue with additional revenue from offering AI Coaching Services to students. 
    - Boost personal coaching value by stepping in for complex and unique situations charging a premium for personal coaching services.
    - Impress students and competition with innovative AI solutions.
    - Increase student satisfaction and learning performance by providing them with dedicated AI assistance and support.
    - Set up AI Coach easily for online courses. The WebCoach AI Team does all the work for you.
    
    Future Plans:
    - The team is working on building the first test version of WebCoach AI for the first testers. 
    - These first Versions are going to be free to use and will also offer discounted life time rates.
    - By signing up for the waitlist clients get access to the testing stage and continuous updates about the development progress.
    """

    # Prepare messages for OpenAI API
    messages = [{"role": "system", "content": system_prompts}]
    for msg in chat['messages']:
        messages.append({"role": "user", "content": msg['user']})
        messages.append({"role": "assistant", "content": msg['ai']})
    messages.append({"role": "user", "content": user_message})
    
    try:
        logger.debug("Sending request to OpenAI API")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        logger.debug("Received response from OpenAI API")
        ai_message = response.choices[0].message.content
        logger.debug(f"AI response (first 100 chars): {ai_message[:100]}...")
    except OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    # Update chat with new messages
    chat_sessions.update_one(
        {"_id": ObjectId(chat_id)},
        {"$push": {"messages": {"user": user_message, "ai": ai_message, "timestamp": datetime.now(timezone.utc)}}}
    )
    
    return jsonify({"ai_response": ai_message}), 200

def get_chat_history(chat_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    chat = chat_sessions.find_one({"_id": ObjectId(chat_id), "user_id": session['user_id']})
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    
    return jsonify({"messages": chat['messages']}), 200

def list_chats():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    chats = chat_sessions.find({"user_id": session['user_id']})
    chat_list = [{
        "chat_id": str(chat['_id']),
        "created_at": chat['created_at'],
        "last_message": chat['messages'][-1]['user'] if chat['messages'] else None
    } for chat in chats]
    
    return jsonify({"chats": chat_list}), 200

def delete_chat(chat_id):
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    result = chat_sessions.delete_one({"_id": ObjectId(chat_id), "user_id": session['user_id']})
    if result.deleted_count == 0:
        return jsonify({"error": "Chat not found or unauthorized"}), 404
    
    return jsonify({"message": "Chat deleted successfully"}), 200

def test_openai_connection():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, are you working?"}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"