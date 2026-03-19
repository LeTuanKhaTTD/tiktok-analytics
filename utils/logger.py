"""
Logging System for YouTube Analytics
Provides structured logging with file rotation
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


class AnalyticsLogger:
    """Centralized logging system"""
    
    def __init__(
        self,
        name: str = "youtube_analytics",
        log_dir: str = "logs",
        level: int = logging.INFO,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        """
        Initialize logger
        
        Args:
            name: Logger name
            log_dir: Directory to store logs
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes: Max size before rotation
            backup_count: Number of backup files
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Avoid duplicate handlers
        if self.logger.handlers:
            return
        
        # Create log directory
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Format
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        log_file = log_path / f"{name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)
    
    def log_api_call(self, endpoint: str, status: str, duration: float):
        """Log API call"""
        self.info(f"API Call: {endpoint} | Status: {status} | Duration: {duration:.2f}s")
    
    def log_analysis(self, analysis_type: str, items_count: int, duration: float):
        """Log analysis operation"""
        self.info(f"Analysis: {analysis_type} | Items: {items_count} | Duration: {duration:.2f}s")


# ===== ERROR HANDLER DECORATOR =====

def handle_errors(logger: Optional[AnalyticsLogger] = None):
    """
    Decorator để handle errors và log
    
    Usage:
        @handle_errors(logger)
        def my_function():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if logger:
                    logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                else:
                    print(f"Error in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator


# ===== PERFORMANCE MONITOR =====

import time
from functools import wraps


def monitor_performance(logger: Optional[AnalyticsLogger] = None):
    """
    Decorator để monitor performance
    
    Usage:
        @monitor_performance(logger)
        def slow_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if logger:
                    logger.info(f"{func.__name__} completed in {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                if logger:
                    logger.error(f"{func.__name__} failed after {duration:.2f}s: {str(e)}")
                
                raise
        
        return wrapper
    return decorator


# ===== EXAMPLE USAGE =====

if __name__ == '__main__':
    # Initialize logger
    logger = AnalyticsLogger(name="test_logger", level=logging.DEBUG)
    
    # Test logging levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test API logging
    logger.log_api_call("/api/videos", "success", 1.23)
    
    # Test analysis logging
    logger.log_analysis("sentiment", 150, 45.67)
    
    # Test decorator
    @handle_errors(logger)
    @monitor_performance(logger)
    def test_function():
        time.sleep(0.5)
        return "Success"
    
    result = test_function()
    print(f"Result: {result}")
