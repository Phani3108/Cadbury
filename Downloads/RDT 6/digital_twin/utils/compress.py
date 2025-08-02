"""
Compression utilities for Digital Twin using Chain-of-Density.
"""
import openai
import os
from typing import List
from ingest.types import Chunk
from digital_twin.utils.config import openai_kwargs, get_model_key

def compress(chunks: List[Chunk], query: str = "", limit_tokens: int = 1500) -> str:
    """
    Compress chunks using Chain-of-Density approach.
    
    Args:
        chunks: List of chunks to compress
        query: User query for context
        limit_tokens: Target token limit
        
    Returns:
        Compressed text string
    """
    if not chunks:
        return ""
    
    # Concatenate chunks with metadata
    full_text = ""
    for chunk in chunks:
        if chunk.speaker:
            full_text += f"{chunk.speaker}: {chunk.text}\n\n"
        else:
            full_text += f"{chunk.text}\n\n"
    
    # If text is already short enough, return as is
    if len(full_text.split()) <= limit_tokens // 4:  # Rough token estimation
        return full_text.strip()
    
    try:
        # Use OpenAI for compression
        model_key = get_model_key(is_heavy=False)  # Use cheap model for compression
        kwargs = openai_kwargs(model_key)
        client = openai.AsyncOpenAI(**kwargs)
        
        # Get the actual model name
        model_name = os.getenv(model_key, "gpt-3.5-turbo")
        
        prompt = f"""
Compress the following text while preserving key entities, dates, and important information.
Keep the text under {limit_tokens} tokens.

Query context: {query}

Text to compress:
{full_text}

Compressed version:
"""
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=limit_tokens,
            temperature=0.1,
        )
        
        compressed_text = response.choices[0].message.content.strip()
        return compressed_text
        
    except Exception as e:
        print(f"⚠️  Compression failed: {e}, returning truncated text")
        # Fallback: simple truncation
        words = full_text.split()
        return " ".join(words[:limit_tokens // 4])

def estimate_tokens(text: str) -> int:
    """Rough token estimation."""
    return len(text.split()) * 1.3  # Rough approximation 