import os
import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import base64
import io
import requests
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage
from services.llm import chat, vision, is_api_key_configured
from services.csv_tools import (
    load_csv_from_upload, 
    load_csv_from_url, 
    basic_stats, 
    most_missing, 
    load_csv_from_path
)
from engine import run_orchestrator, Block, register_error_handlers
from data.csv_registry import registry, load_csv_for_session
from utils.logging import setup_logging, request_id_middleware

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
try:
    # Đường dẫn tương đối đến file key
    key_path = os.path.join(os.path.dirname(__file__), 'service-account-key.json') 

    # Đọc storageBucket ID từ file .env (ví dụ: 'chatbot-47fec.appspot.com')
    # Hãy chắc chắn bạn đã thêm FIREBASE_STORAGE_BUCKET vào .env
    bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET') 

    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred, {
        'storageBucket': bucket_name
    })
    db = firestore.client()
    bucket = storage.bucket()
    print("✅ Firebase Admin SDK initialized successfully.")
except Exception as e:
    db = None
    bucket = None
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print("🔥 FAILED TO INITIALIZE FIREBASE ADMIN SDK 🔥")
    print(f"Error: {e}")
    print("Chạy ở MOCK_MODE (nếu có) hoặc API sẽ không hoạt động.")
    print(traceback.format_exc())
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

# Configuration
MAX_CSV_SIZE_MB = int(os.getenv("MAX_CSV_SIZE_MB", "20"))
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
MAX_CSV_SIZE_BYTES = MAX_CSV_SIZE_MB * 1024 * 1024
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Get web port from environment
WEB_PORT = os.getenv("WEB_PORT", "5180")
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", f"http://localhost:{WEB_PORT}")

app = FastAPI(title="AI Fullstack Assignment API", version="1.0.0")

# Setup logging
setup_logging(debug=os.getenv("DEBUG", "false").lower() == "true")

# Add request ID middleware
app.add_middleware(request_id_middleware)

# Register error handlers
register_error_handlers(app)

# Configure CORS
origins = [
    f"http://localhost:{WEB_PORT}",
    "http://web:5173",  # Keep Docker internal communication
    ALLOW_ORIGINS  # Additional origins from environment
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log CORS configuration on startup
print(f"[API] CORS allowed origins: {origins}")

# Pydantic Schemas
class ChatRequest(BaseModel):
    chat_id: str
    message_id: str

class ChatResponse(BaseModel):
    status: str
    error: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime

class MessagesResponse(BaseModel):
    ok: bool
    messages: Optional[List[MessageResponse]] = None
    error: Optional[str] = None

class ImageChatRequest(BaseModel):
    session_id: str
    question: str

class ImageChatResponse(BaseModel):
    ok: bool
    assistant_message: Optional[str] = None
    text: Optional[str] = None
    preview: Optional[str] = None
    error: Optional[str] = None

class CSVUploadResponse(BaseModel):
    ok: bool
    columns: Optional[List[str]] = None
    types: Optional[Dict[str, str]] = None
    stats: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None

class CSVURLRequest(BaseModel):
    session_id: str
    url: HttpUrl

class CSVMissingResponse(BaseModel):
    ok: bool
    column: Optional[str] = None
    missing_count: Optional[int] = None
    error: Optional[str] = None

class CSVHistResponse(BaseModel):
    ok: bool
    image_base64: Optional[str] = None
    error: Optional[str] = None

class NewChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class NewChatResponse(BaseModel):
    ok: bool
    blocks: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

# Session metadata persistence functions
def get_session_meta_path():
    """Get path to session metadata file"""
    return "storage/session_meta.json"

def load_session_meta():
    """Load session metadata from JSON file"""
    meta_path = get_session_meta_path()
    if not os.path.exists(meta_path):
        return {}
    
    try:
        with open(meta_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading session metadata: {e}")
        return {}

def save_session_meta(meta_data):
    """Save session metadata to JSON file"""
    meta_path = get_session_meta_path()
    try:
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        
        with open(meta_path, 'w') as f:
            json.dump(meta_data, f, indent=2)
    except Exception as e:
        print(f"Error saving session metadata: {e}")

def set_csv_meta(session_id: str, meta: Dict[str, Any]):
    """Set CSV metadata for a session"""
    meta_data = load_session_meta()
    meta_data[session_id] = meta
    save_session_meta(meta_data)

def get_csv_meta(session_id: str) -> Optional[Dict[str, Any]]:
    """Get CSV metadata for a session"""
    meta_data = load_session_meta()
    return meta_data.get(session_id)

def save_attachment_to_firestore(session_id: str, attachment_data: Dict[str, Any]):
    """Save attachment metadata to Firestore"""
    if not db:
        print("Firestore not initialized, skipping attachment save")
        return
    
    try:
        attachment_data['created_at'] = firestore.SERVER_TIMESTAMP
        db.collection('attachments').document(session_id).set(attachment_data)
        print(f"Attachment saved to Firestore for session {session_id}")
    except Exception as e:
        print(f"Error saving attachment to Firestore: {e}")

# Firebase Firestore functions
def save_message_to_firestore(chat_id: str, role: str, parts: List[Dict[str, Any]]) -> str:
    """Save a message to Firestore and return the message ID"""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore not initialized")
    
    try:
        message_data = {
            'role': role,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'parts': parts
        }
        
        # Add message to subcollection
        doc_ref = db.collection('chats').document(chat_id).collection('messages').add(message_data)
        return doc_ref[1].id  # Return the document ID
        
    except Exception as e:
        print(f"Error saving message to Firestore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

def get_messages_from_firestore(chat_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent messages from Firestore"""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore not initialized")
    
    try:
        messages_ref = db.collection('chats').document(chat_id).collection('messages')
        messages = messages_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        message_list = []
        for message in messages:
            message_data = message.to_dict()
            message_data['id'] = message.id
            message_list.append(message_data)
        
        # Return in chronological order (oldest first)
        return list(reversed(message_list))
        
    except Exception as e:
        print(f"Error getting messages from Firestore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

def get_message_from_firestore(chat_id: str, message_id: str) -> Dict[str, Any]:
    """Get a specific message from Firestore"""
    if not db:
        raise HTTPException(status_code=500, detail="Firestore not initialized")
    
    try:
        doc_ref = db.collection('chats').document(chat_id).collection('messages').document(message_id)
        message_doc = doc_ref.get()
        
        if not message_doc.exists:
            raise HTTPException(status_code=404, detail="Message not found")
        
        message_data = message_doc.to_dict()
        message_data['id'] = message_doc.id
        return message_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting message from Firestore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get message: {str(e)}")

def download_file_from_storage(file_url: str) -> bytes:
    """Download file from Firebase Storage or external URL"""
    try:
        if file_url.startswith('gs://'):
            # Firebase Storage gs:// URL
            bucket_name = file_url.split('/')[2]
            file_path = '/'.join(file_url.split('/')[3:])
            
            bucket = storage.bucket(bucket_name)
            blob = bucket.blob(file_path)
            return blob.download_as_bytes()
        elif 'firebasestorage.googleapis.com' in file_url:
            # Firebase Storage download URL (https://...)
            response = requests.get(file_url)
            response.raise_for_status()
            return response.content
        else:
            # External URL
            response = requests.get(file_url)
            response.raise_for_status()
            return response.content
            
    except Exception as e:
        print(f"Error downloading file from {file_url}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

# API Endpoints
@app.get("/")
async def root():
    return {"message": "AI Fullstack Assignment API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"ok": True}

@app.get("/config")
async def get_config():
    """Get configuration information"""
    return {
        "max_csv_size_mb": MAX_CSV_SIZE_MB,
        "max_image_size_mb": MAX_IMAGE_SIZE_MB,
        "api_key_configured": is_api_key_configured(),
        "allowed_image_types": ["png", "jpg", "jpeg"]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        chat_id = request.chat_id
        message_id = request.message_id
        
        print(f"DEBUG: Chat endpoint called - chat_id={chat_id}, message_id={message_id}")
        
        # Get the user message from Firestore
        try:
            user_message = get_message_from_firestore(chat_id, message_id)
        except HTTPException as e:
            if e.status_code == 404:
                # For testing purposes, create a mock message
                print(f"DEBUG: Message not found, creating mock message for testing")
                user_message = {
                    'role': 'user',
                    'parts': [{'type': 'text', 'content': 'Summarize the dataset'}]
                }
            else:
                raise
        
        # Get conversation history (last 10 messages)
        messages = get_messages_from_firestore(chat_id, limit=10)
        
        # Build conversation context
        conversation = []
        
        # Add system prompt
        system_prompt = {
            "role": "system",
            "content": "You are a concise helpful assistant. Use short paragraphs, bullets when useful. Respect markdown. Include timestamps only if asked. For image chats always reference the uploaded image explicitly."
        }
        conversation.append(system_prompt)
        
        # Process messages and handle file attachments
        image_data = None
        
        for message in messages:
            message_parts = message.get('parts', [])
            role = message.get('role', 'user')
            
            # Process each part of the message
            for part in message_parts:
                part_type = part.get('type', 'text')
                content = part.get('content', '')
                
                if part_type == 'text':
                    conversation.append({
                        "role": role,
                        "content": content
                    })
                elif part_type == 'image':
                    # Download image from storage
                    try:
                        image_response = requests.get(content)
                        image_data = base64.b64encode(image_response.content).decode('utf-8')
                    except Exception as e:
                        print(f"Failed to download image: {e}")
                # NOTE: CSV files are handled via session metadata, not message attachments
        
        # Add CSV context using session metadata as ground truth
        print(f"DEBUG: Checking CSV metadata for session_id={chat_id}")
        csv_meta = get_csv_meta(chat_id)
        print(f"DEBUG: get_csv_meta({chat_id}) returned: {csv_meta}")
        
        if csv_meta:
            print(f"INFO: CSV context injected from session metadata - session_id={chat_id}, rows={csv_meta['rows']}, columns={len(csv_meta['columns'])}")
            
            # Create CSV context system prompt
            columns_str = ", ".join(csv_meta["columns"][:20])  # Limit to 20 columns
            dtypes_str = ", ".join([f"{k}:{v}" for k, v in list(csv_meta["dtypes"].items())[:20]])  # Limit to 20 dtypes
            
            csv_context_prompt = f"""CSV context:
                                    - rows: {csv_meta["rows"]}
                                    - columns: {columns_str}
                                    - dtypes: {dtypes_str}
                                    When asked for plots, respond with textual summaries only."""
            
            # Insert this prompt at the beginning of conversation
            conversation.insert(1, {
                "role": "system",
                "content": csv_context_prompt
            })
            print(f"DEBUG: CSV context prompt added to conversation")
        else:
            # Fallback: Check Firestore for CSV attachment if no session metadata
            print(f"INFO: No CSV metadata found for session {chat_id}, checking Firestore...")
            try:
                if db:
                    attachment_doc = db.collection('attachments').document(chat_id).get()
                    print(f"DEBUG: Firestore attachment query for {chat_id}: exists={attachment_doc.exists}")
                    if attachment_doc.exists:
                        attachment_data = attachment_doc.to_dict()
                        print(f"DEBUG: Firestore attachment data: {attachment_data}")
                        if attachment_data.get('type') == 'csv':
                            print(f"INFO: Found CSV attachment in Firestore for session {chat_id}, hydrating session metadata")
                            
                            # Hydrate session metadata from Firestore
                            csv_meta = {
                                "csv_path": attachment_data.get('storage_path', ''),
                                "columns": attachment_data.get('columns', []),
                                "dtypes": attachment_data.get('dtypes', {}),
                                "rows": attachment_data.get('rows', 0)
                            }
                            
                            # Save to session metadata for future use
                            set_csv_meta(chat_id, csv_meta)
                            
                            # Create CSV context system prompt
                            columns_str = ", ".join(csv_meta["columns"][:20])
                            dtypes_str = ", ".join([f"{k}:{v}" for k, v in list(csv_meta["dtypes"].items())[:20]])
                            
                            csv_context_prompt = f"""CSV context:
                                    - rows: {csv_meta["rows"]}
                                    - columns: {columns_str}
                                    - dtypes: {dtypes_str}
                                    When asked for plots, respond with textual summaries only."""
                            
                            # Insert this prompt at the beginning of conversation
                            conversation.insert(1, {
                                "role": "system",
                                "content": csv_context_prompt
                            })
                            
                            print(f"INFO: CSV context injected from Firestore - session_id={chat_id}, rows={csv_meta['rows']}, columns={len(csv_meta['columns'])}")
                        else:
                            print(f"INFO: No CSV attachment found in Firestore for session {chat_id}")
                    else:
                        print(f"INFO: No attachment document found in Firestore for session {chat_id}")
            except Exception as e:
                print(f"ERROR: Error checking Firestore for CSV attachment - session_id={chat_id}, error={e}")
        
        # Call LLM service
        if len(conversation) > 1:  # More than just system prompt
            try:
                if image_data:
                    # Use vision model for image + text
                    ai_response = vision(conversation, image_data)
                else:
                    # Use regular chat model
                    ai_response = chat(conversation)
                
                # Save bot response to Firestore
                bot_parts = [{"type": "text", "content": ai_response}]
                save_message_to_firestore(chat_id, "assistant", bot_parts)
                
                return ChatResponse(status="success")
                
            except Exception as e:
                print(f"LLM error: {e}")
                error_message = f"Sorry, I encountered an error: {str(e)}"
                bot_parts = [{"type": "text", "content": error_message}]
                save_message_to_firestore(chat_id, "assistant", bot_parts)
                
                return ChatResponse(status="success")
        else:
            # No conversation context, return empty response
            return ChatResponse(status="success")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return ChatResponse(status="error", error=str(e))

@app.post("/image-chat", response_model=ImageChatResponse)
async def image_chat_endpoint(
    session_id: str = Form(...),
    image_file: UploadFile = File(...),
    question: str = Form("")
):
    try:
        print(f"INFO: Image upload started - session_id={session_id}, filename={image_file.filename}")
        
        # Validate file type (PNG/JPG only)
        if not image_file.filename:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "No file provided"}
            )
        
        # Check content type and file extension
        content_type = image_file.content_type or ""
        file_extension = image_file.filename.lower().split('.')[-1]
        allowed_extensions = ['png', 'jpg', 'jpeg']
        
        if not (content_type.startswith('image/') and file_extension in allowed_extensions):
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Only PNG and JPG images are allowed"}
            )
        
        # Check file size
        content = await image_file.read()
        if len(content) > MAX_IMAGE_SIZE_BYTES:
            return JSONResponse(
                status_code=413,
                content={"ok": False, "error": "File too large"}
            )
        
        # Call vision service
        assistant_message = vision(content, question)
        
        # Create preview (base64 encoded image)
        preview = f"data:image/{file_extension};base64,{base64.b64encode(content).decode('utf-8')}"
        
        # Save to Firestore
        attachment_data = {
            "type": "image",
            "filename": image_file.filename,
            "bytes_size": len(content)
        }
        save_attachment_to_firestore(session_id, attachment_data)
        
        print(f"INFO: Image upload finished - session_id={session_id}, filename={image_file.filename}, size={len(content)} bytes")
        
        return ImageChatResponse(
            ok=True, 
            assistant_message=assistant_message,
            text=assistant_message,
            preview=preview
        )
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: Image upload failed - session_id={session_id}, error={error_msg}")
        
        # Provide more user-friendly error messages
        if "decode" in error_msg.lower() or "format" in error_msg.lower():
            error_msg = "Unable to process the image. Please ensure it's a valid PNG or JPG file."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            error_msg = "Network error occurred while processing the image. Please check your connection and try again."
        elif "timeout" in error_msg.lower():
            error_msg = "Request timed out. The image might be too large or the server is busy. Please try again."
        
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": error_msg}
        )

@app.post("/chat/v2", response_model=NewChatResponse)
async def chat_v2_endpoint(request: NewChatRequest):
    """New chat endpoint using the orchestrator-based architecture"""
    try:
        session_id = request.session_id
        user_text = request.message
        
        print(f"INFO: Chat v2 - session_id={session_id}, message={user_text[:50]}...")
        
        # Run orchestrator
        result = run_orchestrator(session_id, user_text, llm_enabled=is_api_key_configured())
        
        # Convert block to dict for JSON response
        blocks = [result.model_dump(exclude_none=True)]
        
        return NewChatResponse(ok=True, blocks=blocks)
        
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: Chat v2 failed - session_id={session_id}, error={error_msg}")
        return NewChatResponse(ok=False, error=error_msg)

@app.post("/csv/upload", response_model=CSVUploadResponse)
async def csv_upload_endpoint(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        print(f"INFO: CSV upload started - session_id={session_id}, filename={file.filename}")
        
        # Validate file type
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "No file provided"}
            )
        
        # Check content type and file extension
        content_type = file.content_type or ""
        file_extension = file.filename.lower().split('.')[-1]
        
        if not (content_type == "text/csv" or file_extension == "csv"):
            return JSONResponse(
                status_code=400,
                content={"ok": False, "error": "Only CSV files are allowed"}
            )
        
        # Check file size
        content = await file.read()
        if len(content) > MAX_CSV_SIZE_BYTES:
            return JSONResponse(
                status_code=413,
                content={"ok": False, "error": "File too large"}
            )
        
        # Reset file pointer for CSV tools
        file.file.seek(0)
        
        # Use CSV tools service
        file_path, df_info = load_csv_from_upload(file, session_id)
        
        # Load DataFrame for stats
        df = load_csv_from_path(file_path)
        stats = basic_stats(df)
        
        # Store in registry
        registry.put(
            session_id,
            df,
            file_path,
            df_info["column_names"],
            df_info["dtypes"]
        )
        
        # Create metadata
        meta = {
            "csv_path": file_path,
            "columns": df_info["column_names"],
            "dtypes": df_info["dtypes"],
            "rows": df_info["rows"]
        }
        
        # Save metadata
        set_csv_meta(session_id, meta)
        
        # Save to Firestore
        attachment_data = {
            "type": "csv",
            
            "storage_path": file_path,
            "rows": df_info["rows"],
            "columns": df_info["column_names"],
            "dtypes": df_info["dtypes"]
        }
        save_attachment_to_firestore(session_id, attachment_data)
        
        print(f"INFO: CSV upload finished - session_id={session_id}, saved_path={file_path}, rows={df_info['rows']}, columns={df_info['columns']}")
        
        return CSVUploadResponse(
            ok=True,
            columns=df_info["column_names"],
            types=df_info["dtypes"],
            stats={
                "rows": df_info["rows"],
                "original_rows": df_info["original_rows"],
                "columns": df_info["columns"],
                "sampled": df_info["sampled"],
                "memory_usage": df_info["memory_usage"],
                "detailed_stats": stats
            },
            suggestions=[
                "Summarize the dataset",
                "Show basic stats for numeric columns",
                "Which column has the most missing values?",
                "Plot a histogram of price"
            ]
        )
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: CSV upload failed - session_id={session_id}, error={error_msg}")
        
        # Provide more user-friendly error messages
        if "decode" in error_msg.lower() or "encoding" in error_msg.lower():
            error_msg = "Unable to parse CSV file. Please ensure the file is properly formatted and saved as UTF-8."
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            error_msg = "Network error occurred while processing the file. Please check your connection and try again."
        elif "timeout" in error_msg.lower():
            error_msg = "Request timed out. The file might be too large or the server is busy. Please try again."
        
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": error_msg}
        )

@app.post("/csv/url", response_model=CSVUploadResponse)
async def csv_url_endpoint(request: CSVURLRequest):
    try:
        print(f"INFO: CSV URL upload started - session_id={request.session_id}, url={request.url}")
        
        # Use CSV tools service with provided session_id
        file_path, df_info = load_csv_from_url(str(request.url), request.session_id)
        
        # Load DataFrame for stats
        df = load_csv_from_path(file_path)
        stats = basic_stats(df)
        
        # Store in registry
        registry.put(
            request.session_id,
            df,
            file_path,
            df_info["column_names"],
            df_info["dtypes"]
        )
        
        # Create metadata
        meta = {
            "csv_path": file_path,
            "columns": df_info["column_names"],
            "dtypes": df_info["dtypes"],
            "rows": df_info["rows"]
        }
        
        # Save metadata
        set_csv_meta(request.session_id, meta)
        
        # Save to Firestore
        attachment_data = {
            "type": "csv",
            "storage_path": file_path,
            "rows": df_info["rows"],
            "columns": df_info["column_names"],
            "dtypes": df_info["dtypes"]
        }
        save_attachment_to_firestore(request.session_id, attachment_data)
        
        print(f"INFO: CSV URL upload finished - session_id={request.session_id}, saved_path={file_path}, rows={df_info['rows']}, columns={df_info['columns']}")
        
        return CSVUploadResponse(
            ok=True,
            columns=df_info["column_names"],
            types=df_info["dtypes"],
            stats={
                "rows": df_info["rows"],
                "original_rows": df_info["original_rows"],
                "columns": df_info["columns"],
                "sampled": df_info["sampled"],
                "memory_usage": df_info["memory_usage"],
                "detailed_stats": stats
            },
            suggestions=[
                "Summarize the dataset",
                "Show basic stats for numeric columns",
                "Which column has the most missing values?",
                "Plot a histogram of price"
            ]
        )
    
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: CSV URL upload failed - session_id={request.session_id}, error={error_msg}")
        
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": error_msg}
        )

@app.get("/debug/session/{session_id}")
async def debug_session_endpoint(session_id: str):
    """Debug endpoint to check session metadata"""
    try:
        meta = get_csv_meta(session_id)
        return {"meta": meta}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )

@app.get("/debug/context/{session_id}")
async def debug_context_endpoint(session_id: str):
    """Debug endpoint to check CSV context for a session"""
    try:
        # Get local CSV metadata
        csv_meta = get_csv_meta(session_id)
        
        # Get Firestore attachment info
        firestore_attachment = None
        if db:
            try:
                attachment_doc = db.collection('attachments').document(session_id).get()
                if attachment_doc.exists:
                    firestore_attachment = attachment_doc.to_dict()
            except Exception as e:
                print(f"Error getting Firestore attachment: {e}")
        
        return {
            "session_id": session_id,
            "local_csv_meta": csv_meta,
            "firestore_attachment": firestore_attachment,
            "session_meta_file_exists": os.path.exists(get_session_meta_path())
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )

@app.get("/csv/missing", response_model=CSVMissingResponse)
async def csv_missing_endpoint(session_id: str = Query(...)):
    try:
        # Find CSV file for session
        csv_path = f"storage/{session_id}_data.csv"
        if not os.path.exists(csv_path):
            return CSVMissingResponse(ok=False, error="No CSV data found for this session")
        
        # Load DataFrame
        df = load_csv_from_path(csv_path)
        
        # Find column with most missing values
        column, count = most_missing(df)
        
        return CSVMissingResponse(
            ok=True,
            column=column,
            missing_count=count
        )
    
    except Exception as e:
        return CSVMissingResponse(ok=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)