// API Configuration for Tensora
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:4000';

export const API_ENDPOINTS = {
  // AI Chat endpoints
  chat: `${API_BASE_URL}/proxy/ai`,
  chatStream: `${API_BASE_URL}/proxy/stream`,
  executeAI: `${API_BASE_URL}/proxy/ai/execute`,
  
  // Conversation management
  conversations: `${API_BASE_URL}/conversations`,
  conversation: `${API_BASE_URL}/conversation`,
  addMessage: `${API_BASE_URL}/add_message`,
  
  // Speech-to-text
  speechToText: `${API_BASE_URL}/speech-to-text`,
  
  // Title generation
  generateTitle: `${API_BASE_URL}/title`,
  
  // Health check
  health: `${API_BASE_URL}/health`,
  
  // MCP proxy
  mcpProxy: `${API_BASE_URL}/proxy`
};

export default API_ENDPOINTS;
