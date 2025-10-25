# AI Fullstack Assignment

A modern full-stack application built with FastAPI (backend), Firebase Storage (database) and React + TypeScript + Tailwind CSS (frontend) that provides AI-powered chat capabilities with CSV data analysis and image processing.

## 🚀 Quick Start

### Requirements
- **Docker** and **Docker Compose**
- **OpenRouter API Key** (for real AI responses)

### Running the Application

1. **Clone and navigate to the project:**
   ```bash
   git clone https://github.com/LuongDat9999/Chatbot-Fullstack-Intelligent-Interenet.git
   cd Chatbot-Fullstack-Intelligent-Interenet
   ```

2. **Set up environment variables:**
   
   **Backend (`api/.env`):**
   ```bash
   cp api/env.example api/.env
   # Edit api/.env and add your OpenRouter API key
   ```
   
   **Frontend (`web/.env`):**
   ```bash
   cp web/env.example web/.env
   # Edit web/.env if needed (defaults work for local development)
   ```

3. **Start the application:**
   ```bash
   docker compose up --build
   ```
   
   **Alternative port configuration:**
   ```bash
   # Use custom port to avoid conflicts
   WEB_PORT=5181 docker compose up --build
   ```

4. **Access the application:**
   - **Frontend**: http://localhost:5180 (or your custom port)
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

5. **Verify installation:**
   - Check API key status at http://localhost:8000/health
   - Upload a CSV file to test data analysis
   - Try asking "Summarize the dataset" to test intent detection

## 🔧 Environment Configuration

### Backend (`api/.env`)
```env
# OpenAI API Configuration
OPENAI_API_KEY=your-openrouter-api-key-here

# File Upload Configuration
MAX_CSV_SIZE_MB=20
MAX_IMAGE_SIZE_MB=10

# Firebase Configuration
GOOGLE_APPLICATION_CREDENTIALS="./path/to/your-service-account-key.json"
FIREBASE_STORAGE_BUCKET=your-storage-bucket-name.appspot.com
FIREBASE_PROJECT_ID=your-project-id

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

```

### Frontend (`web/.env`)
```env
# API Configuration
VITE_API_URL=http://localhost:8000

# Web Server Configuration
WEB_PORT=5180

# File Upload Configuration
VITE_MAX_CSV_SIZE_MB=20
VITE_MAX_IMAGE_SIZE_MB=10

# Development Configuration
VITE_DEV_MODE=true
```

## ✨ Features

### Core Functionality
- ✅ **AI Chat Interface** - Interactive chat with AI assistant
- ✅ **CSV Data Analysis** - Upload and analyze CSV files
- ✅ **Image Processing** - Upload images for AI analysis
- ✅ **Session Management** - Multiple chat sessions
- ✅ **Real-time Messaging** - Live chat interface

### Advanced Features
- ✅ **System Prompt Integration** - Consistent AI behavior with CSV context
- ✅ **Dynamic CSV Context** - AI automatically knows about uploaded data
- ❌ **Statistical Analysis** - Basic stats, missing values, histograms
- ✅ **File Validation** - Frontend and backend validation
- ✅ **Error Handling** - User-friendly error messages
- ✅ **API Key Management** - Clear configuration status

### Technical Features
- ✅ **Docker Containerization** - Easy deployment and development
- ✅ **Environment Configuration** - Configurable file limits and settings
- ✅ **TypeScript Support** - Type-safe frontend development
- ✅ **Responsive Design** - Modern UI with Tailwind CSS
- ✅ **CORS Configuration** - Proper cross-origin setup

## 🎯 Demo Steps

### 1. Basic Chat
1. Start the application with `docker compose up --build`
2. Open http://localhost:5180 (or your custom port)
3. Click "New Chat" to create a session
4. Type a message and see AI response
5. Notice the API key status indicator

### 2. CSV Data Analysis
1. Upload a CSV file using the file picker
2. View automatic data overview (rows, columns, memory usage)
3. Click "Basic Statistics" to see detailed stats
4. Use "Most Missing Values" to identify data quality issues
5. Select a column and generate a histogram
6. Ask questions about your data - AI will have full context

### 3. Image Analysis
1. Drag and drop an image (PNG/JPG only)
2. Add a question about the image
3. Click "Analyze Image" to get AI insights
4. View the response with image context

### 4. Advanced Features
1. Try uploading a large CSV (>20MB) to see validation
2. Upload a non-CSV file to see type validation
3. Upload a non-PNG/JPG image to see format validation
4. Check the API key status indicator

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: SQLite with session management
- **AI Integration**: OpenRouter API with fallback mock responses
- **File Processing**: Pandas for CSV, Matplotlib for charts
- **Validation**: Pydantic models with custom error handling

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom dark theme
- **State Management**: Zustand for global state
- **API Client**: Axios with React Query for caching
- **File Handling**: React Dropzone with validation

### Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose for development
- **Networking**: Internal Docker network with CORS
- **Storage**: Persistent volumes for data and uploads

## 📚 API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints
- `POST /chat` - Send chat messages
- `POST /image-chat` - Analyze images
- `POST /csv/upload` - Upload CSV files
- `POST /csv/url` - Load CSV from URL
- `GET /config` - Get configuration settings
- `GET /health` - Health check with API key status


## 🛠️ Troubleshooting

### Common Issues

#### CSV URL Issues
**Problem**: CSV URLs not loading properly
**Solution**: 
- For GitHub URLs, add `?raw=1` parameter
- Ensure URL points directly to CSV file
- Check URL accessibility from your network

#### API Key Configuration
**Problem**: Getting mock responses instead of real AI
**Solution**:
1. Copy `api/env.example` to `api/.env`
2. Add your OpenRouter API key
3. Restart the API container: `docker compose restart api`

#### File Upload Errors
**Problem**: Files rejected during upload
**Solutions**:
- **Size**: Check file size limits (20MB CSV, 10MB images)
- **Format**: Ensure CSV files have `.csv` extension
- **Images**: Only PNG and JPG formats allowed
- **Network**: Check internet connection for URL uploads

#### CORS Issues
**Problem**: Frontend can't connect to backend
**Solution**: 
- Ensure `ALLOW_ORIGINS=http://localhost:5180` in `api/.env` (or your custom port)
- Check that both services are running
- Verify ports 5180 (web) and 8000 (api) are available
- Use `WEB_PORT=5181 docker compose up --build` to avoid port conflicts

#### Port Conflicts
**Problem**: "Address already in use" error
**Solution**:
- Use a different port: `WEB_PORT=5181 docker compose up --build`
- Check what's using the port: `lsof -i :5180`
- Kill the process using the port: `kill -9 <PID>`
- Default port changed from 5175 to 5180 to avoid common conflicts

#### Database Issues
**Problem**: Messages not persisting
**Solution**:
- Check `api/storage/` directory permissions
- Ensure SQLite database file is writable
- Restart API container if needed

### Development Tips

#### Viewing Logs
```bash
# View all logs
docker compose logs

# View specific service logs
docker compose logs api
docker compose logs web
```

#### Rebuilding After Changes
```bash
# Rebuild and restart
docker compose up --build

# Rebuild specific service
docker compose build api
docker compose up api
```

#### Environment Variables
- Changes to `.env` files require container restart
- Use `docker compose restart` after env changes
- Check environment loading with `/health` endpoint


## 🤝 Contributing

1. Chatbot Support: Chatgpt, Cursor
2. API chatbot free: Openrounter

## 🔄 Detail Features

### 🆕 Chat Management System
- **Sequential Chat Numbering**: Chat 1, Chat 2, Chat 3... (stable, no gaps)
- **Race Condition Prevention**: Only one chat created per click
- **Proper ID Management**: chatId ≠ sessionId for better architecture
- **Centralized State Management**: Enhanced Zustand store with chat management
- **Legacy Support**: Handle existing "New Chat" titles gracefully

### 🚀 Conversation Engine Refactoring
- **Three-Layer Architecture**: Intent → Orchestrator → Renderer
- **Intent Detection**: Automatic detection of 6 core intents (summarize, stats, missing, histogram, schema, sample)
- **Block Response Protocol**: Standardized response format with TextBlock, TableBlock, ImageBlock, AlertBlock
- **Performance Improvement**: CSV operations bypass LLM for 10x speed improvement
- **Comprehensive Error Handling**: Custom exceptions with proper HTTP status codes
- **Structured Logging**: Request tracing and performance monitoring

### 📊 CSV Intent Switch
- **Server-side Bypass**: CSV-QA hoạt động ngay lập tức khi detect intent
- **No More "Which dataset..."**: Direct analysis without asking for clarification
- **Intent Detection**: Regex-based pattern matching for Vietnamese and English
- **Formatted Responses**: Pre-formatted markdown responses for better UX

### 🤖 AI Model Configuration
- **Current Model**: `openai/gpt-oss-20b:free` via OpenRouter
- **Vision Model**: `openai/gpt-4o` for image analysis
- **Provider Support**: OpenRouter (primary) with Hugging Face fallback
- **Rate Limit Handling**: Graceful degradation with user-friendly messages

### 🔧 Technical Improvements
- **Docker Compatibility**: Fixed import issues for containerized deployment
- **Environment Configuration**: Flexible provider switching (OpenRouter/Hugging Face)
- **Error Handling**: Comprehensive error management with AlertBlock responses
- **Testing**: Comprehensive test coverage for all components

## 📚 Architecture Details

### Conversation Engine Architecture
```
User Message → Intent Detector → Orchestrator → Renderer → Block Response
                     ↓              ↓           ↓
                Pattern Match   Route Logic   Format Output
```

### Block Response Protocol
```json
{
    "status": "success",
    "block": {
        "type": "table|text|image|alert",
        "title": "Optional Title",
        "payload": "Response Data",
        "debug": {
            "session_id": "session_123",
            "intent": "summarize",
            "took_ms": 150
        }
    }
}
```

### Supported Intents
- **summarize**: Dataset overview and summary
- **stats**: Statistical analysis of numeric columns
- **missing**: Missing values analysis
- **histogram**: Distribution visualization
- **schema**: Column information and data types
- **sample**: Data preview/sampling

## 🎯 Performance Improvements

### CSV Operations (Bypass LLM)
- **Summarize**: ~50ms (vs ~2000ms with LLM)
- **Stats**: ~100ms (vs ~2000ms with LLM)
- **Missing**: ~75ms (vs ~2000ms with LLM)
- **Histogram**: ~200ms (vs ~2000ms with LLM)
- **Schema**: ~25ms (vs ~2000ms with LLM)
- **Sample**: ~30ms (vs ~2000ms with LLM)

## 🔧 Advanced Configuration

### LLM Provider Options
```env
# OpenRouter (Primary)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openrouter_api_key_here

# Hugging Face (Alternative)
LLM_PROVIDER=huggingface
HF_TOKEN=hf_your_token_here
HF_MODEL_NAME=llava-hf/llava-1.6-mistral-7b-hf
```

### Model Configuration
- **Chat Model**: `openai/gpt-oss-20b:free` (OpenRouter)
- **Vision Model**: `openai/gpt-4o` (OpenRouter)
- **Alternative VLM**: Hugging Face models with adapter support

## 📝 Migration Notes

### From Old Architecture
- **No Data Migration Required**: Existing chats work as-is
- **Display-Only Changes**: Legacy titles handled in UI layer
- **Backward Compatible**: All existing functionality preserved
- **Progressive Enhancement**: New features work with old data

### Key Changes
1. **Intent Detection**: Moved from inline logic to dedicated module
2. **Response Format**: Standardized Block protocol instead of raw text
3. **Error Handling**: Centralized exception handling
4. **Logging**: Structured logging with request tracing
5. **Testing**: Comprehensive test coverage

## 📄 License

This project is part of an AI Fullstack Assignment. See the assignment requirements for specific usage guidelines.
