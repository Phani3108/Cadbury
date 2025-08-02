"""
Quote rewriter with caching for Digital Twin.
"""
import sqlite3
import hashlib
import os
from typing import Optional
from datetime import datetime, timedelta

# Cache database path
CACHE_DB = os.path.join('.cache', 'quotes.db')

def _ensure_cache_dir():
    """Ensure cache directory exists."""
    cache_dir = os.path.dirname(CACHE_DB)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

def _init_cache():
    """Initialize cache database."""
    _ensure_cache_dir()
    
    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quote_cache (
            hash TEXT PRIMARY KEY,
            original_text TEXT NOT NULL,
            rewritten_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def _get_cache_hash(text: str) -> str:
    """Generate hash for text."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def _get_cached_quote(text: str) -> Optional[str]:
    """Get cached rewritten quote."""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        text_hash = _get_cache_hash(text)
        
        cursor.execute('''
            SELECT rewritten_text, accessed_at 
            FROM quote_cache 
            WHERE hash = ?
        ''', (text_hash,))
        
        result = cursor.fetchone()
        
        if result:
            rewritten_text, accessed_at = result
            
            # Update access time
            cursor.execute('''
                UPDATE quote_cache 
                SET accessed_at = CURRENT_TIMESTAMP 
                WHERE hash = ?
            ''', (text_hash,))
            
            conn.commit()
            conn.close()
            
            return rewritten_text
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"Cache lookup failed: {e}")
        return None

def _cache_quote(original_text: str, rewritten_text: str):
    """Cache rewritten quote."""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        text_hash = _get_cache_hash(original_text)
        
        cursor.execute('''
            INSERT OR REPLACE INTO quote_cache 
            (hash, original_text, rewritten_text, created_at, accessed_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (text_hash, original_text, rewritten_text))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Cache storage failed: {e}")

def _cleanup_old_cache(days: int = 30):
    """Clean up old cache entries."""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            DELETE FROM quote_cache 
            WHERE accessed_at < ?
        ''', (cutoff_date,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} old cache entries")
            
    except Exception as e:
        print(f"Cache cleanup failed: {e}")

def rewrite_quote(text: str) -> str:
    """
    Rewrite Ramki's quotes to be more coherent and actionable.
    
    Args:
        text: Original quote text
        
    Returns:
        Rewritten quote text
    """
    if not text or not text.strip():
        return text
    
    # Initialize cache
    _init_cache()
    
    # Check cache first
    cached_result = _get_cached_quote(text)
    if cached_result:
        return cached_result
    
    # Simple rewriting rules (in production, use LLM)
    rewritten = text.strip()
    
    # Fix common issues
    if rewritten.endswith('...'):
        rewritten = rewritten[:-3] + '.'
    
    if rewritten.endswith('..'):
        rewritten = rewritten[:-2] + '.'
    
    # Ensure proper sentence ending
    if not rewritten.endswith(('.', '!', '?')):
        rewritten += '.'
    
    # Capitalize first letter
    if rewritten and rewritten[0].islower():
        rewritten = rewritten[0].upper() + rewritten[1:]
    
    # Remove excessive punctuation
    rewritten = rewritten.replace('...', '.')
    rewritten = rewritten.replace('..', '.')
    
    # Cache the result
    _cache_quote(text, rewritten)
    
    return rewritten

def get_cache_stats() -> dict:
    """Get cache statistics."""
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM quote_cache')
        total_entries = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM quote_cache 
            WHERE accessed_at > datetime('now', '-1 day')
        ''')
        recent_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'recent_entries': recent_entries,
            'cache_size_mb': os.path.getsize(CACHE_DB) / (1024 * 1024) if os.path.exists(CACHE_DB) else 0
        }
        
    except Exception as e:
        print(f"Cache stats failed: {e}")
        return {'error': str(e)}

# Cleanup old entries on import
_cleanup_old_cache() 