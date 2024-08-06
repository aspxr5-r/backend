from flask import jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from modules.database import users
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)

def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    logger.debug(f"Registering user: {username}")
    
    if not username or not password:
        logger.warning("Username or password missing")
        return jsonify({"error": "Username and password are required"}), 400
    
    if users.find_one({"username": username}):
        logger.warning(f"Username {username} already exists")
        return jsonify({"error": "Username already exists"}), 400
    
    hashed_password = generate_password_hash(password)
    user_id = users.insert_one({
        "username": username, 
        "password": hashed_password
    }).inserted_id

    logger.info(f"User {username} registered successfully")
    
    return jsonify({"message": "User registered successfully", "user_id": str(user_id)}), 201

def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    user = users.find_one({"username": username})
    if user and check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        return jsonify({"message": "Logged in successfully", "user_id": str(user['_id'])}), 200
    
    return jsonify({"error": "Invalid username or password"}), 401

def logout():
    if 'user_id' in session:
        session.pop('user_id', None)
        return jsonify({"message": "Logged out successfully"}), 200
    return jsonify({"error": "No user is currently logged in"}), 400

def get_current_user():
    if 'user_id' in session:
        user_id = session['user_id']
        user = users.find_one({"_id": ObjectId(user_id)})
        if user:
            return jsonify({
                "user_id": str(user['_id']),
                "username": user['username']
            }), 200
    return jsonify({"error": "No user is currently logged in"}), 401