import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from .config import Config
from .ai_core import AICore
from .database import DatabaseManager

bp = Blueprint("main", __name__)

_db_manager = DatabaseManager("chat_history.db")
_ai_core = AICore(_db_manager, model_name="deepseek-r1-distill-llama-70b")
MODELS = ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "gemma2-9b-it", "deepseek-r1-distill-qwen-32b"]

@bp.route("/", methods=["GET"])
def index():
    return render_template("index.html",
                           models=MODELS,
                           selected_model="deepseek-r1-distill-llama-70b",
                           chat_history=_ai_core.chat_history,
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

@bp.route("/chat", methods=["POST"])
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
        file_path = os.path.join(Config.UPLOAD_FOLDER, file_obj.filename)
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
    _db_manager.create_conversation(conversation_data)
    
    try:
        response, summary, total_tokens, price = _ai_core.answer_query(
            user_id, query, file_obj, summarize, tone, model_name, creativity,
            keywords, language, response_length, welcome_message, exclusion_words, main_prompt, chatbot_name
        )
        user_message_id = str(uuid.uuid4())
        ai_message_id = str(uuid.uuid4())
        _db_manager.create_message({
            "id": user_message_id,
            "conversation_id": conversation_id,
            "role": "user",
            "content": query,
            "tokens_used": _ai_core.count_tokens(query),
            "file_ids": []
        })
        _db_manager.create_message({
            "id": ai_message_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": response,
            "tokens_used": _ai_core.count_tokens(response),
            "file_ids": []
        })
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('main.index'))
    finally:
        if saved_file_path:
            if file_obj:
                file_obj.close()
            os.remove(saved_file_path)
    return render_template("templates/index.html",
                           models=MODELS,
                           selected_model=model_name,
                           chat_history=_ai_core.chat_history,
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

@bp.route("/clear", methods=["POST"])
def clear():
    _ai_core.clear_history()
    return redirect(url_for('main.index'))

@bp.route("/static/swagger.json")
def swagger_json():
    return send_from_directory("static", "swagger.json")
