from api.agents import register_agent_routes
from api.chat import register_chat_routes
from api.files import register_file_routes

def register_routes(app):
    """Register all API routes with the Flask app."""
    register_agent_routes(app)
    register_chat_routes(app)
    register_file_routes(app)