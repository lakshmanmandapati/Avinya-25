import React, { useState, useEffect } from 'react';
import API_ENDPOINTS from '../config/api';
import { Trash2, Plus, MessageSquare, Calendar, Settings, LogOut, ChevronLeft, User } from 'lucide-react';

const ConversationSidebar = ({ 
  currentConversationId, 
  onConversationSelect, 
  onNewConversation,
  onToggleCollapse
}) => {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/conversations`);
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (err) {
      console.error('Failed to load conversations:', err);
      setError('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const handleNewConversation = async () => {
    try {
      const response = await fetch(`${API_ENDPOINTS.BASE_URL}/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' })
      });
      const data = await response.json();
      const newConversation = {
        id: data.conversation_id,
        title: data.title,
        created_at: new Date().toISOString(),
        message_count: 0
      };
      setConversations(prev => [newConversation, ...prev]);
      onNewConversation(response.conversation_id);
    } catch (err) {
      console.error('Failed to create conversation:', err);
      setError('Failed to create new conversation');
    }
  };

  const handleDeleteConversation = async (conversationId, e) => {
    e.stopPropagation(); // Prevent conversation selection
    
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    try {
      await fetch(`${API_ENDPOINTS.BASE_URL}/conversations/${conversationId}`, {
        method: 'DELETE'
      });
      setConversations(prev => prev.filter(conv => conv.id !== conversationId));
      
      // If we deleted the current conversation, create a new one
      if (conversationId === currentConversationId) {
        handleNewConversation();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
      setError('Failed to delete conversation');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      {/* Header with History and New Chat */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-gray-900">History</h2>
            <button
              onClick={handleNewConversation}
              className="p-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              title="New Conversation"
            >
              <Plus size={14} />
            </button>
          </div>
          
          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            title="Collapse Sidebar"
          >
            <ChevronLeft size={16} />
          </button>
        </div>
        
        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded-lg">
            {error}
          </div>
        )}
      </div>

      {/* History Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center text-gray-500">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-sm">Loading history...</p>
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <MessageSquare size={48} className="mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No conversation history</p>
            <p className="text-xs text-gray-400 mt-1">Start a new chat to begin</p>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                onClick={() => onConversationSelect(conversation.id)}
                className="cursor-pointer hover:bg-gray-50 p-2 rounded-lg transition-colors"
              >
                <h3 className="text-sm font-medium text-gray-900 mb-1">
                  {conversation.title || 'New Chat'}
                </h3>
                <div className="flex items-center text-xs text-gray-500 space-x-2">
                  <Calendar size={12} />
                  <span>{formatDate(conversation.created_at)}</span>
                  {conversation.message_count > 0 && (
                    <>
                      <span>•</span>
                      <span>{conversation.message_count} messages</span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* User Profile Section */}
      <div className="p-3 border-t border-gray-200">
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
            L
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900">Lakshman</p>
            <p className="text-xs text-gray-500 truncate">lakshman0@gmail.com</p>
          </div>
        </div>
        
        <div className="text-xs text-gray-500 mb-2">
          <p>{conversations.length} conversation{conversations.length !== 1 ? 's' : ''}</p>
        </div>
        
        {/* Settings and Logout buttons */}
        <div className="space-y-1">
          <button className="w-full flex items-center space-x-3 p-2 rounded-md hover:bg-gray-100 text-gray-700 hover:text-gray-900 text-sm transition-colors">
            <Settings size={16} />
            <span>Settings</span>
          </button>
          <button className="w-full flex items-center space-x-3 p-2 rounded-md hover:bg-red-50 text-gray-700 hover:text-red-600 text-sm transition-colors">
            <LogOut size={16} />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConversationSidebar;
