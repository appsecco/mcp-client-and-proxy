# Appsecco MCP Client

A Generic MCP Client with proxying capabilities.

1. Allows you to start a local relaying proxy so that you can send your traffic upstream (to Burp for example)
2. Connects to MCP servers defined in `mcp_config.json` and interact with their tools.

## Usage

```bash
usage: app.py [-h] [--config CONFIG] [--proxy PROXY] [--start-proxy] [--proxy-port PROXY_PORT] [--no-burp] [--no-proxychains]
              [--no-ssl-bypass]

Generic MCP Client Application with proxychains support

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        MCP configuration file (default: mcp_config.json)
  --proxy PROXY, -p PROXY
                        Burp proxy URL (default: http://127.0.0.1:8080)
  --start-proxy         Start HTTP proxy server for Burp inspection
  --proxy-port PROXY_PORT
                        HTTP proxy server port (default: 3000)
  --no-burp             Disable Burp proxy routing
  --no-proxychains      Disable proxychains usage
  --no-ssl-bypass       Disable SSL certificate bypass (may cause HTTPS errors with proxychains)

Example: python app.py --start-proxy
```

## Setup and Example Run

1. Create venv - `python3 -m venv venv && source venv/bin/activate`
2. Install requirements - `pip3 install -r requirements.txt`
3. Proxychains is required on the system. Instructions to install will be shown if `proxychains` is not found.
4. Run the app - `python3 app.py --start-proxy`
5. Launch Burp and set it to listen on port 8080 localhost
6. Use the app interactively and see the traffic in Burp, you can then use Burp tools like Repeater and Intruder etc.

## Data Flow with --start-proxy

1. Run the app - `python3 app.py --start-proxy`
2. MCP Server Starts
3. Local Proxy Server Starts on port 3000
4. App sends requests → Burp (port 8080) → Local Proxy (port 3000) → MCP Server (stdio)
5. MCP local server via proxychains and Burp sends and receives data from backend server
6. MCP Server responds → Local Proxy → Burp → App
