"""
Logging utilities for LokerPuller.
"""

import logging
import os
from typing import Optional


def setup_logging(
    name: str = "LokerPuller",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup enhanced logging with detailed formatting.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Add file handler if specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the standard LokerPuller format.
    
    Args:
        name: Logger name (will be prefixed with 'LokerPuller.')
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"LokerPuller.{name}")


def log_system_resources(logger: logging.Logger) -> None:
    """
    Log current system resource usage.
    
    Args:
        logger: Logger instance to use
    """
    try:
        # Get memory info (Linux/Unix systems)
        if os.path.exists('/proc/meminfo'):
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            mem_total = None
            mem_available = None
            for line in meminfo.split('\n'):
                if 'MemTotal:' in line:
                    mem_total = int(line.split()[1]) // 1024  # Convert to MB
                elif 'MemAvailable:' in line:
                    mem_available = int(line.split()[1]) // 1024  # Convert to MB
            
            if mem_total and mem_available:
                mem_used = mem_total - mem_available
                mem_percent = (mem_used / mem_total) * 100
                logger.info(f"💾 Memory: {mem_used}MB/{mem_total}MB ({mem_percent:.1f}% used)")
        
        # Get load average (Linux/Unix systems)
        if os.path.exists('/proc/loadavg'):
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.read().strip().split()[0]
            logger.info(f"⚡ Load average: {load_avg}")
        
    except Exception as e:
        logger.debug(f"Could not read system resources: {e}")


def cleanup_old_logs(log_dir: str, days_to_keep: int = 7) -> None:
    """
    Clean up old log files.
    
    Args:
        log_dir: Directory containing log files
        days_to_keep: Number of days to keep logs
    """
    if not os.path.exists(log_dir):
        return
        
    import time
    from pathlib import Path
    
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    
    for log_file in Path(log_dir).glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
            except OSError:
                pass  # Ignore errors when deleting log files 