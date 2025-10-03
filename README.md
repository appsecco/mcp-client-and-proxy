# Appsecco MCP Client and Proxy

> **Semi Professional Security Tool with Cool Vibes** -  Send MCP Server Traffic to your Burp Suite

[![Appsecco](https://img.shields.io/badge/Powered%20by-Appsecco-blue?style=for-the-badge&logo=security)](https://appsecco.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)

---

## 🌟 Key Features

- **🔍 Advanced MCP Server Integration** - Connect to any MCP server with professional-grade reliability
- **🌐 Enterprise Proxy Support** - Seamless integration with Burp Suite and other security tools
- **🔗 Proxychains Integration** - Professional traffic routing and analysis capabilities
- **🛡️ SSL Bypass Support** - Advanced testing scenarios with certificate handling
- **📊 Interactive Security Testing** - Professional interface for security assessments

---

## 🚀 What This Tool Does

The **Appsecco MCP Client and Proxy** is a professional security testing tool that provides:

1. **Local Relaying Proxy** - Start a local proxy server to route traffic through Burp Suite or other security tools
2. **MCP Server Integration** - Connect to MCP servers defined in `mcp_config.json` and interact with their tools
3. **Professional Traffic Analysis** - Route all traffic through configurable proxies for security testing
4. **Enterprise-Grade Reliability** - Built for professional security teams and penetration testers

---

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.7+
- Proxychains (for advanced proxy routing)
- Burp Suite (recommended for traffic analysis)

### Quick Start

```bash
# 1. Create virtual environment
python3 -m venv venv && source venv/bin/activate

# 2. Install requirements
pip3 install -r requirements.txt

# 3. Run the professional security testing tool
python3 app.py --start-proxy
```

### Proxychains Installation

The tool will automatically detect if `proxychains` is installed and provide installation instructions if needed:

- **Ubuntu/Debian**: `sudo apt-get install proxychains`
- **CentOS/RHEL**: `sudo yum install proxychains`
- **macOS**: `brew install proxychains-ng`

---

## 📖 Usage

### Basic Usage

```bash
# Start with HTTP proxy server for Burp inspection
python3 app.py --start-proxy

# Use custom configuration file
python3 app.py --config my_mcp_config.json --start-proxy

# Disable Burp proxy routing
python3 app.py --no-burp

# Disable proxychains
python3 app.py --no-proxychains
```

### Advanced Options

```bash
usage: python3 app.py [-h] [--config CONFIG] [--proxy PROXY] [--start-proxy] 
              [--proxy-port PROXY_PORT] [--no-burp] [--no-proxychains]
              [--no-ssl-bypass]

Appsecco MCP Client and Proxy - Professional Security Testing Tool with proxychains support

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
  --no-ssl-bypass       Disable SSL certificate bypass

Example: python3 app.py --start-proxy

Brought to you by Appsecco - Product Security Experts
```

---

## 🔄 Data Flow with --start-proxy

When using the `--start-proxy` flag, the tool creates a professional security testing environment:

```
1. 🚀 Run the app: python3 app.py --start-proxy
2. 🔧 MCP Server Starts with proxychains
3. 🌐 Local Proxy Server Starts on port 3000
4. 📡 App sends requests -> Local Proxy (port 3000) -> Burp (port 8080) -> MCP Server (stdio)
5. 🔗 MCP server via proxychains and Burp sends/receives data from backend server
6. 📤 MCP Server responds -> Local Proxy -> Burp -> App
```

### Burp Suite Configuration

1. Launch Burp Suite and set it to listen on port 8080 (localhost)
2. Configure Burp to intercept traffic as usual. This traffic will be travelling to `localhost:3000` and backend APIs
3. Use Burp's professional tools like Repeater, Intruder, and Scanner

## 📊 Analytics

This tool includes anonymous usage analytics for Appsecco to obtain usage metrics 

**What we track**: startup arguments, tool start and end, count of MCP servers, error rates and basic system info (OS, Python version)
**What we DON'T track**: Personal data, URLs, testing targets, traffic, credentials  
**Opt-out**: Use `--no-analytics` flag or set `MCP_ANALYTICS_DISABLED=true`

You can use `export MCP_ANALYTICS_DEBUG=true` to see what analytics data is shared.
---

## Why did we build this universal MCP client

[![Watch the video](https://imgs.kloudle.com/apsc-public/why-did-we-build-universal-mcp-client.png)](https://youtu.be/A3DpnyEfC4M)


## 🛡️ About Appsecco - Let Us Hack Your Product Like Attackers Do 🛡️

**Appsecco** is a leading cybersecurity company specializing in product security testing, penetration testing, and security assessments. At Appsecco we hack your product and Cloud/K8s infra like hackers do. Real security testing for business-critical applications.

We wrote this MCP Client and Proxy tool when we had to testing the security of MCP server of a Fortune 500 FinTech company. It worked well for our Burp Suite workflow. We felt that there could be others who may need this as well.

## 🏢 Product Security Testing

**Appsecco** provides comprehensive cybersecurity services:

- **🔍 Penetration Testing & Security Assessments for Business-critical Products**
- **🛡️ Application Security Testing**
- **🏗️ Infrastructure Security Audits**
- **☁️ Cloud Security Assessments**

---

## 📞 Contact & Support

While this tool is offered under an open source MIT license, if you are interested in taking a look at our services. Here are the details.

- **🌐 Website**: [https://appsecco.com](https://appsecco.com)
- **📧 Email**: [HackMyProduct@appsecco.com](mailto:hackmyproduct@appsecco.com)
- **📱 LinkedIn**: [https://linkedin.com/company/appsecco](https://linkedin.com/company/appsecco)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with ❤️ by **[Riyaz](https://github.com/riyazwalikar) & [Akash](https://github.com/makash)** for the cybersecurity community.

**Appsecco - Let Us Hack Your Product Like Attackers Do** 🛡️
