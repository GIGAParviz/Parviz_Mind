from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import os

from config import Config
from api import register_routes
from utils.validation import ValidationError

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)
    
    # Register error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return {"error": str(error)}, 400
    
    @app.errorhandler(Exception)
    def handle_general_error(error):
        return {"error": str(error)}, 500
    
    # Add route for swagger.json
    @app.route("/static/swagger.json")
    def swagger_json():
        return send_from_directory("static", "swagger.json")
    
    # Register Swagger UI
    swaggerui_blueprint = get_swaggerui_blueprint(
        Config.SWAGGER_URL,
        Config.API_URL,
        config={'app_name': "Parviz Mind API"}
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=Config.SWAGGER_URL)
    
    # Register API routes
    register_routes(app)
    
    return app

if __name__ == "__main__":
    # In development mode, skip environment validation
    dev_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    if not dev_mode:
        # Validate config before starting the app
        Config.validate()
    
    # Create and run the app
    app = create_app()
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000)
