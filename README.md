# Parviz Mind API

A powerful AI chatbot with human agent support.

## Project Structure

```
parviz-mind/
├── api/                  # API routes and endpoints
│   ├── __init__.py      # API module initialization
│   ├── agents.py        # Agent management endpoints
│   ├── chat.py          # Chat endpoints
│   └── files.py         # File management endpoints
├── core/                 # Core functionality
│   ├── __init__.py      # Core module initialization
│   ├── ai.py            # AI processing
│   └── storage.py       # File storage service
├── schemas/             # Data validation schemas
│   ├── __init__.py      # Schema module initialization
│   ├── base.py          # Base schemas
│   ├── chat.py          # Chat schemas
│   └── agents.py        # Agent schemas
├── services/            # Business logic services
│   ├── __init__.py      # Services module initialization
│   ├── database.py      # Database operations
│   ├── knowledge_base.py# Knowledge base management
│   └── human_agent.py   # Human agent management
├── utils/               # Utility functions
│   ├── __init__.py      # Utils module initialization
│   ├── validation.py    # Data validation
│   ├── language.py      # Language support
│   └── response.py      # Response handling
├── static/              # Static files
│   └── swagger.json     # API documentation
├── config.py            # App configuration
├── app.py               # Main application
├── gunicorn_config.py   # Gunicorn server config
├── requirements.txt     # Dependencies
└── .env                 # Environment variables
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd parviz-mind
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your credentials

5. Start the development server:
   ```
   python app.py
   ```

6. For production deployment:
   ```
   gunicorn -c gunicorn_config.py "app:create_app()"
   ```

## API Documentation

The API documentation is available through Swagger UI:

- Development: `http://localhost:5000/swagger`
- Production: `https://your-domain.com/swagger`

## Key Components

### AI Core

The AI Core handles natural language processing using powerful LLM models like Llama 3. It supports:
- Multiple languages (English, Persian)
- Different response styles
- File processing
- Token counting and pricing

### Storage Service

File storage is managed through MinIO, an S3-compatible object storage service. The storage service provides:
- File upload/download
- File metadata
- Object lifecycle management

### Database

SQLite is used for storing conversations, messages, agent information, and ratings. Key tables:
- users
- agents
- agent_ratings
- conversations
- messages
- summaries
- agent_conversations

### Human Agent System

The system supports human handoff for complex queries, with features including:
- Agent registration and management
- Agent status tracking
- Conversation handoff
- Performance metrics and ratings

## Development Guidelines

1. **Code Style**: Follow PEP 8 guidelines for Python code.
2. **Error Handling**: Use appropriate exception handling and return proper HTTP status codes.
3. **Testing**: Write unit tests for new functionality.
4. **Documentation**: Update API documentation when endpoints change.
5. **Security**: Never commit sensitive information or credentials.

## Environment Variables

Required environment variables:

- `FLASK_DEBUG`: Set to "True" for development mode
- `MINIO_ENDPOINT`: MinIO server address
- `MINIO_ACCESS_KEY`: MinIO access key
- `MINIO_SECRET_KEY`: MinIO secret key
- `MINIO_SECURE`: Whether to use HTTPS for MinIO
- `MINIO_BUCKET`: MinIO bucket name
- `HUGGINGFACE_TOKEN`: Token for Hugging Face API
- `GROQ_API_KEY`: API key for Groq services
- `DATABASE_PATH`: Path to SQLite database file

## Contact

For questions or support, contact the development team at dev@parviz-mind.com 