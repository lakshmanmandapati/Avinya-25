import os
import json
import requests
from typing import Optional

class TitleGenerator:
    """Generates concise chat titles using AI providers"""
    
    def __init__(self):
        self.api_keys = {
            "gemini": os.getenv("GEMINI_API_KEY"),
            "openai": os.getenv("OPENAI_API_KEY"),
            "claude": os.getenv("CLAUDE_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY")
        }
        
        self.models = {
            "openai": "gpt-3.5-turbo",
            "gemini": "gemini-2.5-flash",
            "claude": "claude-3-haiku-20240307",
            "groq": "llama3-8b-8192"
        }
    
    def generate_title(self, query: str, provider: str = "gemini", model: str = None) -> Optional[str]:
        """Generate a concise title (max 5 words) for a chat query"""
        
        if not self.api_keys.get(provider):
            # Fallback to gemini if provider key not available
            if provider != "gemini" and self.api_keys.get("gemini"):
                provider = "gemini"
            else:
                return self._generate_fallback_title(query)
        
        if not model:
            model = self.models.get(provider, "gemini-2.5-flash")
        
        system_prompt = """You are a title generator. Create a concise, descriptive title for the given user query.

RULES:
- Maximum 5 words
- Be specific and descriptive
- No quotes or special characters
- Capture the main topic/intent
- Use title case

Examples:
Query: "How do I deploy a Docker container to AWS?"
Title: "Docker AWS Deployment Guide"

Query: "What's the difference between React and Vue?"
Title: "React vs Vue Comparison"

Query: "Send an email to john@example.com about the meeting"
Title: "Email Meeting Notification"

Query: "Create a LinkedIn post about AI trends"
Title: "LinkedIn AI Trends Post"

Generate a title for the following query:"""
        
        try:
            if provider == "gemini":
                return self._generate_gemini_title(system_prompt, query)
            elif provider == "openai":
                return self._generate_openai_title(system_prompt, query)
            elif provider == "claude":
                return self._generate_claude_title(system_prompt, query)
            elif provider == "groq":
                return self._generate_groq_title(system_prompt, query)
            else:
                return self._generate_fallback_title(query)
                
        except Exception as e:
            print(f"Title generation error: {e}")
            return self._generate_fallback_title(query)
    
    def _generate_gemini_title(self, system_prompt: str, query: str) -> str:
        """Generate title using Gemini API"""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={self.api_keys['gemini']}"
        
        headers = {"Content-Type": "application/json"}
        body = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\nQuery: {query}\n\nTitle:"
                }]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 20
            }
        }
        
        try:
            response = requests.post(endpoint, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response structures
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    if len(candidate["content"]["parts"]) > 0:
                        title = candidate["content"]["parts"][0]["text"].strip()
                        return self._clean_title(title)
            
            # Fallback if structure is unexpected
            print(f"Unexpected Gemini response structure: {data}")
            return self._clean_title(query[:30])
            
        except Exception as e:
            print(f"Gemini title generation error: {e}")
            return self._clean_title(query[:30])
    
    def _generate_openai_title(self, system_prompt: str, query: str) -> str:
        """Generate title using OpenAI API"""
        endpoint = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_keys['openai']}"
        }
        body = {
            "model": self.models["openai"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {query}\n\nTitle:"}
            ],
            "temperature": 0.3,
            "max_tokens": 20
        }
        
        response = requests.post(endpoint, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        title = data["choices"][0]["message"]["content"].strip()
        return self._clean_title(title)
    
    def _generate_claude_title(self, system_prompt: str, query: str) -> str:
        """Generate title using Claude API"""
        endpoint = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_keys["claude"],
            "anthropic-version": "2023-06-01"
        }
        body = {
            "model": self.models["claude"],
            "max_tokens": 20,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"Query: {query}\n\nTitle:"}
            ]
        }
        
        response = requests.post(endpoint, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        title = data["content"][0]["text"].strip()
        return self._clean_title(title)
    
    def _generate_groq_title(self, system_prompt: str, query: str) -> str:
        """Generate title using Groq API"""
        endpoint = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_keys['groq']}"
        }
        body = {
            "model": self.models["groq"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {query}\n\nTitle:"}
            ],
            "temperature": 0.3,
            "max_tokens": 20
        }
        
        response = requests.post(endpoint, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        title = data["choices"][0]["message"]["content"].strip()
        return self._clean_title(title)
    
    def _clean_title(self, title: str) -> str:
        """Clean and validate the generated title"""
        # Remove quotes and extra whitespace
        title = title.strip().strip('"').strip("'").strip()
        
        # Remove "Title:" prefix if present
        if title.lower().startswith("title:"):
            title = title[6:].strip()
        
        # Limit to 5 words
        words = title.split()
        if len(words) > 5:
            title = " ".join(words[:5])
        
        # Ensure it's not empty
        if not title:
            return "New Chat"
        
        # Capitalize first letter of each word (title case)
        title = " ".join(word.capitalize() for word in title.split())
        
        return title
    
    def _generate_fallback_title(self, query: str) -> str:
        """Generate a simple fallback title when AI is unavailable"""
        # Extract first few words and clean them
        words = query.strip().split()[:3]
        
        if not words:
            return "New Chat"
        
        # Remove common question words and clean
        stop_words = {"how", "what", "when", "where", "why", "who", "can", "could", "would", "should"}
        filtered_words = [word for word in words if word.lower() not in stop_words]
        
        if not filtered_words:
            filtered_words = words[:2]  # Keep at least some words
        
        # Clean and capitalize
        title = " ".join(filtered_words)
        title = "".join(char for char in title if char.isalnum() or char.isspace())
        title = " ".join(word.capitalize() for word in title.split())
        
        return title or "New Chat"

# Global instance
title_generator = TitleGenerator()
