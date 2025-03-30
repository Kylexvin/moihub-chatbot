# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from db import get_answer, add_knowledge, get_all_knowledge

app = Flask(__name__)
# Enable CORS for all routes - this is crucial for your React frontend
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    """Handles user queries and returns chatbot responses."""
    data = request.json
    user_question = data.get("question")
    
    if not user_question:
        return jsonify({"error": "No question provided"}), 400
    
    answer = get_answer(user_question)
    
    if answer:
        return jsonify({"response": answer})
        
    return jsonify({"response": "I don't know that yet. Can you teach me the correct answer?"})

@app.route("/train", methods=["POST"])
def train():
    """Allows users to add new knowledge to the chatbot."""
    data = request.json
    question = data.get("question")
    answer = data.get("answer")
    
    if not question or not answer:
        return jsonify({"error": "Both question and answer are required!"}), 400
    
    success_message = add_knowledge(question, answer)
    return jsonify({"message": success_message})

@app.route("/knowledge", methods=["GET"])
def knowledge():
    """Returns all stored knowledge."""
    knowledge_data = get_all_knowledge()
    return jsonify(knowledge_data)

if __name__ == "__main__":
    app.run(debug=True)