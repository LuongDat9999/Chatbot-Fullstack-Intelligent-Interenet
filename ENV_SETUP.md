# Environment Setup

## API (.env)
Create `api/.env` with the following content:
```
# OpenAI Configuration
OPENAI_API_KEY=your-openrouter-api-key-here

# File Upload Configuration
MAX_UPLOAD_MB=10

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,http://web:5173

# Database Configuration
DATABASE_URL=sqlite:///./storage/messages.db

# Application Configuration
DEBUG=True
LOG_LEVEL=info
```

## Web (.env)
Create `web/.env` with the following content:
```
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=AI Fullstack Assignment
VITE_APP_VERSION=1.0.0
```

## LLM Service

The application now includes a modular LLM service (`services/llm.py`) with the following features:

### Functions
- `chat(messages: List[Dict[str, str]]) -> str` - OpenAI Chat Completion
- `vision(image_bytes: bytes, question: str) -> str` - OpenAI Vision API
- `is_api_key_configured() -> bool` - Check API key status

### Mock Mode
- **No API Key**: Returns deterministic mock responses for local development
- **Invalid API Key**: Falls back to mock responses with error handling
- **Valid API Key**: Uses real OpenAI/OpenRouter API calls

### Mock Responses
- **Chat**: "🤖 [Mock Response] I'm a helpful AI assistant! This is a mock response because no API key is configured..."
- **Vision**: "🖼️ [Mock Vision Response] In the uploaded image, I see various visual elements..."

## API Endpoints

### Chat Endpoints
- `POST /chat` - Send a message and get AI response
- `GET /messages?session_id=<id>` - Get conversation history

### Image Chat
- `POST /image-chat` - Upload image and ask questions (multipart form)

### CSV Analysis
- `POST /csv/upload` - Upload CSV file (multipart form)
- `POST /csv/url` - Download CSV from URL
- `GET /csv/missing?session_id=<id>` - Get column with most missing values
- `GET /csv/hist?session_id=<id>&col=<column>` - Get histogram as base64 PNG

### System Status
- `GET /health` - Health check with API key status

## Running the Application

1. Create the .env files as described above
2. Set your OpenRouter API key in `api/.env` (or leave as default for mock mode)
3. Run `docker compose up --build` from the root directory
4. Access the web app at http://localhost:5173
5. Access the API at http://localhost:8000
6. View API documentation at http://localhost:8000/docs
7. Check system status at http://localhost:8000/health
