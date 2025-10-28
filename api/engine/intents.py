"""Intent Detection - Recognize user intent from text"""
import re
from typing import Optional, Dict, Any


def detect_intent(user_text: str) -> Optional[Dict[str, Any]]:
    """
    Detect user intent from text using heuristics (regex/keywords)
    
    Returns:
        Optional[Intent]: Detected intent with args, or None if no match
    """
    text = user_text.lower().strip()
    
    # Summarize intent
    if re.search(r'\b(summarize|t[oó]m t[aắ]t|summary)\b', text, re.IGNORECASE):
        return {"name": "summarize", "args": {}}
    
    # Stats intent
    if re.search(r'\b(stats|th[oố]ng k[eê]|statistics|describe)\b', text, re.IGNORECASE):
        return {"name": "stats", "args": {}}
    
    # Missing values intent
    if re.search(r'\b(missing|null|nan|thi[eế]u|gi[aá] tr[ịi] thi[eế]u)\b', text, re.IGNORECASE):
        return {"name": "missing", "args": {}}
    
    # Schema intent
    if re.search(r'\b(schema|columns|dtypes|d[aạ]ng li[eệ]u|c[oộ]t|c[oộ]t n[aà]o)\b', text, re.IGNORECASE):
        return {"name": "schema", "args": {}}
    
    # Sample/Preview intent with optional count
    sample_match = re.search(r'\b(sample|preview|xem|m[aẫ]u)\b', text, re.IGNORECASE)
    if sample_match:
        # Extract number if present
        number_match = re.search(r'\b(\d+)\b', text)
        n = int(number_match.group(1)) if number_match else 10
        n = max(1, min(50, n))  # Clamp between 1 and 50
        return {"name": "sample", "args": {"n": n}}
    
    # Chart intents - detect various chart types
    chart_intent = _detect_chart_intent(text)
    if chart_intent:
        return chart_intent
    
    return None


def _detect_chart_intent(text: str) -> Optional[Dict[str, Any]]:
    """Detect chart creation intent and return ChartSpec-like dict"""
    import re
    
    text_lower = text.lower()
    
    # Histogram
    if re.search(r'\bhist(?:ogram)?\s+of\s+([a-zA-Z0-9_\s]+)', text_lower):
        match = re.search(r'\bhist(?:ogram)?\s+of\s+([a-zA-Z0-9_\s]+)', text_lower)
        column = match.group(1).strip() if match else None
        bins_match = re.search(r'bins?\s*=\s*(\d+)', text_lower)
        bins = int(bins_match.group(1)) if bins_match else 30
        
        if column:
            return {
                "name": "chart",
                "args": {
                    "spec": {
                        "mark": "histogram",
                        "x": {"name": column, "type": "quantitative"},
                        "bins": bins
                    }
                }
            }
    
    # Bar chart
    if re.search(r'\bbar\s+chart\s+of\s+([a-zA-Z0-9_\s]+)', text_lower):
        match = re.search(r'\bbar\s+chart\s+of\s+([a-zA-Z0-9_\s]+)', text_lower)
        column = match.group(1).strip() if match else None
        top_match = re.search(r'top\s*=\s*(\d+)', text_lower)
        top = int(top_match.group(1)) if top_match else None
        
        if column:
            return {
                "name": "chart",
                "args": {
                    "spec": {
                        "mark": "bar",
                        "x": {"name": column, "type": "categorical", "topk": top}
                    }
                }
            }
    
    # Line chart
    if re.search(r'\bline\s+chart\s+of\s+([a-zA-Z0-9_\s]+)\s+by\s+([a-zA-Z0-9_\s]+)', text_lower):
        match = re.search(r'\bline\s+chart\s+of\s+([a-zA-Z0-9_\s]+)\s+by\s+([a-zA-Z0-9_\s]+)', text_lower)
        if match:
            y_col = match.group(1).strip()
            x_col = match.group(2).strip()
            
            # Detect time unit
            time_unit = None
            if re.search(r'\bmonth\b', text_lower):
                time_unit = "month"
            elif re.search(r'\bweek\b', text_lower):
                time_unit = "week"
            elif re.search(r'\bday\b', text_lower):
                time_unit = "day"
            elif re.search(r'\byear\b', text_lower):
                time_unit = "year"
            
            return {
                "name": "chart",
                "args": {
                    "spec": {
                        "mark": "line",
                        "x": {"name": x_col, "type": "temporal", "time_unit": time_unit},
                        "y": {"name": y_col, "type": "quantitative"}
                    }
                }
            }
    
    # Scatter plot
    if re.search(r'\bscatter\s+([a-zA-Z0-9_\s]+)\s+vs\s+([a-zA-Z0-9_\s]+)', text_lower):
        match = re.search(r'\bscatter\s+([a-zA-Z0-9_\s]+)\s+vs\s+([a-zA-Z0-9_\s]+)', text_lower)
        if match:
            x_col = match.group(1).strip()
            y_col = match.group(2).strip()
            
            return {
                "name": "chart",
                "args": {
                    "spec": {
                        "mark": "scatter",
                        "x": {"name": x_col, "type": "quantitative"},
                        "y": {"name": y_col, "type": "quantitative"}
                    }
                }
            }
    
    # Box plot
    if re.search(r'\bbox\s+plot\s+of\s+([a-zA-Z0-9_\s]+)\s+by\s+([a-zA-Z0-9_\s]+)', text_lower):
        match = re.search(r'\bbox\s+plot\s+of\s+([a-zA-Z0-9_\s]+)\s+by\s+([a-zA-Z0-9_\s]+)', text_lower)
        if match:
            value_col = match.group(1).strip()
            category_col = match.group(2).strip()
            
            return {
                "name": "chart",
                "args": {
                    "spec": {
                        "mark": "box",
                        "x": {"name": category_col, "type": "categorical"},
                        "y": {"name": value_col, "type": "quantitative"}
                    }
                }
            }
    
    return None

