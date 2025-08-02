"""
Input/output validation utilities for the Digital Twin System.
"""

import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ValidationError, validator
from .logger import get_logger


class QueryValidator(BaseModel):
    """Validator for user queries."""
    
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query content."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        
        if len(v.strip()) < 2:
            raise ValueError("Query must be at least 2 characters long")
        
        if len(v) > 1000:
            raise ValueError("Query cannot exceed 1000 characters")
        
        # Check for potentially harmful content
        harmful_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload=',
            r'onerror='
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Query contains potentially harmful content")
        
        return v.strip()
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Validate user ID format."""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]{1,50}$', v):
                raise ValueError("User ID must be alphanumeric with hyphens/underscores only")
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9_-]{1,100}$', v):
                raise ValueError("Session ID must be alphanumeric with hyphens/underscores only")
        return v


class ResponseValidator(BaseModel):
    """Validator for system responses."""
    
    response: str
    query: str
    sources: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    response_type: Optional[str] = None
    
    @validator('response')
    def validate_response(cls, v):
        """Validate response content."""
        if not v or not v.strip():
            raise ValueError("Response cannot be empty")
        
        if len(v) > 10000:
            raise ValueError("Response cannot exceed 10000 characters")
        
        # Check for basic grammar indicators
        if not v.strip().endswith(('.', '!', '?')):
            raise ValueError("Response should end with proper punctuation")
        
        return v
    
    @validator('confidence_score')
    def validate_confidence_score(cls, v):
        """Validate confidence score range."""
        if v is not None:
            if not 0.0 <= v <= 1.0:
                raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v
    
    @validator('response_type')
    def validate_response_type(cls, v):
        """Validate response type."""
        valid_types = [
            'general', 'specific', 'action_items', 'meeting_scheduling',
            'insights', 'technical', 'follow_up', 'error'
        ]
        if v is not None and v not in valid_types:
            raise ValueError(f"Response type must be one of: {valid_types}")
        return v


class KnowledgeBaseValidator(BaseModel):
    """Validator for knowledge base entries."""
    
    content: str
    source: str
    timestamp: Optional[str] = None
    speaker: Optional[str] = None
    topic: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('content')
    def validate_content(cls, v):
        """Validate content."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        
        if len(v) > 50000:
            raise ValueError("Content cannot exceed 50000 characters")
        
        return v.strip()
    
    @validator('source')
    def validate_source(cls, v):
        """Validate source format."""
        if not v or not v.strip():
            raise ValueError("Source cannot be empty")
        
        # Check for valid file extensions or URLs
        valid_extensions = ['.txt', '.md', '.pdf', '.doc', '.docx']
        if not any(v.lower().endswith(ext) for ext in valid_extensions) and not v.startswith(('http://', 'https://')):
            raise ValueError("Source must be a valid file path or URL")
        
        return v.strip()
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate timestamp format."""
        if v is not None:
            # Basic timestamp validation (ISO format)
            timestamp_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$'
            if not re.match(timestamp_pattern, v):
                raise ValueError("Timestamp must be in ISO format")
        return v


class MeetingRequestValidator(BaseModel):
    """Validator for meeting scheduling requests."""
    
    topic: str
    attendees: List[str]
    priority: str
    duration: Optional[int] = None
    preferred_time: Optional[str] = None
    
    @validator('topic')
    def validate_topic(cls, v):
        """Validate meeting topic."""
        if not v or not v.strip():
            raise ValueError("Meeting topic cannot be empty")
        
        if len(v) > 200:
            raise ValueError("Meeting topic cannot exceed 200 characters")
        
        return v.strip()
    
    @validator('attendees')
    def validate_attendees(cls, v):
        """Validate attendees list."""
        if not v:
            raise ValueError("At least one attendee must be specified")
        
        if len(v) > 20:
            raise ValueError("Cannot have more than 20 attendees")
        
        for attendee in v:
            if not attendee or not attendee.strip():
                raise ValueError("Attendee names cannot be empty")
            if len(attendee) > 100:
                raise ValueError("Attendee names cannot exceed 100 characters")
        
        return [attendee.strip() for attendee in v]
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority level."""
        valid_priorities = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5']
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        """Validate meeting duration."""
        if v is not None:
            if not 15 <= v <= 480:  # 15 minutes to 8 hours
                raise ValueError("Meeting duration must be between 15 and 480 minutes")
        return v


def validate_query(query: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate a user query.
    
    Args:
        query: User query string
        user_id: Optional user ID
        session_id: Optional session ID
        
    Returns:
        Validated query data
        
    Raises:
        ValidationError: If validation fails
    """
    logger = get_logger("validators")
    
    try:
        validated_data = QueryValidator(
            query=query,
            user_id=user_id,
            session_id=session_id
        )
        logger.debug(f"Query validation successful: {query[:50]}...")
        return validated_data.dict()
    except ValidationError as e:
        logger.warning(f"Query validation failed: {e}")
        raise


def validate_response(response: str, query: str, **kwargs) -> Dict[str, Any]:
    """
    Validate a system response.
    
    Args:
        response: System response string
        query: Original user query
        **kwargs: Additional response parameters
        
    Returns:
        Validated response data
        
    Raises:
        ValidationError: If validation fails
    """
    logger = get_logger("validators")
    
    try:
        validated_data = ResponseValidator(
            response=response,
            query=query,
            **kwargs
        )
        logger.debug(f"Response validation successful: {response[:50]}...")
        return validated_data.dict()
    except ValidationError as e:
        logger.warning(f"Response validation failed: {e}")
        raise


def validate_kb_entry(content: str, source: str, **kwargs) -> Dict[str, Any]:
    """
    Validate a knowledge base entry.
    
    Args:
        content: Entry content
        source: Source identifier
        **kwargs: Additional entry parameters
        
    Returns:
        Validated KB entry data
        
    Raises:
        ValidationError: If validation fails
    """
    logger = get_logger("validators")
    
    try:
        validated_data = KnowledgeBaseValidator(
            content=content,
            source=source,
            **kwargs
        )
        logger.debug(f"KB entry validation successful: {content[:50]}...")
        return validated_data.dict()
    except ValidationError as e:
        logger.warning(f"KB entry validation failed: {e}")
        raise


def validate_meeting_request(topic: str, attendees: List[str], priority: str, **kwargs) -> Dict[str, Any]:
    """
    Validate a meeting scheduling request.
    
    Args:
        topic: Meeting topic
        attendees: List of attendees
        priority: Priority level
        **kwargs: Additional meeting parameters
        
    Returns:
        Validated meeting request data
        
    Raises:
        ValidationError: If validation fails
    """
    logger = get_logger("validators")
    
    try:
        validated_data = MeetingRequestValidator(
            topic=topic,
            attendees=attendees,
            priority=priority,
            **kwargs
        )
        logger.debug(f"Meeting request validation successful: {topic}")
        return validated_data.dict()
    except ValidationError as e:
        logger.warning(f"Meeting request validation failed: {e}")
        raise


def sanitize_text(text: str) -> str:
    """
    Sanitize text content for safe processing.
    
    Args:
        text: Raw text content
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially harmful HTML/script tags
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<.*?>', '', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
    
    return text.strip()


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url)) 