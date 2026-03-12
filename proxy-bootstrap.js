// Patch legacy http/https modules
const { bootstrap } = require('/Users/aihacker/.nvm/versions/node/v24.12.0/lib/node_modules/global-agent');
bootstrap();

// Patch undici / native fetch (Node.js 18+)
// mcp-remote uses fetch which goes through undici, not the legacy http module
try {
  const { ProxyAgent, setGlobalDispatcher } = require('undici');
  const proxyUrl = process.env.GLOBAL_AGENT_HTTPS_PROXY
    || process.env.HTTPS_PROXY
    || process.env.https_proxy
    || 'http://127.0.0.1:8080';
  setGlobalDispatcher(new ProxyAgent(proxyUrl));
  console.error('[proxy-bootstrap] undici global dispatcher set to', proxyUrl);
} catch (e) {
  console.error('[proxy-bootstrap] failed to patch undici:', e.message);
}
