# Appsecco MCP Client PST

> **Professional Security Testing Tool** - Advanced MCP Server Integration with Enterprise-Grade Proxy & Burp Suite Integration

[![Appsecco](https://img.shields.io/badge/Powered%20by-Appsecco-blue?style=for-the-badge&logo=security)](https://appsecco.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)

---

## 🛡️ About Appsecco

**Appsecco** is a leading cybersecurity company specializing in professional security testing, penetration testing, and security assessments. Our MCP Client PST tool is part of our comprehensive security toolkit designed for security researchers, penetration testers, and security professionals.

### 🌟 Key Features

- **🔍 Advanced MCP Server Integration** - Connect to any MCP server with professional-grade reliability
- **🌐 Enterprise Proxy Support** - Seamless integration with Burp Suite and other security tools
- **🔗 Proxychains Integration** - Professional traffic routing and analysis capabilities
- **🛡️ SSL Bypass Support** - Advanced testing scenarios with certificate handling
- **📊 Interactive Security Testing** - Professional interface for security assessments

---

## 🚀 What This Tool Does

The **Appsecco MCP Client PST** is a professional security testing tool that provides:

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
python3 app.py --config my_config.json --start-proxy

# Disable Burp proxy routing
python3 app.py --no-burp

# Disable proxychains
python3 app.py --no-proxychains
```

### Advanced Options

```bash
usage: app.py [-h] [--config CONFIG] [--proxy PROXY] [--start-proxy] 
              [--proxy-port PROXY_PORT] [--no-burp] [--no-proxychains]
              [--no-ssl-bypass]

Appsecco MCP Client PST - Professional Security Testing Tool with proxychains support

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

Example: python app.py --start-proxy

Brought to you by Appsecco - Your Trusted Security Partner
```

---

## 🔄 Data Flow with --start-proxy

When using the `--start-proxy` flag, the tool creates a professional security testing environment:

```
1. 🚀 Run the app: python3 app.py --start-proxy
2. 🔧 MCP Server Starts (with proxychains if enabled)
3. 🌐 Local Proxy Server Starts on port 3000
4. 📡 App sends requests → Burp (port 8080) → Local Proxy (port 3000) → MCP Server (stdio)
5. 🔗 MCP server via proxychains and Burp sends/receives data from backend server
6. 📤 MCP Server responds → Local Proxy → Burp → App
```

### Burp Suite Configuration

1. Launch Burp Suite and set it to listen on port 8080 (localhost)
2. Configure Burp to intercept traffic to `localhost:3000`
3. Use Burp's professional tools like Repeater, Intruder, and Scanner

---

## 🏢 Professional Services

**Appsecco** provides comprehensive cybersecurity services:

- **🔍 Penetration Testing & Security Assessments**
- **🛡️ Application Security Testing**
- **🏗️ Infrastructure Security Audits**
- **☁️ Cloud Security Assessments**
- **🔴 Red Team Operations**
- **📚 Security Training & Awareness**
- **📋 Compliance & Regulatory Support**
- **🚨 Incident Response & Forensics**
- **🏛️ Security Architecture Design**

---

## 📞 Contact & Support

- **🌐 Website**: [https://appsecco.com](https://appsecco.com)
- **📧 Email**: [info@appsecco.com](mailto:info@appsecco.com)
- **📱 LinkedIn**: [https://linkedin.com/company/appsecco](https://linkedin.com/company/appsecco)
- **🐦 Twitter**: [@appsecco](https://twitter.com/appsecco)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

Built with ❤️ by the **Appsecco Security Team** for the cybersecurity community.

**Appsecco - Your Trusted Security Partner** 🛡️
