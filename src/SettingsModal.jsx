import React from 'react';

export default function SettingsModal({ 
  isOpen, 
  onClose, 
  url, 
  setUrl, 
  selectedProvider, 
  setSelectedProvider, 
  autoExecute, 
  setAutoExecute,
  useStreaming,
  setUseStreaming 
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Settings</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6 space-y-6">
          {/* MCP Webhook URL */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              MCP Webhook URL
            </label>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://your-mcp-server.com/mcp"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter your MCP server endpoint URL for tool integration
            </p>
          </div>

          {/* AI Provider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Provider
            </label>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="gemini">Gemini (Recommended)</option>
              <option value="openai">OpenAI GPT</option>
              <option value="claude">Claude</option>
              <option value="groq">Groq</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              All requests are currently routed to Gemini for optimal performance
            </p>
          </div>

          {/* Auto Execute Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Auto Execute Plans
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Automatically execute tool plans without confirmation
              </p>
            </div>
            <button
              onClick={() => setAutoExecute(!autoExecute)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                autoExecute ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  autoExecute ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Streaming Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Enable Streaming
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Stream responses in real-time for faster interaction
              </p>
            </div>
            <button
              onClick={() => setUseStreaming(!useStreaming)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                useStreaming ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  useStreaming ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Backend Info */}
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-blue-800 mb-1">MCP Integration</h4>
                <p className="text-xs text-blue-700">
                  This interface supports Cursor-style MCP (Model Context Protocol) integration. 
                  The backend automatically detects whether your input requires chat responses or tool execution.
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}