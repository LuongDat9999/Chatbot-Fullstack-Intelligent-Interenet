"""CSV Registry - In-memory storage for CSV data with TTL"""
import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd


@dataclass
class CsvMeta:
    """Metadata for a CSV file"""
    csv_path: str
    columns: list
    dtypes: dict
    rows: int
    loaded_at: datetime


class CsvRegistry:
    """In-memory registry for CSV data with TTL"""
    
    def __init__(self, ttl_hours: int = 24, max_entries: int = 100):
        self.ttl_hours = ttl_hours
        self.max_entries = max_entries
        self._data: Dict[str, pd.DataFrame] = {}
        self._meta: Dict[str, CsvMeta] = {}
    
    def has(self, session_id: str) -> bool:
        """Check if session has CSV data"""
        if session_id not in self._data:
            return False
        
        # Check TTL
        meta = self._meta[session_id]
        if datetime.now() - meta.loaded_at > timedelta(hours=self.ttl_hours):
            self._remove(session_id)
            return False
        
        return True
    
    def get(self, session_id: str) -> Optional[pd.DataFrame]:
        """Get DataFrame for session"""
        if not self.has(session_id):
            return None
        return self._data[session_id]
    
    def get_meta(self, session_id: str) -> Optional[CsvMeta]:
        """Get metadata for session"""
        if not self.has(session_id):
            return None
        return self._meta[session_id]
    
    def put(self, session_id: str, df: pd.DataFrame, csv_path: str, columns: list, dtypes: dict):
        """Store DataFrame with metadata"""
        # Enforce max entries
        if len(self._data) >= self.max_entries and session_id not in self._data:
            # Remove oldest entry
            oldest = min(self._meta.items(), key=lambda x: x[1].loaded_at)
            self._remove(oldest[0])
        
        self._data[session_id] = df
        
        self._meta[session_id] = CsvMeta(
            csv_path=csv_path,
            columns=columns,
            dtypes=dtypes,
            rows=len(df),
            loaded_at=datetime.now()
        )
    
    def _remove(self, session_id: str):
        """Remove session data"""
        self._data.pop(session_id, None)
        self._meta.pop(session_id, None)
    
    def clear(self):
        """Clear all data"""
        self._data.clear()
        self._meta.clear()


# Singleton instance
registry = CsvRegistry()


def load_csv_for_session(session_id: str):
    """
    Load CSV for session from registry or file system
    
    Returns:
        Tuple of (DataFrame, Meta) or (None, None) if not found
    """
    # Try registry first
    if registry.has(session_id):
        df = registry.get(session_id)
        meta = registry.get_meta(session_id)
        return df, meta
    
    # Try file system
    session_meta_path = "storage/session_meta.json"
    if os.path.exists(session_meta_path):
        try:
            with open(session_meta_path, 'r') as f:
                meta_data = json.load(f)
                
            if session_id in meta_data:
                csv_meta = meta_data[session_id]
                csv_path = csv_meta.get("csv_path")
                
                if csv_path and os.path.exists(csv_path):
                    # Load from services
                    from services.csv_tools import load_csv_from_path
                    df = load_csv_from_path(csv_path)
                    
                    # Add to registry
                    registry.put(
                        session_id,
                        df,
                        csv_path,
                        csv_meta["columns"],
                        csv_meta["dtypes"]
                    )
                    
                    meta = CsvMeta(
                        csv_path=csv_path,
                        columns=csv_meta["columns"],
                        dtypes=csv_meta["dtypes"],
                        rows=csv_meta["rows"],
                        loaded_at=datetime.now()
                    )
                    
                    return df, meta
        except Exception as e:
            print(f"Error loading CSV from file system: {e}")
    
    return None, None

