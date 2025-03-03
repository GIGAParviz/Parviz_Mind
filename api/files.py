from flask import request, jsonify, send_file
from io import BytesIO

from core.storage import get_storage_service
from utils.validation import ValidationError

def register_file_routes(app):
    """Register file-related routes with the Flask app."""
    
    @app.route("/api/files", methods=["POST"])
    def upload_file():
        """Upload a file."""
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
            
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
            
        try:
            storage = get_storage_service()
            file_info = storage.upload_file(file)
            
            return jsonify(file_info), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/files/<file_id>", methods=["GET"])
    def download_file(file_id):
        """Download a file."""
        try:
            storage = get_storage_service()
            file_data = storage.download_file(file_id)
            
            # Create a BytesIO object from the file data
            file_stream = BytesIO(file_data.read())
            file_stream.seek(0)
            
            # Get file info for content type and original filename
            file_info = storage.get_file_info(file_id)
            
            return send_file(
                file_stream,
                mimetype=file_info.get("content_type", "application/octet-stream"),
                as_attachment=True,
                download_name=file_info.get("original_filename", file_id)
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/files/<file_id>", methods=["DELETE"])
    def delete_file(file_id):
        """Delete a file."""
        try:
            storage = get_storage_service()
            result = storage.delete_file(file_id)
            
            return jsonify({"success": True, "message": "File deleted successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/files/<file_id>/info", methods=["GET"])
    def get_file_info(file_id):
        """Get file information."""
        try:
            storage = get_storage_service()
            file_info = storage.get_file_info(file_id)
            
            return jsonify(file_info), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/files", methods=["GET"])
    def list_files():
        """List files."""
        try:
            prefix = request.args.get("prefix")
            
            storage = get_storage_service()
            files = storage.list_files(prefix)
            
            return jsonify({"files": files}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
