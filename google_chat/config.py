# google_chat/config.py
"""
Configuration management for Google Chat integration
Reads and validates environment variables
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_gchat_config() -> Dict[str, Any]:
    """
    Get Google Chat configuration from environment variables
    
    Returns:
        Dict with configuration values
    
    Raises:
        RuntimeError: If required configuration is missing when GCHAT_ENABLED=1
    """
    enabled = os.getenv("GCHAT_ENABLED", "0") == "1"
    
    if not enabled:
        return {
            "enabled": False,
            "mode": None,
            "space_name": None,
            "thread_strategy": "per_app"
        }
    
    # Get required configuration
    mode = os.getenv("GCHAT_MODE", "user")
    space_name = os.getenv("GCHAT_SPACE_NAME")
    thread_strategy = os.getenv("GCHAT_THREAD_STRATEGY", "per_app")
    
    # Validate mode
    if mode not in ["user", "app"]:
        raise RuntimeError(
            f"Invalid GCHAT_MODE: {mode}. Must be 'user' or 'app'"
        )
    
    # Validate space_name when enabled
    if not space_name:
        raise RuntimeError(
            "GCHAT_SPACE_NAME is required when GCHAT_ENABLED=1. "
            "Please set it to your Google Chat Space ID (e.g., spaces/AAAAxxxxxxx)"
        )
    
    # Validate thread_strategy
    valid_strategies = ["per_app", "per_error_type", "per_date", "none"]
    if thread_strategy not in valid_strategies:
        print(f"⚠️ Warning: Invalid GCHAT_THREAD_STRATEGY: {thread_strategy}. "
              f"Using 'per_app'. Valid options: {valid_strategies}")
        thread_strategy = "per_app"
    
    return {
        "enabled": True,
        "mode": mode,
        "space_name": space_name,
        "thread_strategy": thread_strategy
    }


def is_gchat_enabled() -> bool:
    """Quick check if Google Chat is enabled"""
    return os.getenv("GCHAT_ENABLED", "0") == "1"
