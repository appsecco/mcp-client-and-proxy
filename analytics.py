"""
MCP Client Proxy Analytics Module
Provides opt-out, privacy-focused analytics using PostHog
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

# Import configuration
try:
    from analytics_config import (
        POSTHOG_API_KEY,
        POSTHOG_HOST,
        ANALYTICS_ENABLED_BY_DEFAULT,
        PRIVACY_NOTICE,
        TRACKED_EVENTS,
        INCLUDE_METADATA
    )
except ImportError:
    # Fallback if config file doesn't exist
    POSTHOG_API_KEY = 'phc_YOUR_POSTHOG_PROJECT_API_KEY_HERE'
    POSTHOG_HOST = 'https://app.posthog.com'
    ANALYTICS_ENABLED_BY_DEFAULT = True
    PRIVACY_NOTICE = "📊 Anonymous analytics enabled (use --no-analytics to disable)"
    TRACKED_EVENTS = {'session_start': True, 'session_end': True}
    INCLUDE_METADATA = {'os_info': True, 'python_version': True}

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
    - Opt-out by default (can be disabled with --no-analytics)
    - Anonymous user tracking (no PII collected)
    - Session-based tracking
    - Graceful failure (never interrupts main functionality)
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 host: Optional[str] = None,
                 enabled: Optional[bool] = None,
                 debug: Optional[bool] = None,
                 silent: bool = False):
        """
        Initialize the analytics module.
        
        Args:
            api_key: PostHog project API key (defaults to configured key)
            host: PostHog host (defaults to configured host)
            enabled: Whether analytics is enabled (defaults to checking env vars)
            debug: Enable debug logging (defaults to checking env vars)
            silent: Don't print analytics notice
        """
        self.enabled = self._determine_if_enabled(enabled)
        self.debug = self._determine_debug_mode(debug)
        self.silent = silent
        self.posthog = None
        self.session_id = str(uuid.uuid4())
        self.anonymous_id = self._generate_anonymous_id()
        
        if self.debug:
            print(f"[Analytics Debug] Initializing - Enabled: {self.enabled}, Debug: {self.debug}")
        
        if self.enabled and POSTHOG_AVAILABLE:
            # Use provided key, environment variable, or configured key
            self.api_key = (
                api_key or 
                os.getenv('MCP_POSTHOG_API_KEY') or 
                POSTHOG_API_KEY
            )
            
            # Use provided host or configured host
            self.host = host or POSTHOG_HOST
            
            if self.debug:
                print(f"[Analytics Debug] API Key: {self.api_key[:20] if self.api_key else 'NOT SET'}...")
                print(f"[Analytics Debug] Host: {self.host}")
            
            if not self.api_key or 'YOUR' in self.api_key:
                if self.debug:
                    print("[Analytics Debug] No valid API key configured")
                self.enabled = False
                return
            
            try:
                self.posthog = Posthog(
                    project_api_key=self.api_key,
                    host=self.host,
                    debug=self.debug,
                    on_error=self._on_error
                )
                
                # Register cleanup on exit
                atexit.register(self._cleanup)
                
                # Show privacy notice if not silent
                if not self.silent and self.enabled:
                    print(PRIVACY_NOTICE)
                
                if self.debug:
                    print(f"[Analytics Debug] PostHog client initialized successfully")
                    print(f"[Analytics Debug] Session ID: {self.session_id[:8]}...")
                    print(f"[Analytics Debug] Anonymous ID: {self.anonymous_id}")
                    
            except Exception as e:
                if self.debug:
                    print(f"[Analytics Debug] Failed to initialize PostHog: {e}")
                self.enabled = False
        
        elif self.enabled and not POSTHOG_AVAILABLE:
            if not self.silent:
                print("Analytics enabled but PostHog library not installed. Run: pip install posthog")
            self.enabled = False
        elif self.debug:
            print(f"[Analytics Debug] Analytics disabled or PostHog not available")
    
    def _determine_debug_mode(self, debug: Optional[bool]) -> bool:
        """Determine if debug mode should be enabled."""
        if debug is not None:
            return debug
        
        # Check environment variable for debug mode
        env_debug = os.getenv('MCP_ANALYTICS_DEBUG', 'false').lower()
        return env_debug in ('true', '1', 'yes', 'on')
    
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
        
        # Use configured default (opt-out by default)
        return ANALYTICS_ENABLED_BY_DEFAULT
    
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
            print(f"[Analytics Debug] PostHog error: {error}")
            print(f"[Analytics Debug] Failed items: {len(items) if items else 0}")
    
    def _cleanup(self):
        """Clean up and send final events on exit."""
        try:
            if self.debug:
                print("[Analytics Debug] Cleanup: Flushing remaining events...")
            
            if self.enabled and self.posthog:
                self.track_session_end()
                # Ensure all events are sent
                self.posthog.flush()
                self.posthog.shutdown()
                
                if self.debug:
                    print("[Analytics Debug] Cleanup: Events flushed and client shutdown")
        except Exception as e:
            if self.debug:
                print(f"[Analytics Debug] Error during analytics cleanup: {e}")
    
    def _safe_track(self, event_name: str, properties: Optional[Dict[str, Any]] = None):
        """
        Safely track an event with error handling.
        
        Args:
            event_name: Name of the event to track
            properties: Optional event properties
        """
        if not self.enabled or not self.posthog:
            if self.debug:
                print(f"[Analytics Debug] Skipping event '{event_name}' - Analytics disabled or not initialized")
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
                print(f"[Analytics Debug] Tracked event: {event_name}")
                if properties:
                    print(f"[Analytics Debug]   Properties: {properties}")
                
        except Exception as e:
            if self.debug:
                print(f"[Analytics Debug] Failed to track event {event_name}: {e}")
    
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
    
    def track_session_end(self, event_name: Optional[str] = None):
        """Track the end of a session."""
        if event_name:
            self._safe_track(event_name)
        else:
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
    
    # Check if debug should be enabled from environment
    if 'debug' not in kwargs:
        env_debug = os.getenv('MCP_ANALYTICS_DEBUG', 'false').lower()
        if env_debug in ('true', '1', 'yes', 'on'):
            kwargs['debug'] = True
    
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