"""CSV Chart Actions - Render charts from ChartSpec"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io
import time
from typing import Dict, Any, Optional, List, Tuple
from engine.blocks import ImageBlock, AlertBlock, DebugInfo
from engine.chartspec import ChartSpec, FieldSpec, FilterSpec
from engine.errors import CsvNotLoaded, ColumnNotFound
from .csv_registry import load_csv_for_session
from utils.cache import get_cache_key, cache_get, cache_set


def infer_field_type(df: pd.DataFrame, col: str) -> str:
    """
    Infer field type from DataFrame column
    
    Returns:
        "quantitative" | "categorical" | "temporal"
    """
    if col not in df.columns:
        raise ColumnNotFound(col)
    
    dtype = df[col].dtype
    
    # Check if datetime
    if pd.api.types.is_datetime64_any_dtype(dtype) or pd.api.types.is_datetime64tz_dtype(dtype):
        return "temporal"
    
    # Check if numeric
    if pd.api.types.is_numeric_dtype(dtype):
        return "quantitative"
    
    # Otherwise categorical
    return "categorical"


def apply_filters(df: pd.DataFrame, filters: Optional[List[FilterSpec]]) -> pd.DataFrame:
    """Apply filters to DataFrame"""
    if not filters:
        return df
    
    result = df.copy()
    for f in filters:
        col = f.column
        op = f.op
        val = f.value
        
        if col not in result.columns:
            continue
        
        if op == "==":
            result = result[result[col] == val]
        elif op == "!=":
            result = result[result[col] != val]
        elif op == "in":
            result = result[result[col].isin(val)]
        elif op == "notin":
            result = result[~result[col].isin(val)]
        elif op == ">":
            result = result[result[col] > val]
        elif op == ">=":
            result = result[result[col] >= val]
        elif op == "<":
            result = result[result[col] < val]
        elif op == "<=":
            result = result[result[col] <= val]
    
    return result


def plot_histogram(df: pd.DataFrame, col: str, bins: int = 30) -> str:
    """Plot histogram and return base64 PNG"""
    plt.figure(figsize=(10, 6))
    plt.hist(df[col].dropna(), bins=bins, alpha=0.7, color='#81E1FF', edgecolor='#264F68')
    plt.title(f'Histogram of {col}')
    plt.xlabel(col)
    plt.ylabel('Frequency')
    plt.xticks(color='#BAE9F4')
    plt.yticks(color='#BAE9F4')
    plt.gca().set_facecolor('#0F1720')
    plt.gcf().set_facecolor('#0B1114')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', facecolor='#0B1114', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return image_base64


def plot_bar(df: pd.DataFrame, col: str, agg: str = "count", topk: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
    """Plot bar chart and return base64 PNG + table data"""
    # Group and aggregate
    if agg == "count":
        counts = df[col].value_counts()
    elif agg == "sum":
        counts = df.groupby(col).size()  # Sum of counts
    else:
        # For other aggs, we'd need a y column
        counts = df[col].value_counts()
    
    if topk:
        counts = counts.head(topk)
    
    # Create table payload
    table_data = {
        "headers": [col, "Count"],
        "rows": [[str(k), str(v)] for k, v in counts.items()]
    }
    
    # Plot
    plt.figure(figsize=(10, 6))
    counts.plot(kind='bar', color='#81E1FF', edgecolor='#264F68')
    plt.title(f'Bar Chart of {col}')
    plt.xlabel(col)
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right', color='#BAE9F4')
    plt.yticks(color='#BAE9F4')
    plt.gca().set_facecolor('#0F1720')
    plt.gcf().set_facecolor('#0B1114')
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', facecolor='#0B1114', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return image_base64, table_data


def plot_line(df: pd.DataFrame, x_col: str, y_col: str, agg: str = "mean", time_unit: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Plot line chart and return base64 PNG + table data"""
    # Parse temporal grouping
    if time_unit:
        df[x_col] = pd.to_datetime(df[x_col])
        
        if time_unit == "month":
            df['_group'] = df[x_col].dt.to_period('M')
        elif time_unit == "week":
            df['_group'] = df[x_col].dt.to_period('W')
        elif time_unit == "day":
            df['_group'] = df[x_col].dt.to_period('D')
        elif time_unit == "year":
            df['_group'] = df[x_col].dt.to_period('Y')
        else:
            df['_group'] = df[x_col]
    else:
        df['_group'] = df[x_col]
    
    # Aggregate
    if agg == "mean":
        grouped = df.groupby('_group')[y_col].mean()
    elif agg == "sum":
        grouped = df.groupby('_group')[y_col].sum()
    elif agg == "count":
        grouped = df.groupby('_group')[y_col].count()
    elif agg == "min":
        grouped = df.groupby('_group')[y_col].min()
    elif agg == "max":
        grouped = df.groupby('_group')[y_col].max()
    elif agg == "median":
        grouped = df.groupby('_group')[y_col].median()
    else:
        grouped = df.groupby('_group')[y_col].mean()
    
    # Create table payload
    table_data = {
        "headers": ["Time", "Value"],
        "rows": [[str(k), f"{v:.4f}"] for k, v in grouped.items()]
    }
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(grouped.index.astype(str), grouped.values, marker='o', color='#81E1FF', linewidth=2)
    plt.title(f'Line Chart of {y_col} by {x_col}')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.xticks(rotation=45, ha='right', color='#BAE9F4')
    plt.yticks(color='#BAE9F4')
    plt.gca().set_facecolor('#0F1720')
    plt.gcf().set_facecolor('#0B1114')
    plt.grid(True, alpha=0.3, color='#264F68')
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', facecolor='#0B1114', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return image_base64, table_data


def plot_scatter(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[str, Dict[str, Any]]:
    """Plot scatter plot and return base64 PNG + table data"""
    # Create table payload (sample of points)
    sample = df[[x_col, y_col]].dropna().head(200)
    table_data = {
        "headers": [x_col, y_col],
        "rows": [[str(row[0]), str(row[1])] for _, row in sample.iterrows()]
    }
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.6, color='#81E1FF')
    plt.title(f'Scatter Plot: {x_col} vs {y_col}')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.xticks(color='#BAE9F4')
    plt.yticks(color='#BAE9F4')
    plt.gca().set_facecolor('#0F1720')
    plt.gcf().set_facecolor('#0B1114')
    plt.grid(True, alpha=0.3, color='#264F68')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', facecolor='#0B1114', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return image_base64, table_data


def plot_box(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[str, Dict[str, Any]]:
    """Plot box plot and return base64 PNG + table data"""
    # Group data
    grouped = df.groupby(x_col)[y_col]
    
    # Create table payload with summary stats
    stats_data = []
    for name, group in grouped:
        stats_data.append([
            str(name),
            f"{group.min():.2f}",
            f"{group.mean():.2f}",
            f"{group.median():.2f}",
            f"{group.max():.2f}"
        ])
    
    table_data = {
        "headers": [x_col, "Min", "Mean", "Median", "Max"],
        "rows": stats_data
    }
    
    # Plot
    plt.figure(figsize=(10, 6))
    df.boxplot(column=y_col, by=x_col, ax=plt.gca())
    plt.title(f'Box Plot of {y_col} by {x_col}')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.xticks(rotation=45, ha='right', color='#BAE9F4')
    plt.yticks(color='#BAE9F4')
    plt.gca().set_facecolor('#0F1720')
    plt.gcf().set_facecolor('#0B1114')
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', facecolor='#0B1114', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()
    
    return image_base64, table_data


def build_chart(session_id: str, spec: ChartSpec) -> Tuple[ImageBlock, Optional[Dict[str, Any]]]:
    """
    Build chart from ChartSpec
    
    Returns:
        Tuple of (ImageBlock or AlertBlock, optional table payload)
    """
    start_time = time.time()
    
    try:
        # Load DataFrame
        df, meta = load_csv_for_session(session_id)
        if df is None or meta is None:
            raise CsvNotLoaded(session_id)
        
        # Check cache
        cache_key = get_cache_key(session_id, spec)
        cached = cache_get(cache_key)
        if cached:
            return cached
        
        # Apply filters
        df = apply_filters(df, spec.filters)
        
        # Validate columns
        if spec.x.name not in df.columns:
            raise ColumnNotFound(spec.x.name)
        
        if spec.y and spec.y.name not in df.columns:
            raise ColumnNotFound(spec.y.name)
        
        # Infer and verify field types
        x_type = infer_field_type(df, spec.x.name)
        if x_type != spec.x.type and spec.x.type != "quantitative":  # Allow some flexibility
            pass  # Warn but continue
        
        if spec.y:
            y_type = infer_field_type(df, spec.y.name)
            if y_type != spec.y.type and spec.y.type != "quantitative":
                pass  # Warn but continue
        
        # Render chart
        image_base64 = None
        table_payload = None
        rows_used = len(df)
        
        if spec.mark == "histogram":
            bins = spec.bins or spec.x.bin or 30
            if x_type != "quantitative":
                return (AlertBlock(
                    payload=f"Column '{spec.x.name}' is not numeric. Use 'bar chart' for categorical data.",
                    title="Invalid Chart Type"
                ), None)
            image_base64 = plot_histogram(df, spec.x.name, bins)
            
            # Create table payload
            hist_data = pd.cut(df[spec.x.name].dropna(), bins=bins).value_counts().sort_index()
            table_payload = {
                "headers": ["Bin Range", "Count"],
                "rows": [[str(k), str(v)] for k, v in hist_data.items()][:200],
                "truncated": len(hist_data) > 200
            }
        
        elif spec.mark == "bar":
            if x_type == "quantitative":
                return (AlertBlock(
                    payload=f"Column '{spec.x.name}' is numeric. Use 'histogram' for quantitative data.",
                    title="Invalid Chart Type"
                ), None)
            topk = spec.x.topk
            image_base64, table_payload = plot_bar(df, spec.x.name, spec.agg or "count", topk)
        
        elif spec.mark == "line":
            if not spec.y:
                return (AlertBlock(
                    payload="Line chart requires Y axis specification.",
                    title="Invalid Chart Spec"
                ), None)
            image_base64, table_payload = plot_line(
                df, spec.x.name, spec.y.name, 
                spec.agg or "mean", spec.x.time_unit
            )
        
        elif spec.mark == "scatter":
            if not spec.y:
                return (AlertBlock(
                    payload="Scatter plot requires Y axis specification.",
                    title="Invalid Chart Spec"
                ), None)
            image_base64, table_payload = plot_scatter(df, spec.x.name, spec.y.name)
        
        elif spec.mark == "box":
            if not spec.y:
                return (AlertBlock(
                    payload="Box plot requires Y axis specification.",
                    title="Invalid Chart Spec"
                ), None)
            image_base64, table_payload = plot_box(df, spec.x.name, spec.y.name)
        
        else:
            return (AlertBlock(
                payload=f"Unknown chart type: {spec.mark}",
                title="Invalid Chart Type"
            ), None)
        
        took_ms = int((time.time() - start_time) * 1000)
        
        # Create ImageBlock
        block = ImageBlock(
            title=spec.title or f"{spec.mark.title()} Chart",
            payload=image_base64,
            debug=DebugInfo(
                intent="chart",
                took_ms=took_ms,
                notes={"rows_used": rows_used}
            )
        )
        
        # Cache result
        result = (block, table_payload)
        cache_set(cache_key, result)
        
        return result
        
    except (CsvNotLoaded, ColumnNotFound) as e:
        return (AlertBlock(payload=str(e), title="Error"), None)
    except Exception as e:
        return (AlertBlock(
            payload=f"Error rendering chart: {str(e)}",
            title="Error"
        ), None)

