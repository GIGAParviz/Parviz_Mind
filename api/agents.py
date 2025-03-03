from flask import Blueprint, request, jsonify

from schemas.agents import AgentCreate, AgentUpdate
from services.human_agent import HumanAgentManager
from services.database import get_db_manager
from utils.validation import ValidationError

def register_agent_routes(app):
    """Register agent-related routes with the Flask app."""
    
    @app.route("/api/agents", methods=["POST"])
    def create_agent():
        """Create a new agent."""
        data = request.json
        
        try:
            agent_data = AgentCreate(**data).dict()
            db_manager = get_db_manager()
            agent_manager = HumanAgentManager(db_manager)
            result = agent_manager.register_agent(agent_data)
            
            return jsonify(result), 201
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/agents/<agent_id>", methods=["PUT"])
    def update_agent(agent_id):
        """Update an existing agent."""
        data = request.json
        
        try:
            agent_data = AgentUpdate(**data).dict(exclude_unset=True)
            db_manager = get_db_manager()
            agent_manager = HumanAgentManager(db_manager)
            result = agent_manager.update_agent(agent_id, agent_data)
            
            return jsonify(result), 200
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/agents/<agent_id>", methods=["GET"])
    def get_agent(agent_id):
        """Get agent details."""
        try:
            db_manager = get_db_manager()
            agent_manager = HumanAgentManager(db_manager)
            result = agent_manager.get_agent(agent_id)
            
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/agents/<agent_id>", methods=["DELETE"])
    def delete_agent(agent_id):
        """Delete an agent."""
        try:
            db_manager = get_db_manager()
            agent_manager = HumanAgentManager(db_manager)
            result = agent_manager.delete_agent(agent_id)
            
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    @app.route("/api/agents/<agent_id>/status", methods=["PUT"])
    def update_agent_status(agent_id):
        """Update an agent's status."""
        data = request.json
        
        try:
            status = data.get("status")
            if not status:
                raise ValidationError("Status is required")
                
            db_manager = get_db_manager()
            agent_manager = HumanAgentManager(db_manager)
            result = agent_manager.update_agent_status(agent_id, status)
            
            return jsonify(result), 200
        except ValidationError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500