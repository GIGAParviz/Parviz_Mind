import re
from typing import Dict, List, Optional, Any

from transformers import AutoTokenizer
import tiktoken
from langchain_groq import ChatGroq

from services.database import get_db_manager
from utils.language import Language, ResponseLength, ResponseStyle
from config import Config

class AICore:
    """Core AI functionality for handling chat interactions."""
    
    def __init__(self):
        """Initialize the AI core with necessary models and tokenizers."""
        self._db_manager = get_db_manager()
        self._tokenizers = {}
        self._models = {}
        self._conversation_history = []
        self.api_key = Config.GROQ_API_KEY
        self.default_model = "llama"
        
        # Initialize tokenizers
        self._init_tokenizers()
        
    def _init_tokenizers(self):
        """Initialize tokenizers for different models."""
        # Load tokenizers for different models
        self._tokenizers = {
            "deepseek": AutoTokenizer.from_pretrained("deepseek-ai/deepseek-llm-7b-base", token=Config.HUGGINGFACE_TOKEN),
            "llama": AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b", token=Config.HUGGINGFACE_TOKEN),
            "gemma": AutoTokenizer.from_pretrained("google/gemma-7b", token=Config.HUGGINGFACE_TOKEN),
        }
    
    def _get_appropriate_tokenizer(self, model_name):
        """Get the appropriate tokenizer for the model."""
        if model_name in self._tokenizers:
            return self._tokenizers[model_name]
        else:
            # Default to llama tokenizer as fallback
            return self._tokenizers["llama"]
    
    def _init_model(self, model_name=None):
        """Initialize a model using ChatGroq."""
        if not model_name:
            model_name = self.default_model
            
        # Create model with ChatGroq
        return ChatGroq(api_key=self.api_key, model_name=model_name)
    
    def summarize_chat(self):
        """Summarize the current conversation."""
        # Implementation for summarizing the conversation
        summary = "Chat summary placeholder"  # Replace with actual summarization logic
        self._db_manager.save_summary({"summary": summary})
        return summary
    
    def process_file(self, file_obj):
        """Process an uploaded file."""
        if not file_obj:
            return None
            
        file_content = ""
        
        try:
            # Extract text from file based on file type
            if file_obj["content_type"].startswith("text/"):
                # For text files, simply read the content
                file_content = file_obj["data"].decode("utf-8")
            elif file_obj["content_type"] in ["application/pdf"]:
                # For PDFs, use a PDF extraction library (implementation needed)
                file_content = "PDF content extraction placeholder"
            elif file_obj["content_type"] in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                # For Word documents, use a Word extraction library (implementation needed)
                file_content = "Word document content extraction placeholder"
                
            return file_content
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            return None
    
    def count_tokens(self, text, model_name=None):
        """Count the number of tokens in the text for the specified model."""
        if not model_name:
            model_name = self.default_model
            
        tokenizer = self._get_appropriate_tokenizer(model_name)
        
        if hasattr(tokenizer, "encode"):
            return len(tokenizer.encode(text))
        else:
            return len(tokenizer.encode(text, disallowed_special=()))
    
    def calculate_price(self, input_text, output_text, model_name=None):
        """Calculate the price for the input and output text."""
        if not model_name:
            model_name = self.default_model
            
        # Token prices per 1K tokens (example values)
        prices = {
            "deepseek": {"input": 0.0001, "output": 0.0002},
            "llama": {"input": 0.0001, "output": 0.0002},
            "gemma": {"input": 0.0001, "output": 0.0002},
        }
        
        input_tokens = self.count_tokens(input_text, model_name)
        output_tokens = self.count_tokens(output_text, model_name)
        
        if model_name in prices:
            input_price = (input_tokens / 1000) * prices[model_name]["input"]
            output_price = (output_tokens / 1000) * prices[model_name]["output"]
            return input_price + output_price
        else:
            return 0.0  # Default price
    
    def remove_think_sections(self, response_text):
        """Remove <thinking> sections from response text."""
        return re.sub(r'<thinking>.*?</thinking>', '', response_text, flags=re.DOTALL)
    
    def filter_to_persian(self, text):
        """Filter text to keep only Persian characters."""
        return re.sub(r'[^\u0600-\u06FF\s]+', '', text)
    
    def answer_query(self, user_id, query, file_obj=None, summarize=False, 
                     tone=ResponseStyle.CONVERSATIONAL, model_name="llama", 
                     creativity=0.7, keywords=None, language=Language.ENGLISH, 
                     response_length=ResponseLength.MEDIUM, welcome_message=False, 
                     exclusion_words=None, main_prompt=None, chatbot_name="Parviz"):
        """
        Process a user query and generate a response.
        
        Args:
            user_id: The ID of the user making the query
            query: The text of the user's query
            file_obj: Optional file object if a file was uploaded
            summarize: Whether to summarize the conversation
            tone: The desired tone of the response
            model_name: The model to use for generating the response
            creativity: Creativity level (0.0 to 1.0)
            keywords: Optional keywords to include in the response
            language: The language for the response
            response_length: Desired length of the response
            welcome_message: Whether this is a welcome message
            exclusion_words: Words to exclude from the response
            main_prompt: Optional custom prompt to use
            chatbot_name: The name of the chatbot
            
        Returns:
            dict: The response data including the generated text
        """
        try:
            # Process file if provided
            file_content = self.process_file(file_obj) if file_obj else None
            
            # Create conversation if it's a new one
            conversation_id = None
            if not self._conversation_history:
                conversation_data = {
                    "user_id": user_id,
                    "title": query[:50] + "..." if len(query) > 50 else query,
                    "model": model_name,
                    "language": language.value
                }
                conversation_id = self._db_manager.create_conversation(conversation_data).get("id")
            
            # Build the prompt
            system_prompt = main_prompt or f"""You are {chatbot_name}, an AI assistant. 
            Respond in a {tone.value} tone with a {response_length.value} response.
            """
            
            if keywords:
                system_prompt += f" Include these keywords if relevant: {', '.join(keywords)}."
                
            if exclusion_words:
                system_prompt += f" Avoid using these words: {', '.join(exclusion_words)}."
                
            if file_content:
                system_prompt += f"\nHere is the content of the uploaded file to reference:\n{file_content}\n"
                
            if language == Language.PERSIAN:
                system_prompt += "\nRespond in Persian language only."
                
            # Set up the conversation
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in self._conversation_history:
                messages.append(msg)
                
            # Add the current user query
            messages.append({"role": "user", "content": query})
            
            # Initialize the model with ChatGroq
            model = self._init_model(model_name)
            
            # Generate the response using ChatGroq
            response = model.invoke(messages)
            ai_response = response.content
            
            # Process the response based on language
            if language == Language.PERSIAN:
                ai_response = self.filter_to_persian(ai_response)
                
            # Remove thinking sections if present
            ai_response = self.remove_think_sections(ai_response)
            
            # Store the message in history
            self._conversation_history.append({"role": "user", "content": query})
            self._conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Store in database
            self._db_manager.create_message({
                "conversation_id": conversation_id,
                "role": "user",
                "content": query
            })
            
            self._db_manager.create_message({
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": ai_response
            })
            
            # Summarize if requested
            summary = None
            if summarize:
                summary = self.summarize_chat()
                
            # Calculate price
            price = self.calculate_price(query, ai_response, model_name)
            
            return {
                "response": ai_response,
                "conversation_id": conversation_id,
                "model": model_name,
                "tokens": self.count_tokens(ai_response, model_name),
                "price": price,
                "summary": summary
            }
            
        except Exception as e:
            raise Exception(f"Error processing query: {str(e)}")
    
    def clear_history(self):
        """Clear the conversation history."""
        self._conversation_history = []

# Singleton instance
_ai_core_instance = None

def get_ai_core():
    """Get the singleton AI core instance."""
    global _ai_core_instance
    if _ai_core_instance is None:
        _ai_core_instance = AICore()
    return _ai_core_instance
