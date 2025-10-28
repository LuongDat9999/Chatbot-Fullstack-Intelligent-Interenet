"""Block Response Protocol - Standardized response schema"""
from pydantic import BaseModel
from typing import Any, List, Optional, Literal, Dict
from datetime import datetime

BlockType = Literal["text", "table", "image", "alert"]


class DebugInfo(BaseModel):
    """Debug information attached to blocks"""
    session_id: Optional[str] = None
    intent: Optional[str] = None
    took_ms: Optional[int] = None
    notes: Optional[Dict[str, Any]] = None


class TextBlock(BaseModel):
    """Text response block"""
    type: Literal["text"] = "text"
    title: Optional[str] = None
    payload: str
    debug: Optional[DebugInfo] = None


class TableBlock(BaseModel):
    """Table response block"""
    type: Literal["table"] = "table"
    title: Optional[str] = None
    payload: Dict[str, Any]  # {headers: List[str], rows: List[List[Any]], note?: str, truncated?: bool}
    debug: Optional[DebugInfo] = None


class ImageBlock(BaseModel):
    """Image response block"""
    type: Literal["image"] = "image"
    title: Optional[str] = None
    payload: str  # base64 encoded image
    debug: Optional[DebugInfo] = None


class AlertBlock(BaseModel):
    """Alert/error response block"""
    type: Literal["alert"] = "alert"
    title: Optional[str] = None
    payload: str  # message
    debug: Optional[DebugInfo] = None


Block = TextBlock | TableBlock | ImageBlock | AlertBlock

