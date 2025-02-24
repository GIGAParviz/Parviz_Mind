import os
import uuid
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from config import Config, models, default_model
from ai_core import AICore

app = Flask(__name__)
app.config.from_object(Config)
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.config['UPLOAD_FOLDER'] = "uploads"

ai_core = AICore()

SWAGGER_URL = Config.SWAGGER_URL
API_URL = Config.API_URL
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Parviz Mind"}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html",
                           models=models,
                           selected_model=default_model,
                           chat_history=ai_core.chat_history,
                           summary="",
                           token_count=0,
                           token_price="0 دلار",
                           chatbot_name="",
                           tone="رسمی",
                           creativity=0.1,
                           keywords="",
                           language="فارسی",
                           response_length="بلند",
                           main_prompt="",
                           exclusion_words="",
                           summarize=False)

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.form.get("user_id")
    query = request.form.get("query")
    file_obj = request.files.get("file")
    summarize = True if request.form.get("summarize") == "on" else False
    tone = request.form.get("tone")
    model_name = request.form.get("model")
    creativity = float(request.form.get("creativity", 0.1))
    keywords = request.form.get("keywords")
    language = request.form.get("language")
    response_length = request.form.get("response_length")
    welcome_message = request.form.get("welcome_message")
    exclusion_words = request.form.get("exclusion_words")
    main_prompt = request.form.get("main_prompt")
    chatbot_name = request.form.get("chatbot_name")

    saved_file_path = None
    if file_obj and file_obj.filename != "":
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_obj.filename)
        file_obj.save(file_path)
        saved_file_path = file_path
        file_obj = open(file_path, "rb")
    
    conversation_id = str(uuid.uuid4())
    conversation_data = {
        "id": conversation_id,
        "user_id": user_id,
        "agent_id": "",
        "chatbot_name": chatbot_name,
        "model_name": model_name,
        "temperature": creativity,
        "title": f"Chat with {chatbot_name}" if chatbot_name else "Chat Session"
    }
    ai_core.db.create_conversation(conversation_data)
    
    try:
        response, summary, total_tokens, price = ai_core.answer_query(
            user_id, query, file_obj, summarize, tone, model_name, creativity,
            keywords, language, response_length, welcome_message, exclusion_words, main_prompt, chatbot_name
        )
        # Save user and assistant messages in the database
        user_message_id = str(uuid.uuid4())
        ai_message_id = str(uuid.uuid4())
        ai_core.db.create_message({
            "id": user_message_id,
            "conversation_id": conversation_id,
            "role": "user",
            "content": query,
            "tokens_used": ai_core.count_tokens(query),
            "file_ids": []
        })
        ai_core.db.create_message({
            "id": ai_message_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": response,
            "tokens_used": ai_core.count_tokens(response),
            "file_ids": []
        })
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('index'))
    finally:
        if saved_file_path:
            if file_obj:
                file_obj.close()
            os.remove(saved_file_path)
    return render_template("index.html",
                           models=models,
                           selected_model=model_name,
                           chat_history=ai_core.chat_history,
                           summary=summary,
                           token_count=total_tokens,
                           token_price=price,
                           chatbot_name=chatbot_name,
                           tone=tone,
                           creativity=creativity,
                           keywords=keywords,
                           language=language,
                           response_length=response_length,
                           main_prompt=main_prompt,
                           exclusion_words=exclusion_words,
                           summarize=summarize)

@app.route("/clear", methods=["POST"])
def clear():
    ai_core.clear_history()
    return redirect(url_for('index'))

@app.route("/static/swagger.json")
def swagger_json():
    return send_from_directory("static", "swagger.json")

@app.route("/api/users", methods=["POST"])
def register_user():
    data = request.get_json()
    if not data or "id" not in data:
        return jsonify({"message": "User id is required"}), 400
    user = ai_core.db.register_user(data["id"])
    if user is None:
        return jsonify({"message": "User already exists"}), 409
    return jsonify(user), 201

@app.route("/api/agents", methods=["POST"])
def create_agent():
    data = request.get_json()
    required_fields = ["id", "creator_id", "name", "llm_model", "instruction_prompt"]
    if not all(field in data for field in required_fields):
        return jsonify({"message": "Missing required fields"}), 400
    agent = ai_core.db.create_agent(data)
    if agent:
        return jsonify(agent), 201
    return jsonify({"message": "Error creating agent"}), 400

@app.route("/api/agents/<agent_id>", methods=["PUT"])
def update_agent(agent_id):
    data = request.get_json()
    agent = ai_core.db.update_agent(agent_id, data)
    if agent:
        return jsonify(agent), 200
    return jsonify({"message": "Agent not found or update error"}), 404

@app.route("/api/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    agent = ai_core.db.get_agent(agent_id)
    if agent:
        return jsonify(agent), 200
    return jsonify({"message": "Agent not found"}), 404

@app.route("/api/agents/<agent_id>", methods=["DELETE"])
def delete_agent(agent_id):
    success = ai_core.db.delete_agent(agent_id)
    if success:
        return jsonify({"message": "Agent deleted successfully"}), 204
    return jsonify({"message": "Agent not found"}), 404

@app.route("/api/users/<user_id>/conversations", methods=["GET"])
def list_conversations(user_id):
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    conversations = ai_core.db.list_conversations(user_id, page, limit)
    return jsonify({"items": conversations, "total": len(conversations), "page": page, "limit": limit}), 200

@app.route("/api/conversations/<conversation_id>/messages", methods=["GET"])
def list_messages(conversation_id):
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))
    messages = ai_core.db.list_messages(conversation_id, page, limit)
    return jsonify({"items": messages, "total": len(messages), "page": page, "limit": limit}), 200

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    if not data or "user_id" not in data or "message" not in data:
        return jsonify({"message": "Missing required fields: user_id or message"}), 400
    user_id = data["user_id"]
    message = data["message"]
    file_ids = data.get("file_ids", [])
    conversation_id = data.get("conversation_id")
    model_name = data.get("model_name")
    agent_id = data.get("agent_id")
    
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        conversation_data = {
            "id": conversation_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "chatbot_name": data.get("chatbot_name", ""),
            "model_name": model_name,
            "temperature": float(data.get("creativity", 0.7)),
            "title": data.get("title", "")
        }
        ai_core.db.create_conversation(conversation_data)
    try:
        response_text, summary, total_tokens, price = ai_core.answer_query(
            user_id, message, None, False, 
            tone=data.get("tone", ""),
            model_name=model_name if model_name else default_model,
            creativity=float(data.get("creativity", 0.7)),
            keywords=data.get("keywords", ""),
            language=data.get("language", "en"),
            response_length=data.get("response_length", "MEDIUM"),
            welcome_message=data.get("welcome_message", ""),
            exclusion_words=data.get("exclusion_words", ""),
            main_prompt=data.get("main_prompt", ""),
            chatbot_name=data.get("chatbot_name", "")
        )
    except Exception as e:
        return jsonify({"message": f"Error processing chat: {str(e)}"}), 400

    user_message_id = str(uuid.uuid4())
    ai_message_id = str(uuid.uuid4())
    ai_core.db.create_message({
        "id": user_message_id,
        "conversation_id": conversation_id,
        "role": "user",
        "content": message,
        "tokens_used": ai_core.count_tokens(message),
        "file_ids": file_ids
    })
    ai_core.db.create_message({
        "id": ai_message_id,
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": response_text,
        "tokens_used": ai_core.count_tokens(response_text),
        "file_ids": []
    })
    token_usage = {
        "prompt_tokens": ai_core.count_tokens(message),
        "completion_tokens": ai_core.count_tokens(response_text),
        "total_tokens": total_tokens
    }
    return jsonify({
        "conversation_id": conversation_id,
        "message_id": ai_message_id,
        "response": response_text,
        "token_usage": token_usage
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config['DEBUG'])

