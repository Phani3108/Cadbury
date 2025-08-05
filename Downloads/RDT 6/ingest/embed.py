"""
Embedding utilities for the Digital Twin system.
"""

import os
import numpy as np
from typing import List, Optional
import logging
from sentence_transformers import SentenceTransformer
import openai

def get_logger(name):
    return logging.getLogger(name)

logger = get_logger("embed")

# Initialize fallback model
_fallback_model = None

def get_fallback_model():
    """Get or initialize the fallback sentence transformer model."""
    global _fallback_model
    if _fallback_model is None:
        logger.info("Loading fallback embedding model: all-MiniLM-L6-v2")
        _fallback_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _fallback_model

def get_embedding(text: str) -> List[float]:
    """
    Get embedding for text using Azure OpenAI or MiniLM fallback.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding
    """
    # Try Azure OpenAI first
    if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        try:
            return get_azure_embedding(text)
        except Exception as e:
            logger.warning(f"Azure OpenAI embedding failed: {e}, using fallback")
    
    # Use fallback model
    return get_fallback_embedding(text)

def get_azure_embedding(text: str) -> List[float]:
    """
    Get embedding using Azure OpenAI.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding
    """
    try:
        client = openai.AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        )
        
        response = client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"  # Azure OpenAI embedding model
        )
        
        return response.data[0].embedding
        
    except Exception as e:
        logger.error(f"Azure OpenAI embedding error: {e}")
        raise

def get_fallback_embedding(text: str) -> List[float]:
    """
    Get embedding using local sentence transformer model.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding
    """
    try:
        model = get_fallback_model()
        embedding = model.encode(text)
        return embedding.tolist()
        
    except Exception as e:
        logger.error(f"Fallback embedding error: {e}")
        # Return zero vector as last resort
        return [0.0] * 384  # MiniLM-L6-v2 dimension

def batch_get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for multiple texts efficiently.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embeddings
    """
    # Try Azure OpenAI first
    if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        try:
            return batch_get_azure_embeddings(texts)
        except Exception as e:
            logger.warning(f"Azure OpenAI batch embedding failed: {e}, using fallback")
    
    # Use fallback model
    return batch_get_fallback_embeddings(texts)

def batch_get_azure_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for multiple texts using Azure OpenAI.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embeddings
    """
    try:
        client = openai.AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        )
        
        response = client.embeddings.create(
            input=texts,
            model="text-embedding-ada-002"
        )
        
        return [data.embedding for data in response.data]
        
    except Exception as e:
        logger.error(f"Azure OpenAI batch embedding error: {e}")
        raise

def batch_get_fallback_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for multiple texts using local model.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embeddings
    """
    try:
        model = get_fallback_model()
        embeddings = model.encode(texts)
        return embeddings.tolist()
        
    except Exception as e:
        logger.error(f"Fallback batch embedding error: {e}")
        # Return zero vectors as last resort
        return [[0.0] * 384 for _ in texts]

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2) 