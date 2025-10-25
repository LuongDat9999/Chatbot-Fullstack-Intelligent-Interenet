import os
from typing import List, Dict
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_openai_client():
    """Get OpenAI client with proper configuration"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openrouter-api-key-here":
        return None
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def chat(messages: List[Dict[str, str]]) -> str:
    """
    Send messages to OpenAI Chat Completion API
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        str: Assistant's response or mock response if no API key
    """
    client = get_openai_client()
    
    if not client:
        # Mock response for local development
        return "🤖 [Mock Response] I'm a helpful AI assistant! This is a mock response because no API key is configured. Please set your OPENAI_API_KEY in the .env file to use real AI responses."
    
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "AI Fullstack Assignment",
            },
            model="openai/gpt-oss-20b:free",
            messages=messages
        )
        
        return completion.choices[0].message.content
    
    except Exception as e:
        return f"❌ Error calling AI service: {str(e)}"

def vision(image_bytes: bytes, question: str) -> str:
    """
    Send image and question to OpenAI Vision API
    
    Args:
        image_bytes: Raw image bytes
        question: Question about the image
        
    Returns:
        str: Assistant's response about the image or mock response if no API key
    """
    client = get_openai_client()
    
    if not client:
        # Mock response for local development
        return f"🖼️ [Mock Vision Response] In the uploaded image, I see various visual elements. This is a mock response because no API key is configured. Please set your OPENAI_API_KEY in the .env file to analyze real images. Question asked: {question}"
    
    try:
        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:5173",
                "X-Title": "AI Fullstack Assignment",
            },
            model="openai/gpt-4o",  # Vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"In the uploaded image, I see... {question}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
        )
        
        return completion.choices[0].message.content
    
    except Exception as e:
        return f"❌ Error calling vision service: {str(e)}"

def is_api_key_configured() -> bool:
    """
    Check if API key is properly configured
    
    Returns:
        bool: True if API key is configured, False otherwise
    """
    api_key = os.getenv("OPENAI_API_KEY")
    return bool(api_key and api_key != "your-openrouter-api-key-here")
