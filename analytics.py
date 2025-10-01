"""
MCP Client Proxy Analytics Module
Provides opt-in, privacy-focused analytics using PostHog
"""

import os
import sys
import uuid
import platform
import hashlib
import atexit
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps
import logging

# Conditional import to make analytics optional
try:
    from posthog import Posthog
    POSTHOG_AVAILABLE = True
except ImportError:
    POSTHOG_AVAILABLE = False

logger = logging.getLogger(__name__)


class MCPAnalytics:
    """
    Privacy-focused analytics for MCP Client Proxy.
    
    Features:
    - Opt-in by default (requires explicit enabling)
    - Anonymous user tracking (no PII collected)
    - Session-based tracking
    - Graceful failure (never interrupts main functionality)
    """
    
    # Default PostHog API key for MCP Client Proxy
    # This is a project-specific key that only accepts data for this tool
    DEFAULT_API_KEY = 'phc_yb1DOMUcKjOuY0kVNagZBJpfVr5Ct5d6dfCZbxO4h53'  # Replace with your actual key
    HOST = 'https://us.i.posthog.com'
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 host: str = HOST,
                 enabled: Optional[bool] = None,
                 debug: bool = False):
        """
        Initialize the analytics module.
        
        Args:
            api_key: PostHog project API key (defaults to built-in key)
            host: PostHog host (default: cloud instance, can be self-hosted)
            enabled: Whether analytics is enabled (defaults to checking env vars)
            debug: Enable debug logging
        """
        self.enabled = self._determine_if_enabled(enabled)
        self.debug = debug
        self.posthog = None
        self.session_id = str(uuid.uuid4())
        self.anonymous_id = self._generate_anonymous_id()
        
        if self.enabled and POSTHOG_AVAILABLE:
            # Use provided key, environment variable, or default key
            self.api_key = (
                api_key or 
                os.getenv('MCP_POSTHOG_API_KEY') or 
                self.DEFAULT_API_KEY
            )
            
            if not self.api_key or self.api_key == 'phc_YOUR_POSTHOG_PROJECT_API_KEY_HERE':
                logger.warning("Analytics enabled but no valid API key configured. Please set your PostHog API key.")
                self.enabled = False
                return
            
            try:
                self.posthog = Posthog(
                    project_api_key=self.api_key,
                    host=host,
                    debug=debug,
                    # Disable automatic capturing to have full control
                    autocapture=False,
                    # Batch events for better performance
                    on_error=self._on_error
                )
                
                # Register cleanup on exit
                atexit.register(self._cleanup)
                
                if self.debug:
                    logger.info(f"Analytics initialized (session: {self.session_id[:8]}...)")
                    
            except Exception as e:
                if self.debug:
                    logger.error(f"Failed to initialize PostHog: {e}")
                self.enabled = False
        
        elif self.enabled and not POSTHOG_AVAILABLE:
            logger.info("Analytics enabled but PostHog library not installed. Run: pip install posthog")
            self.enabled = False
    
    def _determine_if_enabled(self, enabled: Optional[bool]) -> bool:
        """Determine if analytics should be enabled based on environment and parameters."""
        if enabled is not None:
            return enabled
        
        # Check if explicitly disabled via environment
        env_disabled = os.getenv('MCP_ANALYTICS_DISABLED', 'false').lower()
        if env_disabled in ('true', '1', 'yes', 'on'):
            return False
        
        # Check if explicitly enabled/disabled via MCP_ANALYTICS_ENABLED
        env_enabled = os.getenv('MCP_ANALYTICS_ENABLED')
        if env_enabled is not None:
            return env_enabled.lower() in ('true', '1', 'yes', 'on')
        
        # Default to enabled (opt-out)
        return True
    
    def _generate_anonymous_id(self) -> str:
        """
        Generate a consistent but anonymous user ID.
        Based on machine characteristics but hashed for privacy.
        """
        try:
            # Combine machine characteristics for a stable ID
            machine_info = f"{platform.node()}{platform.system()}{platform.machine()}"
            # Add Python version for better segmentation
            machine_info += f"{sys.version_info.major}.{sys.version_info.minor}"
            
            # Hash for privacy - only first 16 chars for readability
            return hashlib.sha256(machine_info.encode()).hexdigest()[:16]
        except Exception:
            # Fallback to random if we can't get machine info
            return str(uuid.uuid4())[:16]
    
    def _on_error(self, error: Exception, items: list):
        """Handle PostHog errors gracefully."""
        if self.debug:
            logger.error(f"PostHog error: {error}")
    
    def _cleanup(self):
        """Clean up and send final events on exit."""
        try:
            if self.enabled and self.posthog:
                self.track_session_end()
                # Ensure all events are sent
                self.posthog.flush()
                self.posthog.shutdown()
        except Exception as e:
            if self.debug:
                logger.error(f"Error during analytics cleanup: {e}")
    
    def _safe_track(self, event_name: str, properties: Optional[Dict[str, Any]] = None):
        """
        Safely track an event with error handling.
        
        Args:
            event_name: Name of the event to track
            properties: Optional event properties
        """
        if not self.enabled or not self.posthog:
            return
        
        try:
            # Merge default properties with provided ones
            default_props = {
                'session_id': self.session_id,
                'version': self._get_version(),
                'os': platform.system(),
                'os_version': platform.version(),
                'python_version': platform.python_version(),
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            if properties:
                default_props.update(properties)
            
            self.posthog.capture(
                distinct_id=self.anonymous_id,
                event=event_name,
                properties=default_props
            )
            
            if self.debug:
                logger.debug(f"Tracked event: {event_name}")
                
        except Exception as e:
            if self.debug:
                logger.error(f"Failed to track event {event_name}: {e}")
    
    def _get_version(self) -> str:
        """Get the version of the MCP client proxy."""
        # You can update this to read from your actual version file
        return os.getenv('MCP_VERSION', '1.0.0')
    
    # Public tracking methods
    
    def track_session_start(self, server_type: Optional[str] = None):
        """Track the start of a new session."""
        properties = {}
        if server_type:
            properties['server_type'] = server_type
        
        self._safe_track('mcp_session_started', properties)
    
    def track_session_end(self):
        """Track the end of a session."""
        self._safe_track('mcp_session_ended')
    
    def track_server_connected(self, server_name: str, server_type: Optional[str] = None):
        """Track successful server connection."""
        properties = {
            'server_name': server_name,
        }
        if server_type:
            properties['server_type'] = server_type
        
        self._safe_track('mcp_server_connected', properties)
    
    def track_command_executed(self, command: str, success: bool = True):
        """Track command execution."""
        self._safe_track('mcp_command_executed', {
            'command': command,
            'success': success
        })
    
    def track_error(self, error_type: str, error_message: Optional[str] = None):
        """Track errors (without sensitive information)."""
        properties = {
            'error_type': error_type,
        }
        if error_message and self.debug:
            # Only include error message in debug mode
            # Sanitize to remove potential sensitive data
            properties['error_message'] = error_message[:200]  # Truncate long messages
        
        self._safe_track('mcp_error', properties)
    
    def track_feature_used(self, feature_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Track usage of specific features."""
        properties = {'feature': feature_name}
        if metadata:
            properties.update(metadata)
        
        self._safe_track('mcp_feature_used', properties)
    
    # Decorator for tracking function execution
    
    def track_function(self, event_name: Optional[str] = None):
        """
        Decorator to track function execution.
        
        Usage:
            @analytics.track_function("important_operation")
            def my_function():
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = event_name or f"function_{func.__name__}"
                start_time = datetime.utcnow()
                
                try:
                    result = func(*args, **kwargs)
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    self._safe_track(f'mcp_{name}_completed', {
                        'duration_seconds': duration,
                        'success': True
                    })
                    return result
                    
                except Exception as e:
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    self._safe_track(f'mcp_{name}_failed', {
                        'duration_seconds': duration,
                        'success': False,
                        'error_type': type(e).__name__
                    })
                    raise
            
            return wrapper if self.enabled else func
        return decorator
    
    def is_enabled(self) -> bool:
        """Check if analytics is enabled."""
        return self.enabled
    
    def get_session_id(self) -> str:
        """Get the current session ID."""
        return self.session_id
    
    def get_anonymous_id(self) -> str:
        """Get the anonymous user ID."""
        return self.anonymous_id


# Singleton instance for easy import
_analytics_instance = None

def get_analytics(force_new: bool = False, **kwargs) -> MCPAnalytics:
    """
    Get or create the analytics singleton instance.
    
    Args:
        force_new: Force creation of a new instance
        **kwargs: Arguments to pass to MCPAnalytics constructor
    
    Returns:
        MCPAnalytics instance
    """
    global _analytics_instance
    
    if _analytics_instance is None or force_new:
        _analytics_instance = MCPAnalytics(**kwargs)
    
    return _analytics_instance


# Convenience functions for direct usage
def track_session_start(server_type: Optional[str] = None):
    """Convenience function to track session start."""
    get_analytics().track_session_start(server_type)

def track_server_connected(server_name: str, server_type: Optional[str] = None):
    """Convenience function to track server connection."""
    get_analytics().track_server_connected(server_name, server_type)

def track_command_executed(command: str, success: bool = True):
    """Convenience function to track command execution."""
    get_analytics().track_command_executed(command, success)

def track_error(error_type: str, error_message: Optional[str] = None):
    """Convenience function to track errors."""
    get_analytics().track_error(error_type, error_message)

def is_analytics_enabled() -> bool:
    """Check if analytics is enabled."""
    return get_analytics().is_enabled()