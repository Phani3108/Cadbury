"""
Logging utilities for the Digital Twin System.
"""

import sys
import hashlib
import os
from pathlib import Path
from typing import Optional
from loguru import logger
from .config import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_format: Custom log format string
    """
    settings = get_settings()
    
    # Use provided values or fall back to settings
    level = log_level or settings.LOG_LEVEL
    format_str = log_format or settings.LOG_FORMAT
    log_path = log_file or "logs/digital_twin.log"
    
    # Create logs directory if it doesn't exist
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=format_str,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler
    logger.add(
        log_path,
        format=format_str,
        level=level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Add error file handler
    error_log_path = str(Path(log_path).parent / "errors.log")
    logger.add(
        error_log_path,
        format=format_str,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )


def get_logger(name: str = "digital_twin"):
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self):
        """Get logger instance for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(func):
    """
    Decorator to log function calls with parameters and return values.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger_instance = get_logger(func.__module__)
        
        # Log function call
        logger_instance.info(
            f"Calling {func.__name__} with args={args}, kwargs={kwargs}"
        )
        
        try:
            result = func(*args, **kwargs)
            logger_instance.info(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger_instance.error(f"{func.__name__} failed with error: {e}")
            raise
    
    return wrapper


def log_execution_time(func):
    """
    Decorator to log function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    import time
    
    def wrapper(*args, **kwargs):
        logger_instance = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger_instance.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger_instance.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {e}")
            raise
    
    return wrapper


def log_truth_policy_violation(violation_type: str, details: str, query: str):
    """
    Log truth policy violations for monitoring and improvement.
    
    Args:
        violation_type: Type of violation (hallucination, attribution, etc.)
        details: Details about the violation
        query: Original user query
    """
    logger_instance = get_logger("truth_policy")
    logger_instance.warning(
        f"Truth policy violation - Type: {violation_type}, "
        f"Details: {details}, Query: {query}"
    )


def log_response_quality(quality_score: float, response_length: int, query_type: str):
    """
    Log response quality metrics for monitoring.
    
    Args:
        quality_score: Quality score (0-1)
        response_length: Length of response
        query_type: Type of query
    """
    logger_instance = get_logger("response_quality")
    logger_instance.info(
        f"Response quality - Score: {quality_score:.2f}, "
        f"Length: {response_length}, Type: {query_type}"
    )


def log_search_performance(search_type: str, results_count: int, execution_time: float):
    """
    Log search performance metrics.
    
    Args:
        search_type: Type of search performed
        results_count: Number of results returned
        execution_time: Time taken for search
    """
    logger_instance = get_logger("search_performance")
    logger_instance.info(
        f"Search performance - Type: {search_type}, "
        f"Results: {results_count}, Time: {execution_time:.2f}s"
    )


def log_memory_usage(memory_type: str, operation: str, details: str):
    """
    Log memory operations for debugging.
    
    Args:
        memory_type: Type of memory (short_term, long_term)
        operation: Operation performed (store, retrieve, update)
        details: Additional details
    """
    logger_instance = get_logger("memory")
    logger_instance.debug(f"Memory {memory_type} - {operation}: {details}")


def log_integration_call(integration_type: str, operation: str, success: bool, details: str = ""):
    """
    Log integration calls (Jira, Graph, etc.).
    
    Args:
        integration_type: Type of integration
        operation: Operation performed
        success: Whether operation was successful
        details: Additional details
    """
    logger_instance = get_logger("integration")
    level = "info" if success else "error"
    logger_instance.log(
        level.upper(),
        f"Integration {integration_type} - {operation}: {'SUCCESS' if success else 'FAILED'} - {details}"
    )


def log_prompt_and_tokens(prompt_file: str, total_tokens: int, model: str = ""):
    """
    Log prompt hash and token count for cost tracking.
    
    Args:
        prompt_file: Path to prompt file
        total_tokens: Total tokens used
        model: Model used for generation
    """
    try:
        # Calculate SHA-256 hash of prompt file
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
                prompt_hash = hashlib.sha256(prompt_content.encode()).hexdigest()[:16]
        else:
            prompt_hash = "file_not_found"
        
        logger_instance = get_logger("prompt_tracking")
        logger_instance.info(
            f"Prompt tracking - File: {prompt_file}, "
            f"Hash: {prompt_hash}, Tokens: {total_tokens}, Model: {model}"
        )
        
        # Add to span attributes for telemetry
        try:
            from digital_twin.observability.tracing import add_span_attribute
            add_span_attribute("prompt_hash", prompt_hash)
            add_span_attribute("total_tokens", total_tokens)
            add_span_attribute("model_used", model)
        except ImportError:
            pass  # Tracing not available
            
    except Exception as e:
        logger_instance = get_logger("prompt_tracking")
        logger_instance.error(f"Failed to log prompt tracking: {e}")


# Initialize logging on module import
setup_logging() 