from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import json

from schemas.agents import AgentStatus, AgentLevel

class HumanAgentError(Exception):
    """Exception for human agent errors."""
    pass

class HumanAgent:
    """Represents a human agent that can assist with conversations."""
    
    def __init__(self, agent_id: str, name: str, level: AgentLevel, hourly_rate: float):
        """Initialize a human agent."""
        self.id = agent_id
        self.name = name
        self.level = level
        self.hourly_rate = hourly_rate
        self.status = AgentStatus.OFFLINE
        self.specialties = []
        self.languages = []
        self.rating = None
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
    def to_dict(self) -> Dict:
        """Convert agent to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "hourly_rate": self.hourly_rate,
            "status": self.status,
            "specialties": self.specialties,
            "languages": self.languages,
            "rating": self.rating,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class HumanAgentManager:
    """Manager for human agents."""
    
    def __init__(self, db_manager):
        """Initialize the human agent manager."""
        self.db_manager = db_manager
        
    def register_agent(self, agent_data: Dict) -> Dict:
        """
        Register a new human agent.
        
        Args:
            agent_data: Data for the new agent
            
        Returns:
            Dict: The created agent
        """
        try:
            # Validate required fields
            required_fields = ["name", "level", "hourly_rate"]
            for field in required_fields:
                if field not in agent_data:
                    raise HumanAgentError(f"Missing required field: {field}")
            
            # Validate level
            try:
                level = agent_data["level"]
                if isinstance(level, str):
                    level = AgentLevel(level)
            except ValueError:
                raise HumanAgentError(f"Invalid agent level: {agent_data['level']}")
            
            # Validate hourly rate
            if not isinstance(agent_data["hourly_rate"], (int, float)) or agent_data["hourly_rate"] <= 0:
                raise HumanAgentError(f"Invalid hourly rate: {agent_data['hourly_rate']}")
            
            # Create agent in database
            return self.db_manager.create_agent(agent_data)
        except Exception as e:
            if isinstance(e, HumanAgentError):
                raise
            raise HumanAgentError(f"Error registering agent: {str(e)}")
    
    def update_agent_status(self, agent_id: str, status: AgentStatus) -> Dict:
        """
        Update an agent's status.
        
        Args:
            agent_id: ID of the agent
            status: New status
            
        Returns:
            Dict: The updated agent
        """
        try:
            # Validate status
            try:
                if isinstance(status, str):
                    status = AgentStatus(status)
            except ValueError:
                raise HumanAgentError(f"Invalid agent status: {status}")
            
            # Update in database
            return self.db_manager.update_agent(agent_id, {"status": status.value})
        except Exception as e:
            if isinstance(e, HumanAgentError):
                raise
            raise HumanAgentError(f"Error updating agent status: {str(e)}")
    
    def find_available_agent(self, requirements: Dict) -> Optional[Dict]:
        """
        Find an available agent matching the requirements.
        
        Args:
            requirements: Requirements for the agent
            
        Returns:
            Optional[Dict]: Matching agent or None
        """
        try:
            # Get all agents from database
            with self.db_manager.db_name.connect() as conn:
                conn.row_factory = dict
                cursor = conn.cursor()
                
                # Base query for available agents
                query = """
                SELECT * FROM agents WHERE status = 'available'
                """
                params = []
                
                # Add filters based on requirements
                if "preferred_language" in requirements:
                    # This is a simplification, in reality we'd need to do a proper JSON search
                    query += f" AND languages LIKE ?"
                    params.append(f"%{requirements['preferred_language']}%")
                
                if "preferred_level" in requirements:
                    level = requirements["preferred_level"]
                    try:
                        if isinstance(level, str):
                            level = AgentLevel(level)
                        query += f" AND level = ?"
                        params.append(level.value)
                    except ValueError:
                        # Invalid level, ignore this filter
                        pass
                
                # Execute query
                cursor.execute(query, params)
                agents = cursor.fetchall()
                
                # Further filter by specialties if needed
                if "required_specialties" in requirements and requirements["required_specialties"]:
                    filtered_agents = []
                    for agent in agents:
                        specialties = json.loads(agent["specialties"]) if agent["specialties"] else []
                        
                        # Check if agent has all required specialties
                        has_all_specialties = True
                        for specialty in requirements["required_specialties"]:
                            if specialty not in specialties:
                                has_all_specialties = False
                                break
                                
                        if has_all_specialties:
                            filtered_agents.append(agent)
                            
                    agents = filtered_agents
                
                # Return the first matching agent, if any
                return agents[0] if agents else None
                
        except Exception as e:
            raise HumanAgentError(f"Error finding available agent: {str(e)}")
    
    def handoff_conversation(self, conversation_id: str, requirements: Dict) -> Dict:
        """
        Hand off a conversation to a human agent.
        
        Args:
            conversation_id: ID of the conversation
            requirements: Requirements for the agent
            
        Returns:
            Dict: Result of the handoff
        """
        try:
            # Find an available agent
            agent = self.find_available_agent(requirements)
            
            if not agent:
                return {
                    "success": False,
                    "message": "No available agents matching the requirements"
                }
            
            # Create a record of the handoff
            handoff_id = str(uuid.uuid4())
            
            with self.db_manager.db_name.connect() as conn:
                cursor = conn.cursor()
                
                # Record the handoff
                cursor.execute(
                    """
                    INSERT INTO agent_conversations
                    (id, agent_id, conversation_id, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (handoff_id, agent["id"], conversation_id, "active")
                )
                
                # Update agent status to busy
                cursor.execute(
                    """
                    UPDATE agents
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    ("busy", datetime.now().isoformat(), agent["id"])
                )
                
                # Add a system message to the conversation
                message_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO messages
                    (id, conversation_id, role, content)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        message_id,
                        conversation_id,
                        "system",
                        f"Conversation handed off to human agent: {agent['name']}"
                    )
                )
                
                # Update the conversation's updated_at timestamp
                cursor.execute(
                    """
                    UPDATE conversations
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (datetime.now().isoformat(), conversation_id)
                )
                
                conn.commit()
            
            return {
                "success": True,
                "message": f"Conversation handed off to agent {agent['name']}",
                "handoff_id": handoff_id,
                "agent": agent
            }
        except Exception as e:
            raise HumanAgentError(f"Error in conversation handoff: {str(e)}")
    
    def end_conversation(self, conversation_id: str) -> Dict:
        """
        End a conversation with a human agent.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dict: Result of ending the conversation
        """
        try:
            with self.db_manager.db_name.connect() as conn:
                conn.row_factory = dict
                cursor = conn.cursor()
                
                # Find the active agent conversation
                cursor.execute(
                    """
                    SELECT * FROM agent_conversations
                    WHERE conversation_id = ? AND status = 'active'
                    """,
                    (conversation_id,)
                )
                
                agent_conversation = cursor.fetchone()
                
                if not agent_conversation:
                    return {
                        "success": False,
                        "message": "No active human agent for this conversation"
                    }
                
                # Calculate duration
                start_time = datetime.fromisoformat(agent_conversation["start_time"])
                end_time = datetime.now()
                duration_minutes = (end_time - start_time).total_seconds() / 60
                
                # Update the agent conversation
                cursor.execute(
                    """
                    UPDATE agent_conversations
                    SET status = ?, end_time = ?, duration_minutes = ?
                    WHERE id = ?
                    """,
                    (
                        "completed",
                        end_time.isoformat(),
                        duration_minutes,
                        agent_conversation["id"]
                    )
                )
                
                # Update agent status back to available
                cursor.execute(
                    """
                    UPDATE agents
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    ("available", end_time.isoformat(), agent_conversation["agent_id"])
                )
                
                # Add a system message to the conversation
                message_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO messages
                    (id, conversation_id, role, content)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        message_id,
                        conversation_id,
                        "system",
                        f"Conversation with human agent ended. Duration: {duration_minutes:.2f} minutes"
                    )
                )
                
                # Update the conversation's updated_at timestamp
                cursor.execute(
                    """
                    UPDATE conversations
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (end_time.isoformat(), conversation_id)
                )
                
                conn.commit()
                
                # Get agent details
                cursor.execute(
                    """
                    SELECT * FROM agents WHERE id = ?
                    """,
                    (agent_conversation["agent_id"],)
                )
                
                agent = cursor.fetchone()
                
                # Calculate cost based on hourly rate
                hourly_rate = agent["hourly_rate"]
                cost = (hourly_rate / 60) * duration_minutes
                
                return {
                    "success": True,
                    "message": "Conversation with human agent ended",
                    "agent_id": agent_conversation["agent_id"],
                    "agent_name": agent["name"],
                    "duration_minutes": duration_minutes,
                    "cost": cost
                }
                
        except Exception as e:
            raise HumanAgentError(f"Error ending conversation: {str(e)}")
    
    def rate_agent(self, agent_id: str, rating: float, feedback: str = "") -> Dict:
        """
        Rate a human agent.
        
        Args:
            agent_id: ID of the agent
            rating: Rating (1-5)
            feedback: Optional feedback
            
        Returns:
            Dict: Result of rating the agent
        """
        try:
            # Validate rating
            if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
                raise HumanAgentError("Rating must be between 1 and 5")
            
            rating_id = str(uuid.uuid4())
            
            with self.db_manager.db_name.connect() as conn:
                cursor = conn.cursor()
                
                # Get the user ID from an active conversation
                cursor.execute(
                    """
                    SELECT c.user_id
                    FROM agent_conversations ac
                    JOIN conversations c ON ac.conversation_id = c.id
                    WHERE ac.agent_id = ? AND ac.status = 'completed'
                    ORDER BY ac.end_time DESC
                    LIMIT 1
                    """,
                    (agent_id,)
                )
                
                result = cursor.fetchone()
                
                if not result:
                    raise HumanAgentError(f"No completed conversations found for agent {agent_id}")
                    
                user_id = result[0]
                
                # Add the rating
                cursor.execute(
                    """
                    INSERT INTO agent_ratings
                    (id, agent_id, user_id, rating, feedback)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (rating_id, agent_id, user_id, rating, feedback)
                )
                
                conn.commit()
                
                # Calculate new average rating
                cursor.execute(
                    """
                    SELECT AVG(rating) as avg_rating
                    FROM agent_ratings
                    WHERE agent_id = ?
                    """,
                    (agent_id,)
                )
                
                avg_rating = cursor.fetchone()[0]
                
                return {
                    "success": True,
                    "message": "Agent rated successfully",
                    "rating_id": rating_id,
                    "agent_id": agent_id,
                    "rating": rating,
                    "average_rating": avg_rating
                }
                
        except Exception as e:
            if isinstance(e, HumanAgentError):
                raise
            raise HumanAgentError(f"Error rating agent: {str(e)}")
    
    def get_agent_statistics(self, agent_id: str, time_period: Optional[timedelta] = None) -> Dict:
        """
        Get statistics for an agent.
        
        Args:
            agent_id: ID of the agent
            time_period: Optional time period to filter by
            
        Returns:
            Dict: Agent statistics
        """
        try:
            with self.db_manager.db_name.connect() as conn:
                conn.row_factory = dict
                cursor = conn.cursor()
                
                # Get agent details
                cursor.execute(
                    """
                    SELECT * FROM agents WHERE id = ?
                    """,
                    (agent_id,)
                )
                
                agent = cursor.fetchone()
                
                if not agent:
                    raise HumanAgentError(f"Agent {agent_id} not found")
                
                # Build the time filter if needed
                time_filter = ""
                params = [agent_id]
                
                if time_period:
                    cutoff_time = (datetime.now() - time_period).isoformat()
                    time_filter = "AND start_time >= ?"
                    params.append(cutoff_time)
                
                # Get conversation statistics
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(*) as total_conversations,
                        SUM(duration_minutes) as total_minutes,
                        AVG(duration_minutes) as avg_minutes
                    FROM agent_conversations
                    WHERE agent_id = ? {time_filter} AND status = 'completed'
                    """,
                    params
                )
                
                stats = cursor.fetchone()
                
                # Get rating statistics
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(*) as total_ratings,
                        AVG(rating) as avg_rating,
                        MIN(rating) as min_rating,
                        MAX(rating) as max_rating
                    FROM agent_ratings
                    WHERE agent_id = ? {time_filter}
                    """,
                    params
                )
                
                rating_stats = cursor.fetchone()
                
                # Calculate earnings
                total_minutes = stats["total_minutes"] or 0
                hourly_rate = agent["hourly_rate"]
                total_earnings = (hourly_rate / 60) * total_minutes
                
                return {
                    "agent_id": agent_id,
                    "agent_name": agent["name"],
                    "total_conversations": stats["total_conversations"],
                    "total_minutes": total_minutes,
                    "average_minutes_per_conversation": stats["avg_minutes"],
                    "total_earnings": total_earnings,
                    "total_ratings": rating_stats["total_ratings"],
                    "average_rating": rating_stats["avg_rating"],
                    "minimum_rating": rating_stats["min_rating"],
                    "maximum_rating": rating_stats["max_rating"]
                }
                
        except Exception as e:
            if isinstance(e, HumanAgentError):
                raise
            raise HumanAgentError(f"Error getting agent statistics: {str(e)}")

# Function to get singleton instance
_human_agent_manager_instance = None

def get_human_agent_manager(db_manager=None):
    """Get the singleton human agent manager instance."""
    global _human_agent_manager_instance
    if _human_agent_manager_instance is None:
        from services.database import get_db_manager
        db = db_manager or get_db_manager()
        _human_agent_manager_instance = HumanAgentManager(db)
    return _human_agent_manager_instance
