"""Renderer helpers for creating blocks"""
from typing import Optional
from .blocks import TextBlock, TableBlock, ImageBlock, AlertBlock, DebugInfo


def create_text_block(
    payload: str,
    title: Optional[str] = None,
    debug: Optional[DebugInfo] = None
) -> TextBlock:
    """Create a text block"""
    return TextBlock(title=title, payload=payload, debug=debug)


def create_table_block(
    headers: list,
    rows: list,
    title: Optional[str] = None,
    note: Optional[str] = None,
    truncated: bool = False,
    debug: Optional[DebugInfo] = None
) -> TableBlock:
    """Create a table block with headers and rows"""
    payload = {
        "headers": headers,
        "rows": rows
    }
    if note:
        payload["note"] = note
    if truncated:
        payload["truncated"] = truncated
    
    return TableBlock(title=title, payload=payload, debug=debug)


def create_image_block(
    image_base64: str,
    title: Optional[str] = None,
    debug: Optional[DebugInfo] = None
) -> ImageBlock:
    """Create an image block"""
    return ImageBlock(title=title, payload=image_base64, debug=debug)


def create_alert_block(
    message: str,
    title: Optional[str] = None,
    debug: Optional[DebugInfo] = None
) -> AlertBlock:
    """Create an alert block"""
    return AlertBlock(title=title, payload=message, debug=debug)

