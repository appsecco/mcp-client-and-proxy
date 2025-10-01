"""
Analytics Configuration for MCP Client Proxy
"""

# IMPORTANT: Replace with your actual PostHog API key!
POSTHOG_API_KEY = 'phc_yb1DOMUcKjOuY0kVNagZBJpfVr5Ct5d6dfCZbxO4h53'  # <-- REPLACE THIS!

# PostHog Host (use default cloud)
POSTHOG_HOST = 'https://us.i.posthog.com'

# Analytics Settings
ANALYTICS_ENABLED_BY_DEFAULT = True  # Opt-out approach

# Privacy Notice
PRIVACY_NOTICE = """
📊 Anonymous analytics enabled to improve this tool
   • No personal data collected
   • Disable with: --no-analytics
   • Learn more: https://github.com/appsecco/mcp-client-and-proxy#privacy
"""

# Events to track
TRACKED_EVENTS = {
    'session_start': True,
    'session_end': True,
    'proxy_started': True,
    'mcp_server_connected': True,
    'tool_executed': True,
    'burp_proxy_enabled': True,
    'proxychains_enabled': True,
    'errors': True,
}

# Metadata to include
INCLUDE_METADATA = {
    'os_info': True,
    'python_version': True,
    'tool_version': True,
    'session_id': True,
    'timestamp': True,
}