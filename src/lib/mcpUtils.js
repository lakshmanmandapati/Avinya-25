/**
 * MCP (Model Context Protocol) Utility Functions
 * Centralized API communication for the frontend
 */

const API_BASE_URL = 'http://localhost:4000';

/**
 * Make a request to the MCP proxy with error handling
 */
async function makeProxyRequest(endpoint, data, options = {}) {
  const { timeout = 30000, ...fetchOptions } = options;
  
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers
      },
      body: JSON.stringify(data),
      signal: controller.signal,
      ...fetchOptions
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}

/**
 * Analyze prompt with AI (supports both chat and tool modes)
 */
export async function analyzePrompt(prompt, options = {}) {
  const {
    provider = 'gemini',
    mcpUrl,
    serverName = 'Default',
    timeout = 30000
  } = options;
  
  return makeProxyRequest('/proxy/ai', {
    provider,
    prompt,
    mcpUrl,
    serverName
  }, { timeout });
}

/**
 * Execute AI-generated plan
 */
export async function executePlan(actions, options = {}) {
  const {
    mcpUrl,
    serverName = 'Default',
    timeout = 60000 // Longer timeout for execution
  } = options;
  
  return makeProxyRequest('/proxy/ai/execute', {
    actions,
    mcpUrl,
    serverName
  }, { timeout });
}

/**
 * Stream AI response using Server-Sent Events
 */
export async function streamAnalyzePrompt(prompt, options = {}) {
  const {
    provider = 'gemini',
    mcpUrl,
    serverName = 'Default',
    onChunk,
    onComplete,
    onError,
    onStatus
  } = options;
  
  const response = await fetch(`${API_BASE_URL}/proxy/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'ai_analyze',
      provider,
      prompt,
      url: mcpUrl,
      serverName
    })
  });
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const eventData = JSON.parse(line.slice(6));
            
            switch (eventData.type) {
              case 'chunk':
                onChunk?.(eventData.data);
                break;
              case 'complete':
                onComplete?.(eventData.data);
                break;
              case 'error':
                onError?.(eventData.error || 'Streaming error occurred');
                break;
              case 'status':
                onStatus?.(eventData.message);
                break;
            }
          } catch (parseError) {
            console.warn('Failed to parse SSE data:', parseError);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * List available MCP tools
 */
export async function listTools(options = {}) {
  const {
    mcpUrl,
    serverName = 'Default',
    timeout = 10000
  } = options;
  
  return makeProxyRequest('/proxy', {
    action: 'listTools',
    url: mcpUrl,
    serverName
  }, { timeout });
}

/**
 * Call a specific MCP tool
 */
export async function callTool(toolName, args, options = {}) {
  const {
    mcpUrl,
    serverName = 'Default',
    timeout = 30000
  } = options;
  
  return makeProxyRequest('/proxy', {
    action: 'callTool',
    toolName,
    args,
    url: mcpUrl,
    serverName
  }, { timeout });
}

/**
 * Check backend health
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      timeout: 5000
    });
    return response.ok;
  } catch (error) {
    return false;
  }
}

/**
 * Format error messages for display
 */
export function formatError(error) {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error.message) {
    return error.message;
  }
  
  if (error.error) {
    return error.error;
  }
  
  return 'An unexpected error occurred';
}

/**
 * Validate MCP URL format
 */
export function validateMcpUrl(url) {
  if (!url) {
    return { valid: false, error: 'MCP URL is required' };
  }
  
  try {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return { valid: false, error: 'URL must use HTTP or HTTPS protocol' };
    }
    return { valid: true };
  } catch (error) {
    return { valid: false, error: 'Invalid URL format' };
  }
}

/**
 * Parse response mode from backend
 */
export function parseResponseMode(response) {
  if (response.mode === 'chat') {
    return {
      mode: 'chat',
      content: response.response || response.plan,
      isChat: true
    };
  }
  
  return {
    mode: 'tool',
    plan: response.plan,
    actions: response.actions || [],
    confidence: response.confidence,
    isChat: false
  };
}

// Conversation Management API calls
export const conversationAPI = {
  // Get all conversations
  async getConversations() {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch conversations: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching conversations:', error);
      throw error;
    }
  },

  // Get specific conversation by ID
  async getConversation(conversationId) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversation/${conversationId}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`Failed to fetch conversation: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching conversation:', error);
      throw error;
    }
  },

  // Create new conversation
  async createConversation(title = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });
      if (!response.ok) {
        throw new Error(`Failed to create conversation: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error creating conversation:', error);
      throw error;
    }
  },

  // Delete conversation
  async deleteConversation(conversationId) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversation/${conversationId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error(`Failed to delete conversation: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error deleting conversation:', error);
      throw error;
    }
  },

  // Add message to conversation
  async addMessage(conversationId, role, content, type = 'text', metadata = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}/add_message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          role,
          content,
          type,
          metadata,
        }),
      });
      if (!response.ok) {
        throw new Error(`Failed to add message: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error adding message:', error);
      throw error;
    }
  },

  // Update conversation title
  async updateTitle(conversationId, title) {
    try {
      const response = await fetch(`${API_BASE_URL}/conversation/${conversationId}/title`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });
      if (!response.ok) {
        throw new Error(`Failed to update title: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error updating title:', error);
      throw error;
    }
  },

  // Generate title for conversation
  async generateTitle(query, provider = 'gemini', model = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/title`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, provider, model }),
      });
      if (!response.ok) {
        throw new Error(`Failed to generate title: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error generating title:', error);
      throw error;
    }
  },
};

/**
 * Default export with all utilities
 */
export default {
  analyzePrompt,
  executePlan,
  streamAnalyzePrompt,
  listTools,
  callTool,
  checkHealth,
  formatError,
  validateMcpUrl,
  parseResponseMode,
  conversationAPI
};
