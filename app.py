#!/usr/bin/env python3
"""
Generic MCP Client and Proxy

This script provides a generic implementation that works with mcp_config.json
to connect to any MCP server and interact with its available tools via HTTP proxy.

Brought to you by Appsecco - Product Security Experts
"""

import json
import os
import sys
import subprocess
import time
import threading
import queue
import requests
from typing import Dict, Any, List, Optional
import argparse


# Appsecco Version Information
APPSECCO_VERSION = "0.1.0"
APPSECCO_BUILD = "Profesh Edition with vibes"
APPSECCO_COPYRIGHT = "© 2025 Appsecco. All rights reserved."


# Appsecco ASCII Art Banner
APPSECCO_ASCII_ART = """
   ###    ########  ########   ######  ########  ######   ######   ####### 
  ## ##   ##     ## ##     ## ##    ## ##       ##    ## ##    ## ##     ##
 ##   ##  ##     ## ##     ## ##       ##       ##       ##       ##     ##
##     ## ########  ########   ######  ######   ##       ##       ##     ##
######### ##        ##              ## ##       ##       ##       ##     ##
##     ## ##        ##        ##    ## ##       ##    ## ##    ## ##     ##
##     ## ##        ##         ######  ########  ######   ######   ####### 
"""

APPSECCO_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     ###    ########  ########   ######  ########  ######   ######   #######  ║
║    ## ##   ##     ## ##     ## ##    ## ##       ##    ## ##    ## ##     ## ║
║   ##   ##  ##     ## ##     ## ##       ##       ##       ##       ##     ## ║    
║  ##     ## ########  ########   ######  ######   ##       ##       ##     ## ║
║  ######### ##        ##              ## ##       ##       ##       ##     ## ║
║  ##     ## ##        ##        ##    ## ##       ##    ## ##    ## ##     ## ║
║  ##     ## ##        ##         ######  ########  ######   ######   #######  ║
║                                                                              ║
║                                                                              ║
║      MCP CLIENT AND PROXY                                                    ║
║      A generic MCP client with ability to proxy MCP server traffic to your   ║
║      Burp Suite for inspection.                                              ║
║                                                                              ║
║      Version {version} - {build}                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

    🛠️  Built for pentesting MCP servers using STDIO transport
    🎯  Aimed at folks who use Burp Suite for their app testing workflows
    💻  Vibe coded, MIT License, not meant for production use

    📧  Email: HackMyProduct@appsecco.com | 🌐 Website: https://appsecco.com
""".format(version=APPSECCO_VERSION, build=APPSECCO_BUILD)

# Appsecco Tagline
APPSECCO_TAGLINE = """
🔒  WE HACK YOUR PRODUCTS & INFRA BEFORE ATTACKERS DO  🔒
"""


class MCPConfig:
    """Appsecco MCP Client and Proxy - Send MCP Server Traffic to your Burp Suite"""
    
    def __init__(self, config_file: str = "mcp_config.json"):
        """
        Initialize Appsecco MCP Client and Proxy configuration from JSON file
        
        Args:
            config_file: Path to the MCP configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file '{self.config_file}' not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific server"""
        servers = self.config.get("mcpServers", {})
        return servers.get(server_name)
    
    def list_servers(self) -> List[str]:
        """List all available server names"""
        servers = self.config.get("mcpServers", {})
        return list(servers.keys())


class MCPClient:
    """Appsecco MCP Client and Proxy - Generic MCP Client for communicating with any MCP Server via HTTP proxy"""
    
    def __init__(self, server_config: Dict[str, Any], proxy_url: str = "http://127.0.0.1:8080", use_proxychains: bool = True, bypass_ssl: bool = True):
        """
        Initialize the Appsecco MCP Client and Proxy
        
        Args:
            server_config: Server configuration from mcp_config.json
            proxy_url: HTTP proxy URL for Burp inspection
            use_proxychains: Whether to use proxychains for the MCP server process
            bypass_ssl: Whether to bypass SSL certificate verification
        """
        self.server_config = server_config
        self.command = server_config.get("command", "")
        self.args = server_config.get("args", [])
        self.process = None
        self.request_id = 1
        self.tools = {}
        self.initialized = False
        self.proxy_url = proxy_url
        self.base_url = "http://localhost:3000"  # Local HTTP endpoint
        self.use_burp_proxy = True  # Whether to route through Burp proxy
        self.use_proxychains = use_proxychains
        self.bypass_ssl = bypass_ssl
        
    def _check_proxychains_installed(self) -> bool:
        """Check if proxychains is installed on the system"""
        try:
            result = subprocess.run(['which', 'proxychains'], 
                                  capture_output=True, text=True, check=False)
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_proxychains_config(self) -> bool:
        """Check if proxychains.conf exists in the current directory"""
        return os.path.exists('proxychains.conf')
    
    def _verify_proxychains_config(self) -> bool:
        """Verify that proxychains.conf is configured for Burp port 8080"""
        try:
            with open('proxychains.conf', 'r') as f:
                content = f.read()
                # Check if port 8080 is configured
                if '8080' in content:
                    print("✅ proxychains.conf configured for Burp port 8080")
                    return True
                else:
                    print("⚠️  proxychains.conf may not be configured for Burp port 8080")
                    print("   Expected: http 127.0.0.1 8080 in [ProxyList] section")
                    return False
        except Exception as e:
            print(f"❌ Error reading proxychains.conf: {e}")
            return False
    
    def start_server(self) -> bool:
        """Start the MCP server process"""
        try:
            # Check proxychains if enabled
            if self.use_proxychains:
                if not self._check_proxychains_installed():
                    print("❌ proxychains is not installed. Please install it first.")
                    print("   On Ubuntu/Debian: sudo apt-get install proxychains")
                    print("   On CentOS/RHEL: sudo yum install proxychains")
                    print("   On macOS: brew install proxychains-ng")
                    return False
                
                if not self._check_proxychains_config():
                    print("❌ proxychains.conf not found in current directory")
                    print("   Please create a proxychains.conf file or disable proxychains usage")
                    return False
                
                # Verify proxychains configuration
                self._verify_proxychains_config()
                

                cmd = ['proxychains', self.command] + self.args
            else:
                cmd = [self.command] + self.args
            
            # Set environment variables to bypass SSL certificate verification
            # This is needed when using proxychains with Burp for HTTPS requests
            env = os.environ.copy()
            
            # Add environment variables from server configuration if present
            config_env = self.server_config.get("env", {})
            if config_env:
                print(f"🔧 Loading environment variables from config: {list(config_env.keys())}")
                env.update(config_env)
            
            if self.bypass_ssl:
                # SSL bypass variables (these will override config env vars if there are conflicts)
                ssl_bypass_vars = {
                    'NODE_TLS_REJECT_UNAUTHORIZED': '0',  # Node.js SSL bypass
                    'PYTHONHTTPSVERIFY': '0',  # Python SSL bypass
                    'REQUESTS_CA_BUNDLE': '',  # Requests library SSL bypass
                    'SSL_CERT_FILE': '',  # OpenSSL SSL bypass
                    'CURL_CA_BUNDLE': '',  # cURL SSL bypass
                }
                env.update(ssl_bypass_vars)
                       
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )

            print(f"✅ MCP server command to start: {cmd}")
            
            # Wait for the server to start and detect readiness
            if not self._wait_for_server_start():
                return False
            

            return True
                
        except Exception as e:
            print(f"❌ Error starting MCP server: {e}")
            return False
    
    def _check_output_for_indicators(self, output: str, stream_name: str = "output") -> Optional[bool]:
        """
        Check output for success or error indicators
        
        Args:
            output: The output string to check
            stream_name: Name of the stream (e.g., "stderr", "stdout") for logging
            
        Returns:
            True if success indicator found, False if error indicator found, None if neither
        """
        output_lower = output.lower()
        
        # Check for npx-specific indicators
        if self.command == 'npx' or 'npx' in ' '.join(self.args):
            # Success indicators for npx
            success_indicators = [
                'ready', 'started', 'listening', 'server running', 'server is running', 
                'server is ready', 'server started', 'mcp server', 'initialized', 
                'connected', 'package installed', 'npm', 'node_modules', 'successfully', 
                'running on', 'ready to accept connections', 'mcp server is running',
                'mcp server is ready', 'initialized', 'connected', 'installed'
            ]
            if any(indicator in output_lower for indicator in success_indicators):
                print(f"✅ NPX server appears to be ready (from {stream_name})")
                return True
            
            # Error indicators for npx
            error_indicators = [
                'error', 'failed', 'exception', 'crash', 'exit', 'not found', 
                'command failed', 'npm error', 'error', 'failed', 'exception', 'crash', 'exit', 'not found', 'command failed', 'npm error'
            ]
            if any(error in output_lower for error in error_indicators):
                print(f"❌ NPX server error detected (from {stream_name}): {output}")
                return False
        else:
            # Generic success indicators for other commands
            success_indicators = [
                'ready', 'started', 'listening', 'server running', 'mcp server', 
                'initialized', 'connected', 'installed'
            ]
            if any(indicator in output_lower for indicator in success_indicators):
                print(f"✅ Server appears to be ready (from {stream_name})")
                return True
            
            # Generic error indicators
            error_indicators = ['error', 'failed', 'exception', 'crash', 'exit', 'not found', 'command failed', 'npm error']
            if any(error in output_lower for error in error_indicators):
                print(f"❌ Server error detected (from {stream_name}): {output}")
                return False
        
        return None

    def _wait_for_server_start(self, timeout: int = 20) -> bool:
        """
        Wait for the MCP server to start and detect readiness
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if server started successfully, False otherwise
        """

        
        start_time = time.time()
        last_output = ""
        output_buffer = []
        
        # Set stdout to non-blocking mode
        import select
        
        while time.time() - start_time < timeout:
            # Check if process is still running
            if self.process.poll() is not None:
                # Process has exited
                stdout, stderr = self.process.communicate()
                print(f"❌ MCP server process exited unexpectedly")
                if stdout:
                    print(f"STDOUT: {stdout}")
                if stderr:
                    print(f"STDERR: {stderr}")
                return False
            
            # Try to read any available output without blocking
            try:
                import select
                
                # Check stderr
                if self.process.stderr and select.select([self.process.stderr], [], [], 0.1)[0]:
                    stderr = self.process.stderr.readline()
                    if stderr:
                        stderr = stderr.strip()
                        output_buffer.append(stderr)
                        
                        # Check for indicators in stderr
                        result = self._check_output_for_indicators(stderr, "stderr")
                        if result is not None:
                            return result
                
                # Check stdout
                if self.process.stdout and select.select([self.process.stdout], [], [], 0.1)[0]:
                    stdout = self.process.stdout.readline()
                    if stdout:
                        stdout = stdout.strip()
                        output_buffer.append(stdout)
                        last_output = stdout
                        
                        # Check for indicators in stdout
                        result = self._check_output_for_indicators(stdout, "stdout")
                        if result is not None:
                            return result
            except Exception as e:
                # Non-blocking read failed, continue waiting
                pass

            # Small delay to avoid busy waiting
            time.sleep(0.5)
            
            # Show progress every 10 seconds
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0 and elapsed > 0:
                print(f"⏳ Still waiting... ({elapsed}s elapsed)")
        
        # Timeout reached
        print(f"⏰ Timeout reached after {timeout} seconds")
        
        # Check if process is still running (it might be ready but not outputting)
        if self.process.poll() is None:
            print("⚠️  Process is still running but no ready indicator detected")
            print("   Proceeding anyway - server may be ready")
            return True
        else:
            print("❌ Process has exited during startup")
            return False
    
    def stop_server(self):
        """Stop the MCP server process"""
        if self.process:
                    self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
        self.process = None
    
    def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a JSON-RPC request to the MCP server via HTTP proxy
        
        Args:
            method: The RPC method to call
            params: Parameters for the method
            
        Returns:
            Response from the server
        """

        if method == "notifications/initialized":
            request = {
                "jsonrpc": "2.0",
                "method": method
            }
        else:   
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": method
            }

            self.request_id += 1

        if params:
            request["params"] = params
        
        
        try:
            if method == "notifications/initialized":
                timeout = 5
            else:
                timeout = 30
            if self.use_burp_proxy:
                # Route through Burp proxy for inspection
                proxies = {
                    "http": self.proxy_url,
                    "https": self.proxy_url
                }
                response = requests.post(
                    f"{self.base_url}/mcp",
                    json=request,
                    proxies=proxies,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )
            else:
                # Direct connection to local http server
                response = requests.post(
                    f"{self.base_url}/mcp",
                    json=request,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )
            
            if response.status_code != 200:
                raise RuntimeError(f"HTTP request failed with status {response.status_code}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            # Fallback to direct stdio if HTTP fails
            print(f"⚠️  HTTP request failed, falling back to stdio: {e}")
            return self._send_stdio_request(method, params)
        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            print(f"❌ JSON parsing error: {e}")
            return self._send_stdio_request(method, params)
        except Exception as e:
            # Catch any other unexpected errors
            print(f"❌ Unexpected error in send_request: {e}")
            return self._send_stdio_request(method, params)
    
    def _send_stdio_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fallback method: Send request directly via stdio
        
        Args:
            method: The RPC method to call
            params: Parameters for the method
            
        Returns:
            Response from the server
        """
        if not self.process:
            raise RuntimeError("MCP server not started")
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        if params:
            request["params"] = params
        
        self.request_id += 1
        
        # Send request
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str)
        self.process.stdin.flush()
        
        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")
        
        try:
            return json.loads(response_line)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {e}")
    
    def initialize(self) -> bool:
        """Initialize the MCP connection"""
        try:
            init_params = {
                "protocolVersion": "2025-06-18",
                "clientInfo": {
                    "name": "appsecco-mcp-client",
                    "version": "1.0.0"
                },
                "capabilities": {}
            }
            
            response = self.send_request("initialize", init_params)
            
            
            if "result" in response:
                self.initialized = True
                print(f"✅ MCP Initialize done")
        
                return True
            else:
                print(f"❌ Initialization failed: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            return False
        
    def initialized_notification(self) -> bool:
        """Send initialized notification to the MCP server"""
        try:
            
            response = self.send_request("notifications/initialized", {})
            print(f"✅ Initialized notification sent to the MCP server. No response is expected.")
            print(f"✅ Fetching available tools next...")
            return True
        except Exception as e:
            print(f"❌ Error sending initialized notification: {e}")
            return False
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        try:
            response = self.send_request("tools/list", {})
            
            if "result" in response and "tools" in response["result"]:
                tools = response["result"]["tools"]
                self.tools = {tool["name"]: tool for tool in tools}
                return tools
            else:
                print(f"❌ Failed to get tools: {response}")
                return []
                
        except Exception as e:
            print(f"❌ Error listing tools: {e}")
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            Tool response
        """
        try:
            params = {
                "name": tool_name,
                "arguments": arguments
            }
            
            response = self.send_request("tools/call", params)
            
            if "result" in response:
                return response["result"]
            else:
                print(f"❌ Tool call failed: {response}")
                return {}
                
        except Exception as e:
            print(f"❌ Error calling tool: {e}")
            return {}


class GenericMCPApp:
    """Appsecco MCP Client PST - Professional Security Testing Application with interactive interface"""
    
    def __init__(self, config_file: str = "mcp_config.json", proxy_url: str = "http://127.0.0.1:8080", use_burp_proxy: bool = True, use_proxychains: bool = True, bypass_ssl: bool = True):
        """
        Initialize the Appsecco MCP Client PST application
        
        Args:
            config_file: Path to the MCP configuration file
            proxy_url: HTTP proxy URL for Burp inspection
            use_burp_proxy: Whether to route through Burp proxy
            use_proxychains: Whether to use proxychains for MCP server processes
            bypass_ssl: Whether to bypass SSL certificate verification
        """
        self.config = MCPConfig(config_file)
        self.client = None
        self.current_server = None
        self.proxy_url = proxy_url
        self.use_burp_proxy = use_burp_proxy
        self.use_proxychains = use_proxychains
        self.bypass_ssl = bypass_ssl
        self.proxy_server = None
        self.proxy_thread = None
    
    def select_server(self) -> bool:
        """Let user select an MCP server"""
        servers = self.config.list_servers()
        
        if not servers:
            print("❌ No MCP servers configured")
            return False
        
        print("\n📋 Available MCP servers:")
        for i, server_name in enumerate(servers, 1):
            print(f"   {i}. {server_name}")
        
        while True:
            try:
                choice = input(f"\nSelect server (1-{len(servers)}): ").strip()
                server_index = int(choice) - 1
                
                if 0 <= server_index < len(servers):
                    server_name = servers[server_index]
                    server_config = self.config.get_server_config(server_name)
                    
                    if server_config:
                        self.current_server = server_name
                        self.client = MCPClient(server_config, self.proxy_url, self.use_proxychains, self.bypass_ssl)
                        # Set Burp proxy setting
                        self.client.use_burp_proxy = self.use_burp_proxy
                        print(f"✅ Appsecco MCP Client PST - Selected server: {server_name}")
                        return True
                    else:
                        print(f"❌ Invalid configuration for server: {server_name}")
                        return False
                else:
                    print(f"❌ Please enter a number between 1 and {len(servers)}")
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return False
    
    def start_server(self, start_proxy: bool = False, proxy_port: int = 3000) -> bool:
        """Start the selected MCP server"""
        if not self.client:
            print("❌ No server selected")
            return False
        
        print(f"🚀 Appsecco MCP Client PST - Starting server: {self.current_server}")
        if not self.client.start_server():
            return False
        
        # Start proxy server first if requested
        if start_proxy and self.client.process:
            self._start_proxy_server(proxy_port)
            
            # Test proxy server connectivity
            # self._test_proxy_connectivity(proxy_port)
            
            # Give proxy server a moment to start
            import time
            time.sleep(1)
        else:
            print(f"⚠️  Proxy server not enabled")
        
        if not self.client.initialize():
            self.client.stop_server()
            return False
        
        self.client.initialized_notification()

        return True
    
    
    def _start_proxy_server(self, port: int = 3000):
        """Start the HTTP proxy server in a separate thread"""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        import socket
        
        print(f"🔧 Starting HTTP proxy server on port {port}...")
        
        # Check if port is already in use
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex(('localhost', port))
            test_socket.close()
            
            if result == 0:
                print(f"⚠️  Port {port} is already in use!")
                print(f"   This might prevent the proxy server from starting")
                print(f"   You can check what's using the port with: lsof -i :{port}")
                print(f"   Or kill the process with: sudo kill -9 $(lsof -t -i:{port})")
            else:
                print(f"✅ Port {port} is available")
        except Exception as e:
            print(f"⚠️  Could not check port availability: {e}")
        
        # Store the MCP process reference
        mcp_process = self.client.process
        
        # Create a closure to capture mcp_process
        def create_handler_class(mcp_process_ref):
            class MCPProxyHandler(BaseHTTPRequestHandler):
                def do_POST(self):
                    if self.path == '/mcp':
                        try:
                            content_length = int(self.headers['Content-Length'])
                            post_data = self.rfile.read(content_length)
                            
                            request = json.loads(post_data.decode('utf-8'))
                            
                            response = self.forward_to_mcp(request)
                            
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                            self.end_headers()
                            
                            response_json = json.dumps(response)
                            self.wfile.write(response_json.encode('utf-8'))
                            
                        except Exception as e:
                            print(f"❌ Proxy error: {e}")
                            import traceback
                            traceback.print_exc()
                            self.send_response(500)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            error_response = {"error": str(e), "type": "proxy_error"}
                            self.wfile.write(json.dumps(error_response).encode('utf-8'))
                    else:
                        print(f"❌ Proxy received request to unknown path: {self.path}")
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": f"Path {self.path} not found"}).encode('utf-8'))
                
                def do_OPTIONS(self):
                    """Handle CORS preflight requests"""
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                
                def forward_to_mcp(self, request):
                    """Forward request to MCP stdio server"""
                    if not mcp_process_ref:
                        return {"error": "MCP server not available"}
                    
                    if mcp_process_ref.poll() is not None:
                        return {"error": "MCP server process has exited"}
                    
                    try:
                        # Send request to MCP server via stdio

                        request_str = json.dumps(request) + "\n"

                        # print(f"✅ Sending request to MCP server via stdio: {request_str}")
                        mcp_process_ref.stdin.write(request_str)
                        mcp_process_ref.stdin.flush()
                        
                        if request["method"] == "notifications/initialized":
                            response = {"result": "initialized"}
                        else:
                        # Read response
                            response_line = mcp_process_ref.stdout.readline()
                            if not response_line:
                                return {"error": "No response from MCP server"}
                            
                            response = json.loads(response_line.strip())
                        return response
                        
                    except Exception as e:
                        print(f"❌ MCP communication error: {e}")
                        import traceback
                        traceback.print_exc()
                        return {"error": f"Communication error: {str(e)}"}
                
                def log_message(self, format, *args):
                    # Suppress HTTP server logs
                    pass
            
            return MCPProxyHandler
        
        MCPProxyHandler = create_handler_class(mcp_process)
        
        try:
            self.proxy_server = HTTPServer(('localhost', port), MCPProxyHandler)
            
            # Start proxy server in a separate thread
            self.proxy_thread = threading.Thread(
                target=self.proxy_server.serve_forever,
                daemon=True,
                name="MCPProxyThread"
            )
            self.proxy_thread.start()
            
            # Give it a moment to bind
            import time
            time.sleep(1)
            
            # Verify the server is actually listening
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(2)
                result = test_socket.connect_ex(('localhost', port))
                test_socket.close()
                
                if result != 0:
                    print(f"⚠️  HTTP proxy server may not be listening on port {port}")
            except Exception:
                pass
            
        except Exception as e:
            print(f"❌ Failed to start HTTP proxy server: {e}")
    
    def stop_proxy_server(self):
        """Stop the HTTP proxy server"""
        if self.proxy_server:
            self.proxy_server.shutdown()
            self.proxy_server = None
            self.proxy_thread = None
            print("🛑 HTTP proxy server stopped")
    
    def interactive_mode(self, start_proxy: bool = False, proxy_port: int = 3000):
        """Run interactive mode"""
        # Display Appsecco banner
        print(APPSECCO_BANNER)
        print(APPSECCO_TAGLINE)
        
        print("\n" + "="*80)
        print("🔧 Appsecco MCP Client PST - Professional Security Testing Tool")
        print("="*80)
        print(f"🌐 HTTP requests via Burp: {self.proxy_url}")
        print(f"🔗 Proxychains: {'Yes (port 8080)' if self.use_proxychains else 'No'}")
        print(f"🔓 SSL bypass: {'Yes' if self.bypass_ssl else 'No'}")
        if self.use_proxychains:
            print("   - MCP server traffic routed through Burp port 8080 using Proxychains")
        print("   - Local proxy server routes HTTP requests via Burp port 8080")
        
        if start_proxy:
            print("🚀 Will start HTTP proxy server for Burp inspection")
            print("📡 Configure Burp to intercept traffic to localhost:3000")
        else:
            print("⚠️  HTTP proxy server not enabled")
            print("💡 Use --start-proxy to enable Burp inspection\n")
        
        if not self.select_server():
            return
        
        if not self.start_server(start_proxy, proxy_port):
            print("❌ Failed to start server")
            return
        
        # Display connection status after server is started
        print(f"📡 Local HTTP server: {self.client.base_url if self.client else 'Not connected'}")
        
        try:
            # List available tools
            tools = self.client.list_tools()
            if not tools:
                print("❌ No tools available")
                return
            
            print(f"\n🛠️  Available tools ({len(tools)}):")
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool['name']}: {tool.get('description', 'No description')}")
            
            # Interactive menu
            while True:
                print("\n" + "-"*60)
                print("🔧 Appsecco MCP Client PST - Professional Security Testing")
                print("-"*60)
                print("Choose an option:")
                print("1. 🛠️  Call a tool")
                print("2. 📋 List tools again")
                print("3. 🔄 Switch server")
                print("4. 🚪 Exit")
                print("5. ℹ️  About Appsecco")
                
                choice = input("\nEnter your choice (1-5): ").strip()
                
                if choice == "1":
                    self._call_tool_interactive(tools)
                elif choice == "2":
                    tools = self.client.list_tools()
                    print(f"\n🛠️  Available tools ({len(tools)}):")
                    for i, tool in enumerate(tools, 1):
                        print(f"   {i}. {tool['name']}: {tool.get('description', 'No description')}")
                elif choice == "3":
                    self.client.stop_server()
                    if not self.select_server() or not self.start_server():
                        return
                    tools = self.client.list_tools()
                elif choice == "4":
                    print("\n👋 Goodbye!")
                    break
                elif choice == "5":
                    self._show_about_appsecco()
                else:
                    print("❌ Invalid choice. Please enter 1-5.")
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Interrupted by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            if self.client:
                self.stop_proxy_server()
                self.client.stop_server()
            
            # Display Appsecco footer
            print("\n" + "="*80)
            print("🛡️  Thank you for using Appsecco MCP Client PST!")
            print(f"📋 Version: {APPSECCO_VERSION} - {APPSECCO_BUILD}")
            print(f"©  {APPSECCO_COPYRIGHT}")
            print("🌐 Visit https://appsecco.com for professional security services")
            print("="*80)
    
    def _call_tool_interactive(self, tools: List[Dict[str, Any]]):
        """Interactive tool calling"""
        print(f"\nSelect tool (1-{len(tools)}):")
        for i, tool in enumerate(tools, 1):
            print(f"   {i}. {tool['name']}")
        
        try:
            choice = input(f"Enter tool number (1-{len(tools)}): ").strip()
            tool_index = int(choice) - 1
            
            if 0 <= tool_index < len(tools):
                tool = tools[tool_index]
                self._get_tool_arguments_and_call(tool)
            else:
                print(f"❌ Please enter a number between 1 and {len(tools)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n⏹️  Cancelled")
    
    def _show_about_appsecco(self):
        """Display information about Appsecco"""
        print("\n" + "="*80)
        print("ℹ️  ABOUT APPSECCO - Your Trusted Security Partner")
        print("="*80)
        print("🛡️  Appsecco is a leading cybersecurity company specializing in:")
        print("   • Penetration Testing & Security Assessments")
        print("   • Application Security Testing")
        print("   • Infrastructure Security Audits")
        print("   • Cloud Security Assessments")
        print("   • Red Team Operations")
        print("   • Security Training & Awareness")
        print()
        print("🔍  This MCP Client PST tool is part of our professional security toolkit")
        print("   designed for security researchers, penetration testers, and")
        print("   security professionals who need advanced MCP server integration.")
        print()
        print("🌐  Website: https://appsecco.com")
        print("📧  Email: info@appsecco.com")
        print("📱  LinkedIn: https://linkedin.com/company/appsecco")
        print("🐦  Twitter: @appsecco")
        print()
        print("💼  Professional Services:")
        print("   • Enterprise Security Assessments")
        print("   • Compliance & Regulatory Support")
        print("   • Incident Response & Forensics")
        print("   • Security Architecture Design")
        print("="*80)
    
    def _get_tool_arguments_and_call(self, tool: Dict[str, Any]):
        """Get tool arguments and call the tool"""
        tool_name = tool["name"]
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        
        print(f"\n🔧 Calling tool: {tool_name}")
        print(f"Description: {tool.get('description', 'No description')}")
        
        arguments = {}
        
        # Get required arguments first
        for param_name in required:
            if param_name in properties:
                param_info = properties[param_name]
                description = param_info.get("description", "")
                param_type = param_info.get("type", "string")
                
                print(f"\nRequired parameter: {param_name}")
                if description:
                    print(f"Description: {description}")
                print(f"Type: {param_type}")
                
                value = input(f"Enter value for {param_name}: ").strip()
                if value:
                    arguments[param_name] = value
                else:
                    print(f"❌ {param_name} is required")
                    return
        
        # Get optional arguments
        for param_name, param_info in properties.items():
            if param_name not in required:
                description = param_info.get("description", "")
                param_type = param_info.get("type", "string")
                
                print(f"\nOptional parameter: {param_name}")
                if description:
                    print(f"Description: {description}")
                print(f"Type: {param_type}")
                
                value = input(f"Enter value for {param_name} (or press Enter to skip): ").strip()
                if value:
                    arguments[param_name] = value
        
        # Call the tool
        print(f"\n🚀 Calling {tool_name} with arguments: {json.dumps(arguments, indent=2)}")
        
        try:
            result = self.client.call_tool(tool_name, arguments)
            
            if result:
                print("\n✅ Tool call successful!")
                print("Result (may need additional formatting):")
                print(json.dumps(result, indent=2))
            else:
                print("\n❌ Tool call returned no result")
                
        except Exception as e:
            print(f"\n❌ Error calling tool: {e}")
    

def main():
    """Main entry point for Appsecco MCP Client PST"""
    parser = argparse.ArgumentParser(
        description="Appsecco MCP Client PST - Professional Security Testing Tool with proxychains support",
        epilog="""Example: python app.py --start-proxy


Brought to you by Appsecco - Your Trusted Security Partner""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--config", "-c", default="mcp_config.json", 
                       help="MCP configuration file (default: mcp_config.json)")
    parser.add_argument("--proxy", "-p", default="http://127.0.0.1:8080",
                       help="Burp proxy URL (default: http://127.0.0.1:8080)")
    parser.add_argument("--start-proxy", action="store_true",
                       help="Start HTTP proxy server for Burp inspection")
    parser.add_argument("--proxy-port", type=int, default=3000,
                       help="HTTP proxy server port (default: 3000)")
    parser.add_argument("--no-burp", action="store_true",
                       help="Disable Burp proxy routing")
    parser.add_argument("--no-proxychains", action="store_true",
                       help="Disable proxychains usage")
    parser.add_argument("--no-ssl-bypass", action="store_true",
                       help="Disable SSL certificate bypass (may cause HTTPS errors with proxychains)")
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"❌ Configuration file '{args.config}' not found")
        print("Please create a mcp_config.json file with your MCP server configuration")
        sys.exit(1)
    
    # Determine if we should use Burp proxy and proxychains
    use_burp_proxy = not args.no_burp
    use_proxychains = not args.no_proxychains
    bypass_ssl = not args.no_ssl_bypass
    
    app = GenericMCPApp(args.config, args.proxy, use_burp_proxy, use_proxychains, bypass_ssl)
    
    # Run interactive mode
    app.interactive_mode(args.start_proxy, args.proxy_port)


if __name__ == "__main__":
    main()