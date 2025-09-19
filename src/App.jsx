import React, { useState, useEffect, useRef } from 'react';
// Removed unused component imports - functionality integrated into main App
import { ConversationSidebar } from './components/ConversationSidebar';
import { AuthContext } from './contexts/AuthContext';
import API_ENDPOINTS from './config/api';
// App.css removed - using Tailwind CSS for styling
import { UpgradeBanner } from "./components/ui/upgrade-banner.jsx";
// conversationAPI removed - using direct API calls instead

const promptSuggestions = [
  "What are you working on?",
  "What's on your mind today?",
  "Where should we begin?",
  "What's on the agenda today?",
];

export default function App() {
  const [url, setUrl] = useState("https://mcp.zapier.com/api/mcp/s/NjMwZDhjNDQtZTRkYy00YzY3LWIyNGYtZDZhYmIxNThlMjlmOmIxODkzODYyLWY5ZWMtNGY1MC1hZGQ5LWVjYThlYjhiYzRjNA==/mcp");
  const [userPrompt, setUserPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState("gemini");
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [autoExecute, setAutoExecute] = useState(false);
  const [chats, setChats] = useState({ "1": { title: "New Chat", messages: [], conversationId: null, isTemporary: true } });
  const [activeChatId, setActiveChatId] = useState("1");
  const [suggestion, setSuggestion] = useState("");
  const [useStreaming, setUseStreaming] = useState(false);
  
  // Conversation sidebar state
  const [currentConversationId, setCurrentConversationId] = useState(null);
  
  // Sidebar collapse state
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);

  const messagesEndRef = useRef(null);
  const textAreaRef = useRef(null);
  const messages = chats[activeChatId]?.messages || [];

  useEffect(() => {
    setSuggestion(promptSuggestions[Math.floor(Math.random() * promptSuggestions.length)]);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.style.height = "auto";
      textAreaRef.current.style.height = `${textAreaRef.current.scrollHeight}px`;
    }
  }, [userPrompt]);

  const addMessage = useCallback((message) => {
    setChats(prev => {
        const currentMessages = prev[activeChatId]?.messages || [];
        return {
            ...prev,
            [activeChatId]: {
                ...prev[activeChatId],
                messages: [...currentMessages, message]
            }
        };
    });
  }, [activeChatId]);

  const updateMessage = useCallback((messageId, updates) => {
    setChats(prev => {
      const newChats = { ...prev };
      const currentMessages = newChats[activeChatId]?.messages || [];
      const messageIndex = currentMessages.findIndex(msg => msg.id === messageId);
      if (messageIndex !== -1) {
        currentMessages[messageIndex] = { ...currentMessages[messageIndex], ...updates };
        newChats[activeChatId] = { ...newChats[activeChatId], messages: [...currentMessages] };
      }
      return newChats;
    });
  }, [activeChatId]);

  const handleStarterPromptClick = (prompt) => {
    setUserPrompt(prompt);
    textAreaRef.current?.focus();
  };

  const analyzePromptWithAI = async () => {
    const currentPrompt = userPrompt.trim();
    if (!currentPrompt) return;
    if (!url) {
        addMessage({id: Date.now(), role: 'error', content: 'Please set the MCP Webhook URL in settings.', type: 'text', timestamp: new Date()});
        setIsSettingsOpen(true);
        return;
    }

    setIsLoading(true);
    
    let currentChatId = activeChatId;
    const isNewChat = (chats[currentChatId]?.messages.length || 0) === 0;

    if (isNewChat) {
        const currentChat = chats[currentChatId];
        const newTitle = currentPrompt.substring(0, 30) + (currentPrompt.length > 30 ? '...' : '');
        
        if (currentChat?.isTemporary) {
            // Convert temporary chat to permanent
            setChats(prev => ({
                ...prev,
                [currentChatId]: {
                    ...prev[currentChatId],
                    title: newTitle,
                    isTemporary: false
                }
            }));
        } else {
            // Create new permanent chat
            const newChatId = Date.now().toString();
            setChats(prev => {
                const newChats = { ...prev };
                newChats[newChatId] = { title: newTitle, messages: [], conversationId: null, isTemporary: false };
                if (newChats["1"]?.messages.length === 0) delete newChats["1"];
                return newChats;
            });
            setActiveChatId(newChatId);
            currentChatId = newChatId;
        }
    }

    const userMessage = {id: Date.now(), role: 'user', content: currentPrompt, type: 'text', timestamp: new Date()};
    const thinkingMessage = {id: Date.now() + 1, role: 'assistant', content: 'Analyzing...', type: 'thinking', timestamp: new Date()};

    setChats(prev => ({
        ...prev,
        [currentChatId]: {
            ...prev[currentChatId],
            messages: [...(prev[currentChatId]?.messages || []), userMessage, thinkingMessage]
        }
    }));
    setUserPrompt("");

    try {
      if (useStreaming) {
        await handleStreamingResponse(currentPrompt, currentChatId, thinkingMessage.id);
      } else {
        await handleRegularResponse(currentPrompt, currentChatId, thinkingMessage.id);
      }
    } catch (err) {
        const errorMessage = {id: Date.now(), role: 'error', content: `Failed to analyze prompt: ${err.message}`, type: 'text', timestamp: new Date()};
        setChats(prev => {
            const newChats = { ...prev };
            const updatedMessages = newChats[currentChatId].messages.filter(msg => msg.id !== thinkingMessage.id);
            updatedMessages.push(errorMessage);
            newChats[currentChatId] = { ...newChats[currentChatId], messages: updatedMessages };
            return newChats;
        });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegularResponse = async (prompt, chatId, thinkingMessageId) => {
    // Ensure we have a conversation ID for this chat
    let conversationId = chats[chatId]?.conversationId;
    if (!conversationId) {
      try {
        const response = await fetch(`${API_ENDPOINTS.BASE_URL}/conversations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: chats[chatId]?.title || 'New Chat' })
        });
        const data = await response.json();
        conversationId = data.conversation_id;
        
        // Update the chat with the conversation ID
        setChats(prev => ({
          ...prev,
          [chatId]: {
            ...prev[chatId],
            conversationId: conversationId
          }
        }));
      } catch (err) {
        console.error('Failed to create conversation:', err);
        // Continue without conversation tracking
      }
    }

    const response = await fetch(API_ENDPOINTS.chat, {
      method: "POST", 
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        provider: selectedProvider, 
        prompt: prompt, 
        mcpUrl: url,
        serverName: "Default",
        conversation_id: conversationId // Add conversation tracking
      })
    });
    
    const data = await response.json();
    
    // Update conversation ID if returned from backend
    if (data.conversation_id && data.conversation_id !== conversationId) {
      setChats(prev => ({
        ...prev,
        [chatId]: {
          ...prev[chatId],
          conversationId: data.conversation_id
        }
      }));
    }
    
    let finalMessage;
    if (data.error) {
      finalMessage = {id: Date.now(), role: 'error', content: data.error, type: 'text', timestamp: new Date()};
    } else if (data.mode === "chat") {
      finalMessage = {
        id: Date.now(), 
        role: 'assistant', 
        content: data.response || data.plan, 
        type: 'chat', 
        mode: 'chat',
        timestamp: new Date()
      };
    } else {
      // Tool mode response
      if (autoExecute && data.actions?.length > 0) {
          executePlan(data, chatId, thinkingMessageId);
          return; // Don't create final message yet, executePlan will handle it
      } else {
          finalMessage = {
            id: Date.now(), 
            role: 'assistant', 
            content: formatPlanMessage(data), 
            type: 'plan', 
            mode: 'tool',
            actions: data.actions || [], 
            plan: data.plan,
            confidence: data.confidence,
            timestamp: new Date()
          };
      }
    }

    setChats(prev => {
      const newChats = { ...prev };
      const updatedMessages = newChats[chatId].messages.filter(msg => msg.id !== thinkingMessageId);
      if (finalMessage) {
          updatedMessages.push(finalMessage);
      }
      newChats[chatId] = { ...newChats[chatId], messages: updatedMessages };
      return newChats;
    });
  };

  const handleStreamingResponse = async (prompt, chatId, thinkingMessageId) => {
    // Ensure we have a conversation ID for this chat
    let conversationId = chats[chatId]?.conversationId;
    if (!conversationId) {
      try {
        const response = await fetch(`${API_ENDPOINTS.BASE_URL}/conversations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: chats[chatId]?.title || 'New Chat' })
        });
        const data = await response.json();
        conversationId = data.conversation_id;
        
        // Update the chat with the conversation ID
        setChats(prev => ({
          ...prev,
          [chatId]: {
            ...prev[chatId],
            conversationId: conversationId
          }
        }));
      } catch (err) {
        console.error('Failed to create conversation:', err);
        // Continue without conversation tracking
      }
    }

    const response = await fetch(API_ENDPOINTS.chatStream, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "ai_analyze",
        provider: selectedProvider,
        prompt: prompt,
        url: url,
        serverName: "Default",
        conversation_id: conversationId // Add conversation tracking
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let streamingMessageId = Date.now();
    
    // Create initial streaming message
    const streamingMessage = {
      id: streamingMessageId,
      role: 'assistant',
      content: '',
      type: 'streaming',
      timestamp: new Date()
    };

    // Replace thinking message with streaming message
    setChats(prev => {
      const newChats = { ...prev };
      const updatedMessages = newChats[chatId].messages.filter(msg => msg.id !== thinkingMessageId);
      updatedMessages.push(streamingMessage);
      newChats[chatId] = { ...newChats[chatId], messages: updatedMessages };
      return newChats;
    });

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
              
              if (eventData.type === 'chunk' && eventData.data) {
                // Update streaming message content
                updateMessage(streamingMessageId, {
                  content: (streamingMessage.content || '') + (eventData.data.content || eventData.data.text || ''),
                  type: 'streaming'
                });
              } else if (eventData.type === 'complete') {
                // Final response received
                const finalData = eventData.data;
                let finalMessage;
                
                if (finalData.mode === "chat") {
                  finalMessage = {
                    id: streamingMessageId,
                    role: 'assistant',
                    content: finalData.response || finalData.plan,
                    type: 'chat',
                    mode: 'chat',
                    timestamp: new Date()
                  };
                } else {
                  finalMessage = {
                    id: streamingMessageId,
                    role: 'assistant',
                    content: formatPlanMessage(finalData),
                    type: 'plan',
                    mode: 'tool',
                    actions: finalData.actions || [],
                    plan: finalData.plan,
                    confidence: finalData.confidence,
                    timestamp: new Date()
                  };
                }
                
                updateMessage(streamingMessageId, finalMessage);
              } else if (eventData.type === 'error') {
                updateMessage(streamingMessageId, {
                  role: 'error',
                  content: eventData.error || 'Streaming error occurred',
                  type: 'text'
                });
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
  };

  const executePlan = async (plan, chatId = activeChatId, thinkingMessageId = null) => {
    if (!plan.actions?.length) {
        addMessage({id: Date.now(), role: 'error', content: 'No actions to execute.', type: 'text', timestamp: new Date()});
        return;
    }
    
    const executingMessage = {id: Date.now(), role: 'assistant', content: 'Executing plan...', type: 'executing', timestamp: new Date()};
    
    if (thinkingMessageId) {
      // Replace thinking message with executing message
      setChats(prev => {
        const newChats = { ...prev };
        const updatedMessages = newChats[chatId].messages.filter(msg => msg.id !== thinkingMessageId);
        updatedMessages.push(executingMessage);
        newChats[chatId] = { ...newChats[chatId], messages: updatedMessages };
        return newChats;
      });
    } else {
      addMessage(executingMessage);
    }

    try {
      const conversationId = chats[chatId]?.conversationId;
      const response = await fetch(API_ENDPOINTS.executeAI, {
        method: "POST", 
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          actions: plan.actions, 
          mcpUrl: url,
          serverName: "Default",
          conversation_id: conversationId // Add conversation tracking
        })
      });
      const data = await response.json();
      
      let resultMessageContent;
      if (data.error) {
        resultMessageContent = `**Execution Failed:**\n\n${data.error}`;
      } else if (data.results) {
        resultMessageContent = formatExecutionResults(data.results, plan);
      } else {
        resultMessageContent = "**Execution completed** but no detailed results were returned.";
      }
      
      const resultMessage = {
        id: Date.now(), 
        role: 'assistant', 
        content: resultMessageContent, 
        type: 'execution_result',
        mode: 'tool',
        executionData: data,
        timestamp: new Date()
      };

      setChats(prev => {
        const newChats = { ...prev };
        const updatedMessages = newChats[chatId].messages.filter(msg => msg.id !== executingMessage.id);
        updatedMessages.push(resultMessage);
        newChats[chatId] = { ...newChats[chatId], messages: updatedMessages };
        return newChats;
      });

    } catch (err) {
        const errorMessage = {
          id: Date.now(), 
          role: 'error', 
          content: `Failed to execute plan: ${err.message}`, 
          type: 'text', 
          timestamp: new Date()
        };
        setChats(prev => {
            const newChats = { ...prev };
            const updatedMessages = newChats[chatId].messages.filter(msg => msg.id !== executingMessage.id);
            updatedMessages.push(errorMessage);
            newChats[chatId] = { ...newChats[chatId], messages: updatedMessages };
            return newChats;
        });
    }
  };

  const formatPlanMessage = (plan) => {
    let message = `**Plan:** ${plan.plan || 'AI generated plan'}\n\n`;
    if (plan.confidence) {
      message += `**Confidence:** ${plan.confidence}%\n\n`;
    }
    if (plan.actions?.length > 0) {
      message += "**Proposed Actions:**\n" + plan.actions.map((act, i) => 
        `\n**${i + 1}. ${act.tool}**\n   - **Reasoning:** ${act.reasoning || 'No reasoning provided'}\n   - **Parameters:** \`${JSON.stringify(act.parameters || {})}\``
      ).join('');
      message += "\n\nShall I proceed with execution?";
    } else {
      message += "\n*No specific actions required for this request.*";
    }
    return message;
  };

  const formatExecutionResults = (results, originalPlan) => {
    let message = `**Execution Results:**\n\n`;
    if (originalPlan?.plan) {
      message += `**Original Plan:** ${originalPlan.plan}\n\n`;
    }
    
    message += results.map((res, i) => {
      let resultText = `**${i + 1}. ${res.action}** - ${res.success ? "✅ Success" : "❌ Failed"}\n`;
      
      if (res.success && res.result) {
        if (typeof res.result === 'object') {
          // Handle structured results
          if (res.result.output) {
            resultText += `   - **Output:** ${JSON.stringify(res.result.output, null, 2)}\n`;
          } else {
            resultText += `   - **Result:** ${JSON.stringify(res.result, null, 2)}\n`;
          }
        } else {
          resultText += `   - **Result:** ${res.result}\n`;
        }
      }
      
      if (res.error) {
        resultText += `   - **Error:** ${res.error}\n`;
      }
      
      return resultText;
    }).join('\n');
    
    return message;
  };

  const startNewChat = () => {
    const newChatId = Date.now().toString();
    setChats(prev => {
      const newChats = { ...prev };
      
      // Remove any existing empty temporary chats
      Object.keys(newChats).forEach(id => {
        const chat = newChats[id];
        if (chat.isTemporary && chat.messages.length === 0) {
          delete newChats[id];
        }
      });
      
      // Add new temporary chat
      newChats[newChatId] = { title: "New Chat", messages: [], conversationId: null, isTemporary: true };
      return newChats;
    });
    setActiveChatId(newChatId);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      analyzePromptWithAI();
    }
  };

  const onConfirmExecution = (messageId, actions) => {
    if (!actions) return;
    setChats(prev => {
      const newChats = { ...prev };
      const currentMessages = newChats[activeChatId]?.messages || [];
      newChats[activeChatId] = { ...newChats[activeChatId], messages: currentMessages.filter(msg => msg.id !== messageId) };
      return newChats;
    });
    executePlan({ actions });
  };

  const onCancelExecution = (messageId) => {
    setChats(prev => {
      const newChats = { ...prev };
      const currentMessages = newChats[activeChatId]?.messages || [];
      newChats[activeChatId] = { ...newChats[activeChatId], messages: currentMessages.filter(msg => msg.id !== messageId) };
      return newChats;
    });
    addMessage({id: Date.now(), role: 'assistant', content: 'Execution cancelled. How else can I help you?', type: 'text', timestamp: new Date()});
  };

  const handleEditMessage = (messageId, content) => {
    setUserPrompt(content);
    // Focus on the input field
    const inputElement = document.querySelector('textarea');
    if (inputElement) {
      inputElement.focus();
    }
  };

  const hasStartedChat = messages.length > 0;

  return (
    <div className="antialiased bg-white flex h-screen overflow-hidden" style={{ fontFamily: 'Aptos, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      <ChatHistory chats={chats} activeChatId={activeChatId} setActiveChatId={setActiveChatId} startNewChat={startNewChat} onSettingsClick={() => setIsSettingsOpen(true)} isCollapsed={isSidebarCollapsed} setIsCollapsed={setIsSidebarCollapsed} />
      <div className={`flex-1 flex flex-col h-screen relative bg-white transition-all duration-300 ease-in-out ${isSidebarCollapsed ? 'ml-0' : 'ml-0'}`}>
        <main className={`flex-1 overflow-y-auto transition-all duration-500 ease-in-out ${!hasStartedChat ? 'flex items-center justify-center' : 'pt-6 pb-6'}`}>
          {!hasStartedChat ? (
            <div className="animate-fade-in transition-all duration-500 ease-in-out">
              <Welcome suggestion={suggestion} onPromptClick={handleStarterPromptClick} />
            </div>
          ) : (
            <div className="w-full max-w-4xl mx-auto px-6 space-y-0 overflow-hidden animate-slide-in-up transition-all duration-500 ease-in-out opacity-0 animate-fade-in-delayed">
              {messages.map((message, index) => (
                <MemoizedChatMessage key={message.id} message={message} onConfirm={onConfirmExecution} onCancel={onCancelExecution} onEdit={handleEditMessage} style={{ '--animation-delay': `${index * 100}ms` }} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </main>
        <footer className={`p-4 w-full bg-white transition-all duration-500 ease-in-out ${!hasStartedChat ? `fixed bottom-32 ${isSidebarCollapsed ? 'left-16' : 'left-64'} right-0 max-w-4xl mx-auto` : ''}`}>
          <div className="max-w-4xl mx-auto transition-all duration-300 ease-in-out">
            <CustomPromptInput
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              onSubmit={analyzePromptWithAI}
              placeholder="Ask me Tensora AI..."
              disabled={isLoading}
              selectedProvider={selectedProvider}
              onProviderChange={setSelectedProvider}
              className="shadow-sm border-gray-300 focus-within:ring-1 focus-within:ring-gray-400 focus-within:border-gray-400 rounded-xl"
            />
          </div>
        </footer>
        
        {/* Upgrade Banner at the bottom */}
        {!hasStartedChat && (
          <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
            <UpgradeBanner 
              buttonText="Developing Tensora Own Modal"
              description="for unlimited AI conversations and premium features"
              onClose={() => {/* Handle close if needed */}}
              onClick={() => {/* Handle upgrade click */}}
            />
          </div>
        )}
      </div>
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
        url={url} 
        setUrl={setUrl} 
        selectedProvider={selectedProvider} 
        setSelectedProvider={setSelectedProvider} 
        autoExecute={autoExecute} 
        setAutoExecute={setAutoExecute}
        useStreaming={useStreaming}
        setUseStreaming={setUseStreaming}
      />
    </div>
  );
}