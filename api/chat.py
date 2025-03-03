from flask import request, jsonify

from core.ai import get_ai_core
from services.database import get_db_manager
from schemas.chat import ChatRequest, ConversationResponse, MessageResponse
from utils.validation import ValidationError

def register_chat_routes(app):
    """Register chat-related routes with the Flask app."""
    
    @app.route("/api/chat", methods=["POST"])
    def chat():
        """Process a chat request."""
        data = request.json
        file = request.files.get("file")
        
        try:
            # Validate request data
            chat_request = ChatRequest(**data)
            
            # Get AI core instance
            ai_core = get_ai_core()
            
            # Process file if provided
            file_obj = None
            if file:
                from core.storage import get_storage_service
                storage = get_storage_service()
                file_obj = storage.upload_file(file)
            
            # Process the query
            response = ai_core.answer_query(
                user_id=chat_request.user_id,
                query=chat_request.query,
                file_obj=file_obj,
                summarize=chat_request.summarize,
                tone=chat_request.tone,
                model_name=chat_request.model_name,
                creativity=chat_request.creativity,
                keywords=chat_request.keywords,
                language=chat_request.language,
                response_length=chat_request.response_length,
                welcome_message=chat_request.welcome_message,
                exclusion_words=chat_request.exclusion_words,
                main_prompt=chat_request.main_prompt,
                chatbot_name=chat_request.chatbot_name
            )
            
            return jsonify(response), 200
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/users/<user_id>/conversations", methods=["GET"])
    def list_conversations(user_id):
        """List conversations for a user."""
        try:
            page = request.args.get("page", 1, type=int)
            limit = request.args.get("limit", 20, type=int)
            
            db_manager = get_db_manager()
            conversations = db_manager.list_conversations(user_id, page, limit)
            
            result = {
                "conversations": [ConversationResponse(**conv).dict() for conv in conversations],
                "page": page,
                "limit": limit,
                "total": len(conversations)  # This should ideally be the total count, not just the current page
            }
            
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/conversations/<conversation_id>/messages", methods=["GET"])
    def list_messages(conversation_id):
        """List messages in a conversation."""
        try:
            page = request.args.get("page", 1, type=int)
            limit = request.args.get("limit", 50, type=int)
            
            db_manager = get_db_manager()
            messages = db_manager.list_messages(conversation_id, page, limit)
            
            result = {
                "messages": [MessageResponse(**msg).dict() for msg in messages],
                "page": page,
                "limit": limit,
                "total": len(messages)  # This should ideally be the total count, not just the current page
            }
            
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
