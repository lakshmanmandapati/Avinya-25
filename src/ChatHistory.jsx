import React, { useState } from 'react';
import { logout } from './firebase/auth.js';
import { useAuth } from './contexts/AuthContext.jsx';

export default function ChatHistory({ chats, activeChatId, setActiveChatId, startNewChat, onSettingsClick, isCollapsed, setIsCollapsed }) {
  const { currentUser } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  return (
    <aside 
      className={`bg-card text-card-foreground flex flex-col transition-all duration-300 ease-in-out ${isCollapsed ? 'w-16' : 'w-64'}`}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
    >
      {isCollapsed ? (
        // Collapsed state - only show hamburger menu button
        <div className="p-4 flex items-center justify-center">
          <button onClick={() => setIsCollapsed(!isCollapsed)} className="p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
             <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
             </svg>
          </button>
        </div>
      ) : (
        // Expanded state - show full sidebar
        <>
          <div className="p-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground" style={{ fontFamily: 'Aptos, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>Tensora AI</h2>
            <button onClick={() => setIsCollapsed(!isCollapsed)} className="p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
               </svg>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            <div className="p-2">
              <button onClick={startNewChat} className="w-full text-left flex items-center gap-3 p-2.5 rounded-lg font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                <span>New chat</span>
              </button>
            </div>
            
            <nav className="mt-2 p-2 space-y-1">
              {Object.entries(chats).reverse().map(([id, chat]) => (
                <div key={id} className={`flex items-center gap-2 p-2.5 rounded-lg transition-colors ${activeChatId === id ? 'bg-accent text-accent-foreground' : 'hover:bg-accent/50 text-muted-foreground hover:text-foreground'}`}>
                  <button 
                    onClick={() => setActiveChatId(id)} 
                    className="flex-1 text-left truncate font-medium"
                    title={chat.title}
                  >
                    {chat.isTemporary && chat.messages.length === 0 ? (
                      <span className="italic opacity-70">New chat</span>
                    ) : (
                      chat.title
                    )}
                  </button>
                  {!chat.isTemporary && chat.messages.length > 0 && (
                    <button className="p-1 rounded hover:bg-accent opacity-60 hover:opacity-100 transition-opacity">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-4-4m4 4v-4m0 4h-4" />
                      </svg>
                    </button>
                  )}
                </div>
              ))}
            </nav>
          </div>

          <div className="p-2">
            {/* User info */}
            {currentUser && (
              <div className="mb-2 p-2 rounded-lg bg-accent/50">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-medium">
                    {currentUser.displayName ? currentUser.displayName.charAt(0).toUpperCase() : currentUser.email.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {currentUser.displayName || currentUser.email}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {currentUser.email}
                    </p>
                  </div>
                </div>
              </div>
            )}

            <button onClick={onSettingsClick} className="w-full text-left flex items-center gap-3 p-2.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground font-medium transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" /></svg>
              <span>Settings</span>
            </button>

            <button onClick={handleLogout} className="w-full mt-1 text-left flex items-center gap-3 p-2.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground font-medium transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 102 0V4a1 1 0 00-1-1zm10.293 9.293a1 1 0 001.414 1.414l3-3a1 1 0 000-1.414l-3-3a1 1 0 10-1.414 1.414L14.586 9H7a1 1 0 100 2h7.586l-1.293 1.293z" clipRule="evenodd" /></svg>
              <span>Logout</span>
            </button>
          </div>
        </>
      )}
    </aside>
  );
}