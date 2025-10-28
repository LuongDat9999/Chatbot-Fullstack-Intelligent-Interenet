"""Orchestrator - Decision logic for routing between data actions and LLM"""
import time
from typing import Optional, Dict, Any
from .blocks import Block, TextBlock, AlertBlock, DebugInfo
from .intents import detect_intent
from .chartspec import ChartSpec
from data.csv_registry import registry
from data import csv_actions
from data.csv_charts import build_chart
from services.llm import chat


def call_llm_with_blocks(session_id: Optional[str], user_text: str) -> Block:
    """
    Call LLM service and wrap response in a TextBlock
    
    Args:
        session_id: Session ID for context
        user_text: User's message
    
    Returns:
        Block: TextBlock or AlertBlock
    """
    try:
        # Load session metadata for CSV context
        csv_context = None
        if session_id:
            # Import session metadata loading from app.py
            import os
            import json
            
            session_meta_path = "storage/session_meta.json"
            if os.path.exists(session_meta_path):
                try:
                    with open(session_meta_path, 'r') as f:
                        meta_data = json.load(f)
                        csv_meta = meta_data.get(session_id)
                except Exception:
                    csv_meta = None
            else:
                csv_meta = None
            
            if csv_meta:
                columns_str = ", ".join(csv_meta["columns"][:20])
                dtypes_str = ", ".join([f"{k}:{v}" for k, v in list(csv_meta["dtypes"].items())[:20]])
                csv_context = f"""CSV context:
                                - rows: {csv_meta["rows"]}
                                - columns: {columns_str}
                                - dtypes: {dtypes_str}
                                When asked for plots, respond with textual summaries only."""
        
        # Build conversation
        conversation = [
            {
                "role": "system",
                "content": "You are a concise helpful assistant. Use short paragraphs, bullets when useful. Respect markdown. Include timestamps only if asked. For image chats always reference the uploaded image explicitly."
            }
        ]
        
        if csv_context:
            conversation.append({
                "role": "system",
                "content": csv_context
            })
        
        conversation.append({
            "role": "user",
            "content": user_text
        })
        
        # Call LLM
        response = chat(conversation)
        
        return TextBlock(
            payload=response,
            title=None
        )
    except Exception as e:
        return AlertBlock(
            payload=f"Error calling LLM: {str(e)}",
            title="Error"
        )


def run_orchestrator(session_id: Optional[str], user_text: str, llm_enabled: bool = True) -> Block:
    """
    Main orchestrator - decide whether to use data actions or LLM
    
    Args:
        session_id: Session ID
        user_text: User message
        llm_enabled: Whether to enable LLM fallback
    
    Returns:
        Block: Response block (TextBlock, TableBlock, ImageBlock, or AlertBlock)
    """
    start_time = time.time()
    
    # Detect intent
    intent = detect_intent(user_text)
    
    # Check if session has CSV
    has_csv = bool(session_id and registry.has(session_id))
    
    # Try data actions first if CSV exists and intent detected
    if has_csv and intent:
        intent_name = intent.get("name")
        intent_args = intent.get("args") or {}
        
        try:
            if intent_name == "summarize":
                block = csv_actions.action_summarize(session_id)
            elif intent_name == "schema":
                block = csv_actions.action_schema(session_id)
            elif intent_name == "sample":
                block = csv_actions.action_sample(session_id, n=intent_args.get("n", 10))
            elif intent_name == "stats":
                block = csv_actions.action_stats(session_id)
            elif intent_name == "missing":
                block = csv_actions.action_missing(session_id)
            elif intent_name == "histogram":
                column = intent_args.get("column")
                if column:
                    block = csv_actions.action_histogram(session_id, column=column, bins=int(intent_args.get("bins", 30)))
                else:
                    # Column not specified
                    block = AlertBlock(payload="Please specify a column for histogram. For example: 'histogram of price'")
            elif intent_name == "chart":
                # Handle chart requests
                spec_dict = intent_args.get("spec")
                if spec_dict:
                    try:
                        spec = ChartSpec(**spec_dict)
                        block, table_payload = build_chart(session_id, spec)
                        
                        # If we have table data, we could attach it to debug notes
                        if table_payload and block.debug:
                            existing_notes = block.debug.notes or {}
                            block.debug.notes = {
                                **existing_notes,
                                "table_preview": table_payload
                            }
                    except Exception as e:
                        block = AlertBlock(
                            payload=f"Error parsing chart spec: {str(e)}",
                            title="Invalid Chart Spec"
                        )
                else:
                    block = AlertBlock(
                        payload="No chart specification provided",
                        title="Missing Chart Spec"
                    )
            else:
                # Unknown intent with CSV
                if llm_enabled:
                    block = call_llm_with_blocks(session_id, user_text)
                else:
                    block = AlertBlock(payload="Unrecognized request. Please try: summarize, stats, missing, histogram, schema, or sample")
            
            # Add debug info
            took_ms = int((time.time() - start_time) * 1000)
            if block.debug is None:
                block.debug = DebugInfo(
                    session_id=session_id,
                    intent=intent_name if intent else None,
                    took_ms=took_ms
                )
            else:
                block.debug.intent = intent_name if intent else None
                block.debug.took_ms = took_ms
            
            return block
            
        except Exception as e:
            # Action failed, fall back to LLM if enabled
            if llm_enabled:
                return call_llm_with_blocks(session_id, user_text)
            else:
                return AlertBlock(
                    payload=f"Error processing request: {str(e)}",
                    title="Error"
                )
    
    # No CSV or no intent detected
    if not has_csv:
        if llm_enabled:
            return call_llm_with_blocks(session_id, user_text)
        else:
            return AlertBlock(
                payload="No CSV data loaded. Please upload a CSV file first.",
                title="No Data"
            )
    
    # Has CSV but no intent matched
    if llm_enabled:
        return call_llm_with_blocks(session_id, user_text)
    else:
        return AlertBlock(
            payload="Unrecognized request. Try: summarize, stats, missing, histogram, schema, or sample",
            title="Unrecognized"
        )