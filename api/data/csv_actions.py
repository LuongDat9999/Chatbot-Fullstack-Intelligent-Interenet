"""CSV Data Actions - Execute data operations and return blocks"""
import pandas as pd
import time
from typing import Optional
from engine.blocks import Block, TableBlock, ImageBlock
from engine.renderers import create_table_block, create_image_block, create_alert_block
from engine.errors import CsvNotLoaded, ColumnNotFound, CsvTooLarge
from .csv_registry import load_csv_for_session, registry


def _load_dataframe(session_id: str) -> tuple[pd.DataFrame, dict]:
    """Helper to load DataFrame from session"""
    df, meta = load_csv_for_session(session_id)
    
    if df is None or meta is None:
        raise CsvNotLoaded(session_id)
    
    return df, meta


def action_summarize(session_id: str) -> TableBlock:
    """Summarize dataset - rows, columns, data types"""
    start_time = time.time()
    
    df, meta = _load_dataframe(session_id)
    
    rows = [
        ["Metric", "Value"],
        ["Total Rows", str(meta.rows)],
        ["Total Columns", str(len(meta.columns))],
        ["Numeric Columns", str(sum(1 for dt in meta.dtypes.values() if 'float' in dt or 'int' in dt))],
        ["Text Columns", str(sum(1 for dt in meta.dtypes.values() if 'object' in dt or 'string' in dt))],
        ["Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"]
    ]
    
    took_ms = int((time.time() - start_time) * 1000)
    
    return create_table_block(
        headers=["Metric", "Value"],
        rows=rows,
        title="Dataset Summary",
        note="Try: 'Show stats' for numeric column details, 'Show missing values' for null analysis",
    )


def action_schema(session_id: str) -> TableBlock:
    """Get dataset schema - columns and data types"""
    start_time = time.time()
    
    df, meta = _load_dataframe(session_id)
    
    rows = []
    for col, dtype in meta.dtypes.items():
        rows.append([col, dtype])
    
    # Limit to 50 columns
    truncated = len(rows) > 50
    if truncated:
        rows = rows[:50]
    
    took_ms = int((time.time() - start_time) * 1000)
    
    return create_table_block(
        headers=["Column", "Data Type"],
        rows=rows,
        title="Dataset Schema",
        truncated=truncated,
        note=f"Showing {len(rows)} of {len(meta.columns)} columns. Try: 'Show sample' to see data preview"
    )


def action_sample(session_id: str, n: int = 10) -> TableBlock:
    """Get sample rows from dataset"""
    start_time = time.time()
    
    df, meta = _load_dataframe(session_id)
    
    n = max(1, min(50, n))  # Clamp between 1 and 50
    sample = df.head(n)
    
    rows = [list(meta.columns)] + [list(row) for _, row in sample.iterrows()]
    
    # Limit to 100 rows max
    truncated = len(sample) > 100
    if truncated:
        rows = rows[:101]  # header + 100 rows
    
    took_ms = int((time.time() - start_time) * 1000)
    
    return create_table_block(
        headers=list(meta.columns),
        rows=rows[1:],  # Skip header row (it's in headers param)
        title=f"Data Sample ({n} rows)",
        truncated=truncated,
        note=f"Showing first {min(n, 100)} rows. Try: 'Show stats' for statistics"
    )


def action_stats(session_id: str) -> TableBlock:
    """Get statistics for numeric columns (limit to 5 columns)"""
    start_time = time.time()
    
    df, meta = _load_dataframe(session_id)
    
    # Filter numeric columns
    numeric_cols = [col for col, dtype in meta.dtypes.items() 
                   if 'float' in dtype or 'int' in dtype]
    
    if not numeric_cols:
        return create_alert_block("No numeric columns found in this dataset")
    
    # Limit to 5 columns
    numeric_cols = numeric_cols[:5]
    
    rows = []
    headers = ["Statistic"] + numeric_cols
    
    for stat in ['count', 'mean', 'std', 'min', 'q25', 'median', 'q75', 'max']:
        row = [stat]
        for col in numeric_cols:
            if stat == 'count':
                row.append(str(df[col].count()))
            elif stat == 'mean':
                row.append(f"{df[col].mean():.4f}" if not df[col].isnull().all() else "N/A")
            elif stat == 'std':
                row.append(f"{df[col].std():.4f}" if not df[col].isnull().all() else "N/A")
            elif stat == 'min':
                row.append(f"{df[col].min():.4f}" if not df[col].isnull().all() else "N/A")
            elif stat == 'q25':
                row.append(f"{df[col].quantile(0.25):.4f}" if not df[col].isnull().all() else "N/A")
            elif stat == 'median':
                row.append(f"{df[col].median():.4f}" if not df[col].isnull().all() else "N/A")
            elif stat == 'q75':
                row.append(f"{df[col].quantile(0.75):.4f}" if not df[col].isnull().all() else "N/A")
            elif stat == 'max':
                row.append(f"{df[col].max():.4f}" if not df[col].isnull().all() else "N/A")
        rows.append(row)
    
    took_ms = int((time.time() - start_time) * 1000)
    
    return create_table_block(
        headers=headers,
        rows=rows,
        title="Numeric Column Statistics",
        note=f"Showing stats for {len(numeric_cols)} numeric columns. Try: 'Show missing' for null analysis"
    )


def action_missing(session_id: str) -> TableBlock:
    """Get missing value analysis (sorted descending, limit to 15 rows)"""
    start_time = time.time()
    
    df, meta = _load_dataframe(session_id)
    
    missing_data = []
    for col in meta.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        missing_data.append({
            'column': col,
            'missing_count': int(null_count),
            'missing_pct': float(null_pct)
        })
    
    # Sort by missing count descending, limit to 15
    missing_data = sorted(missing_data, key=lambda x: x['missing_count'], reverse=True)[:15]
    
    rows = []
    for data in missing_data:
        rows.append([
            data['column'],
            str(data['missing_count']),
            f"{data['missing_pct']:.2f}%"
        ])
    
    took_ms = int((time.time() - start_time) * 1000)
    
    return create_table_block(
        headers=["Column", "Missing Count", "Missing %"],
        rows=rows,
        title="Missing Values Analysis",
        note="Columns sorted by missing count. Try: 'Show stats' for numeric details"
    )


def action_histogram(session_id: str, column: str, bins: int = 30) -> Block:
    """Create histogram for a column (returns ImageBlock for numeric, TableBlock for non-numeric)"""
    start_time = time.time()
    
    df, meta = _load_dataframe(session_id)
    
    if column not in df.columns:
        raise ColumnNotFound(column)
    
    # Check if column is numeric
    is_numeric = pd.api.types.is_numeric_dtype(df[column])
    
    if is_numeric:
        # Generate histogram image
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import base64
        import io
        
        plt.figure(figsize=(10, 6))
        plt.hist(df[column].dropna(), bins=bins, alpha=0.7, color='#81E1FF', edgecolor='#264F68')
        plt.title(f'Histogram of {column}')
        plt.xlabel(column)
        plt.ylabel('Frequency')
        plt.gca().set_facecolor('#0F1720')
        plt.gcf().set_facecolor('#0B1114')
        plt.xticks(color='#BAE9F4')
        plt.yticks(color='#BAE9F4')
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor='#0B1114', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return create_image_block(
            image_base64=image_base64,
            title=f"Histogram of {column}",
        )
    else:
        # Return top value counts as table
        value_counts = df[column].value_counts().head(20)
        
        rows = []
        for value, count in value_counts.items():
            rows.append([str(value), str(count)])
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return create_table_block(
            headers=["Value", "Count"],
            rows=rows,
            title=f"Top Values for {column}",
            note="Showing top 20 values. Use 'histogram' on numeric columns for visual distribution"
        )

