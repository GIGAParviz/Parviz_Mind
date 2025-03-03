import os

class Config:
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    SWAGGER_URL = "/swagger"
    API_URL = "/static/swagger.json"
    
    # MinIO Configuration
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
    MINIO_SECURE = os.getenv('MINIO_SECURE', 'True').lower() == 'true'
    MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'parviz-mind')
    
    # API Keys and Tokens
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'chat_history.db')
    
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set."""
        required_vars = [
            'MINIO_ENDPOINT',
            'MINIO_ACCESS_KEY',
            'MINIO_SECRET_KEY',
            'HUGGINGFACE_TOKEN',
            'GROQ_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
