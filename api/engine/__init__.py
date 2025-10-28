"""Engine module for intent-based conversation processing"""
from .blocks import Block, BlockType, TextBlock, TableBlock, ImageBlock, AlertBlock, DebugInfo
from .intents import detect_intent
from .orchestrator import run_orchestrator
from .renderers import create_text_block, create_table_block, create_image_block, create_alert_block
from .chartspec import ChartSpec, FieldSpec, FilterSpec, Mark, Agg
from .errors import (
    AppError,
    CsvNotLoaded,
    ColumnNotFound,
    InvalidCsv,
    CsvTooLarge,
    register_error_handlers
)

__all__ = [
    "Block",
    "BlockType",
    "TextBlock",
    "TableBlock",
    "ImageBlock",
    "AlertBlock",
    "DebugInfo",
    "detect_intent",
    "run_orchestrator",
    "create_text_block",
    "create_table_block",
    "create_image_block",
    "create_alert_block",
    "ChartSpec",
    "FieldSpec",
    "FilterSpec",
    "Mark",
    "Agg",
    "AppError",
    "CsvNotLoaded",
    "ColumnNotFound",
    "InvalidCsv",
    "CsvTooLarge",
    "register_error_handlers",
]

