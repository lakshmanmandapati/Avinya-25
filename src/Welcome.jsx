import React, { useState } from 'react';
import { useAuth } from './contexts/AuthContext';

export default function Welcome({ suggestion, onPromptClick }) {
  const { currentUser } = useAuth();
  
  // Get user's first name from display name or email
  const getUserName = () => {
    if (currentUser?.displayName) {
      return currentUser.displayName.split(' ')[0];
    }
    if (currentUser?.email) {
      return currentUser.email.split('@')[0];
    }
    return 'there';
  };

  const welcomeTexts = [
    `Hi. How can I help you automate?, ${getUserName()}. 💗`,
    `Need to automate? I'm here to help 🚀`,
    `Ready to dive deep into any subject, ${getUserName()}! 🧠`,
    `What's sparking your curiosity today, ${getUserName()}? 🔍`
  ];

  // Pick a random text on component mount (page refresh)
  const [randomText] = useState(() => {
    return welcomeTexts[Math.floor(Math.random() * welcomeTexts.length)];
  });

  // Prompt suggestions with full prompts and display text
  const promptSuggestions = [
    {
      displayText: "Create a file",
      fullPrompt: "Create a file in Google Drive named harsha-now with the text: \"n8n is working\". Schedule a meeting on 19th SEP 2025 about n8n servers from 4pm to 8pm in IST . Send an email via Gmail to @gmail.com about that i have made a working prototype regards Harsha and Post on LinkedIn about \"n8n vs MCP\""
    },
    {
      displayText: "Recent Mails ",
      fullPrompt: "Did i get any Recent Gmails?"
    },
    {
      displayText: "Schedule a Zoom ",
      fullPrompt: "Schedule a Zoom Meeting at 9am to 10am IST 19Sep and also Send Gamil to"
    },
    {
      displayText: "Send a Linkedin Post",
      fullPrompt: "Send a Linkedin Post about the How AI is Ruling the World"
    }
  ];

  const handleSuggestionClick = (fullPrompt) => {
    if (onPromptClick) {
      onPromptClick(fullPrompt);
    }
  };

  return (
    <div className="w-full h-full flex flex-col items-center justify-center text-center animate-fade-in px-4 transition-all duration-300 ease-in-out">
      {/* Personalized welcome message */}
      <div className="max-w-2xl w-full transition-all duration-300 ease-in-out">
        <h1 className="font-medium mb-12 text-gray-800 leading-relaxed transition-all duration-300 ease-in-out" style={{ fontFamily: 'Aptos, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', fontSize: '1.755rem' }}>
          {randomText}
        </h1>
        
        {/* Prompt suggestion buttons */}
        <div className="max-w-4xl mx-auto mb-8">
          {/* First row - 4 buttons */}
          <div className="flex flex-wrap justify-center gap-3 mb-2">
            {promptSuggestions.slice(0, 4).map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion.fullPrompt)}
                className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-gray-900 rounded-full text-sm font-medium transition-all duration-200 ease-in-out border border-gray-200 hover:border-gray-300"
                style={{ fontFamily: 'Aptos, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}
              >
                {suggestion.displayText}
              </button>
            ))}
          </div>
          
          {/* Second row - 4 buttons */}
          <div className="flex flex-wrap justify-center gap-3">
            {promptSuggestions.slice(4, 8).map((suggestion, index) => (
              <button
                key={index + 4}
                onClick={() => handleSuggestionClick(suggestion.fullPrompt)}
                className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-gray-900 rounded-full text-sm font-medium transition-all duration-200 ease-in-out border border-gray-200 hover:border-gray-300"
                style={{ fontFamily: 'Aptos, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}
              >
                {suggestion.displayText}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}