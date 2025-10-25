import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import base64
import io
import os
import requests
from typing import Tuple, Dict, Any, Optional
from fastapi import UploadFile

def load_csv_from_upload(file: UploadFile, session_id: str = None) -> Tuple[str, Dict[str, Any]]:
    """
    Load CSV from uploaded file
    
    Args:
        file: FastAPI UploadFile object
        session_id: Optional session ID for file naming
        
    Returns:
        Tuple of (file_path, df_info)
    """
    try:
        # Read file content
        content = file.file.read()
        
        # Try different encodings
        df = None
        for encoding in ['utf-8', 'latin-1']:
            try:
                df = pd.read_csv(io.StringIO(content.decode(encoding)))
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Could not decode CSV with utf-8 or latin-1 encoding")
        
        # Sample if too large
        original_rows = len(df)
        if len(df) > 200000:
            df = df.sample(n=200000, random_state=42)
            sampled = True
        else:
            sampled = False
        
        # Save to storage
        if session_id:
            file_path = f"storage/{session_id}_data.csv"
        else:
            file_path = f"storage/upload_{hash(content) % 1000000}_data.csv"
        df.to_csv(file_path, index=False)
        
        # Create df_info
        df_info = {
            "path": file_path,
            "rows": int(len(df)),
            "original_rows": int(original_rows),
            "columns": int(len(df.columns)),
            "sampled": sampled,
            "column_names": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage": int(df.memory_usage(deep=True).sum())
        }
        
        return file_path, df_info
        
    except Exception as e:
        raise ValueError(f"Error loading CSV from upload: {str(e)}")

def load_csv_from_url(url: str, session_id: str = None) -> Tuple[str, Dict[str, Any]]:
    """
    Load CSV from URL
    
    Args:
        url: URL to CSV file
        session_id: Optional session ID for file naming
        
    Returns:
        Tuple of (file_path, df_info)
    """
    try:
        # Download CSV
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Try different encodings
        df = None
        for encoding in ['utf-8', 'latin-1']:
            try:
                df = pd.read_csv(io.StringIO(response.text))
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Could not decode CSV with utf-8 or latin-1 encoding")
        
        # Sample if too large
        original_rows = len(df)
        if len(df) > 200000:
            df = df.sample(n=200000, random_state=42)
            sampled = True
        else:
            sampled = False
        
        # Save to storage
        if session_id:
            file_path = f"storage/{session_id}_data.csv"
        else:
            file_path = f"storage/url_{hash(url) % 1000000}_data.csv"
        df.to_csv(file_path, index=False)
        
        # Create df_info
        df_info = {
            "path": file_path,
            "rows": int(len(df)),
            "original_rows": int(original_rows),
            "columns": int(len(df.columns)),
            "sampled": sampled,
            "column_names": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_usage": int(df.memory_usage(deep=True).sum())
        }
        
        return file_path, df_info
        
    except requests.RequestException as e:
        raise ValueError(f"Error downloading CSV from URL: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error loading CSV from URL: {str(e)}")

def basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get basic statistics for DataFrame
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        Dictionary with trimmed describe() statistics
    """
    try:
        # Get describe statistics
        stats = df.describe(include='all')
        
        # Convert to dictionary and clean up
        stats_dict = {}
        
        for col in df.columns:
            col_stats = {}
            
            # Count non-null values
            col_stats['count'] = int(df[col].count())
            col_stats['null_count'] = int(df[col].isnull().sum())
            col_stats['null_percentage'] = float(df[col].isnull().sum() / len(df) * 100)
            
            # Data type
            col_stats['dtype'] = str(df[col].dtype)
            
            # Unique values
            col_stats['unique_count'] = int(df[col].nunique())
            
            # For numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats['mean'] = float(df[col].mean()) if not df[col].isnull().all() else None
                col_stats['std'] = float(df[col].std()) if not df[col].isnull().all() else None
                col_stats['min'] = float(df[col].min()) if not df[col].isnull().all() else None
                col_stats['max'] = float(df[col].max()) if not df[col].isnull().all() else None
                col_stats['median'] = float(df[col].median()) if not df[col].isnull().all() else None
                col_stats['q25'] = float(df[col].quantile(0.25)) if not df[col].isnull().all() else None
                col_stats['q75'] = float(df[col].quantile(0.75)) if not df[col].isnull().all() else None
            
            # For categorical/text columns
            else:
                col_stats['top'] = str(df[col].mode().iloc[0]) if not df[col].mode().empty else None
                col_stats['freq'] = int(df[col].value_counts().iloc[0]) if not df[col].empty else 0
            
            stats_dict[col] = col_stats
        
        return stats_dict
        
    except Exception as e:
        raise ValueError(f"Error calculating basic stats: {str(e)}")

def most_missing(df: pd.DataFrame) -> Tuple[Optional[str], int]:
    """
    Find column with most missing values
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        Tuple of (column_name, missing_count)
    """
    try:
        missing_counts = df.isnull().sum()
        
        if missing_counts.max() == 0:
            return None, 0
        
        max_missing_col = missing_counts.idxmax()
        max_missing_count = int(missing_counts[max_missing_col])
        
        return max_missing_col, max_missing_count
        
    except Exception as e:
        raise ValueError(f"Error finding most missing column: {str(e)}")

def histogram_png(df: pd.DataFrame, col: str) -> str:
    """
    Generate histogram PNG as base64 string
    
    Args:
        df: Pandas DataFrame
        col: Column name for histogram
        
    Returns:
        Base64 encoded PNG string
    """
    try:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
        
        # Check if column is numeric
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Column '{col}' is not numeric, cannot create histogram")
        
        # Create histogram
        plt.figure(figsize=(10, 6))
        plt.hist(df[col].dropna(), bins=30, alpha=0.7, color='#81E1FF', edgecolor='#264F68')
        plt.title(f'Histogram of {col}', color='#BAE9F4')
        plt.xlabel(col, color='#BAE9F4')
        plt.ylabel('Frequency', color='#BAE9F4')
        plt.xticks(color='#BAE9F4')
        plt.yticks(color='#BAE9F4')
        plt.gca().set_facecolor('#0F1720')
        plt.gcf().set_facecolor('#0B1114')
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor='#0B1114', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return image_base64
        
    except Exception as e:
        raise ValueError(f"Error creating histogram: {str(e)}")

def load_csv_from_path(file_path: str) -> pd.DataFrame:
    """
    Load CSV from file path (helper function)
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        Pandas DataFrame
    """
    try:
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        # Try different encodings
        df = None
        for encoding in ['utf-8', 'latin-1']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Could not decode CSV with utf-8 or latin-1 encoding")
        
        return df
        
    except Exception as e:
        raise ValueError(f"Error loading CSV from path: {str(e)}")
