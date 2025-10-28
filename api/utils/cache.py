"""Cache utility for chart rendering"""
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


# In-memory cache with TTL
_cache: Dict[str, Tuple[Any, datetime]] = {}
_cache_ttl_minutes = 10


def get_cache_key(session_id: str, spec: Any) -> str:
    """Generate cache key from session_id and ChartSpec"""
    spec_json = json.dumps(spec.dict() if hasattr(spec, 'dict') else spec, sort_keys=True, default=str)
    key_str = f"{session_id}:{spec_json}"
    return hashlib.md5(key_str.encode()).hexdigest()


def cache_get(key: str) -> Optional[Any]:
    """Get from cache if not expired"""
    if key not in _cache:
        return None
    
    value, timestamp = _cache[key]
    
    # Check TTL
    if datetime.now() - timestamp > timedelta(minutes=_cache_ttl_minutes):
        del _cache[key]
        return None
    
    return value


def cache_set(key: str, value: Any):
    """Set cache with current timestamp"""
    _cache[key] = (value, datetime.now())


def cache_clear():
    """Clear all cache"""
    _cache.clear()

