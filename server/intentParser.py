import re
import json
from typing import List, Dict, Any, Optional

class IntentParser:
    def __init__(self):
        # Keywords that typically indicate tool usage
        self.tool_keywords = [
            'send', 'email', 'schedule', 'create', 'post', 'share', 'book', 'reserve',
            'add', 'update', 'delete', 'search', 'find', 'get', 'fetch', 'download',
            'upload', 'save', 'export', 'import', 'notify', 'remind', 'calendar',
            'meeting', 'appointment', 'task', 'todo', 'contact', 'message', 'call',
            'linkedin', 'twitter', 'facebook', 'instagram', 'gmail', 'outlook',
            'slack', 'teams', 'zoom', 'drive', 'dropbox', 'notion', 'trello',
            'jira', 'salesforce', 'hubspot', 'zapier'
        ]

        # Chat-only patterns (greetings, questions, reasoning)
        self.chat_patterns = [
            re.compile(r'^(hi|hello|hey|good morning|good afternoon|good evening)', re.IGNORECASE),
            re.compile(r'^(how are you|what\'s up|what can you do)', re.IGNORECASE),
            re.compile(r'^(what is|what are|explain|tell me about|how does)', re.IGNORECASE),
            re.compile(r'^(calculate|solve|what\'s|whats)', re.IGNORECASE),
            re.compile(r'\?$'),  # Questions ending with ?
            re.compile(r'^(thank you|thanks|bye|goodbye)', re.IGNORECASE)
        ]

    def analyze_intent(self, user_input: str, available_tools: List[Dict] = None) -> Dict[str, Any]:
        if available_tools is None:
            available_tools = []
            
        input_text = user_input.strip().lower()

        # Check for explicit chat patterns first
        if self.is_chat_intent(input_text):
            return {
                "mode": "chat",
                "application": None,
                "action": None,
                "parameters": {},
                "reasoning": "Detected conversational/informational request"
            }

        # Check for tool-related keywords and available tools
        tool_match = self.find_tool_match(input_text, available_tools)
        if tool_match:
            return {
                "mode": "tool",
                "application": tool_match["application"],
                "action": tool_match["action"],
                "parameters": tool_match["parameters"],
                "reasoning": f"Detected request for {tool_match['application']} integration"
            }

        # Default to chat mode for ambiguous cases
        return {
            "mode": "chat",
            "application": None,
            "action": None,
            "parameters": {},
            "reasoning": "Ambiguous intent, defaulting to conversational mode"
        }

    def is_chat_intent(self, input_text: str) -> bool:
        # Check explicit chat patterns
        for pattern in self.chat_patterns:
            if pattern.search(input_text):
                return True

        # Check for mathematical expressions
        if re.search(r'[\d\+\-\*\/\(\)=]', input_text) and not re.search(r'send|email|create', input_text):
            return True

        # Check for general knowledge questions
        if 'what is' in input_text or 'who is' in input_text or 'when is' in input_text:
            return True

        return False

    def find_tool_match(self, input_text: str, available_tools: List[Dict]) -> Optional[Dict]:
        # Check for tool keywords
        has_tool_keyword = any(keyword in input_text for keyword in self.tool_keywords)

        if not has_tool_keyword:
            return None

        # Try to match with available tools
        for tool in available_tools:
            tool_name = tool.get("name", "").lower()
            tool_desc = (tool.get("description") or "").lower()

            # Direct tool name match
            if tool_name and tool_name in input_text:
                return {
                    "application": self.extract_application(tool),
                    "action": tool.get("name"),
                    "parameters": self.extract_parameters(input_text, tool)
                }

            # Description-based matching
            if self.matches_tool_description(input_text, tool_desc):
                return {
                    "application": self.extract_application(tool),
                    "action": tool.get("name"),
                    "parameters": self.extract_parameters(input_text, tool)
                }

        # Generic tool intent detected but no specific match
        return {
            "application": "generic",
            "action": "unknown",
            "parameters": {"originalInput": input_text}
        }

    def extract_application(self, tool: Dict) -> str:
        tool_name = tool.get("name", "").lower()

        # Common application mappings
        if 'email' in tool_name or 'gmail' in tool_name:
            return 'gmail'
        if 'calendar' in tool_name:
            return 'calendar'
        if 'linkedin' in tool_name:
            return 'linkedin'
        if 'slack' in tool_name:
            return 'slack'
        if 'drive' in tool_name:
            return 'drive'
        if 'leave' in tool_name or 'vacation' in tool_name:
            return 'leave_manager'

        # Default to first word of tool name
        parts = tool_name.split('_')
        return parts[0] if parts else 'unknown'

    def matches_tool_description(self, input_text: str, description: str) -> bool:
        desc_words = [word for word in description.split() if len(word) > 3]
        return any(word.lower() in input_text for word in desc_words)

    def extract_parameters(self, input_text: str, tool: Dict) -> Dict[str, Any]:
        parameters = {}
        schema = tool.get("inputSchema", {}).get("properties", {})

        # Basic parameter extraction patterns
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        emails = re.findall(email_pattern, input_text)

        if emails and any(key in schema for key in ['to', 'email', 'recipient']):
            parameters['to'] = emails[0]
            parameters['email'] = emails[0]
            parameters['recipient'] = emails[0]

        # Extract quoted content as message/body
        quoted_content = re.search(r'"([^"]+)"', input_text)
        if quoted_content and any(key in schema for key in ['message', 'body', 'content']):
            parameters['message'] = quoted_content.group(1)
            parameters['body'] = quoted_content.group(1)
            parameters['content'] = quoted_content.group(1)

        return parameters

    def get_enhanced_system_prompt(self, tools_info: List[Dict], user_prompt: str, mode: str) -> str:
        if mode == "chat":
            return f"""You are a helpful AI assistant. The user is having a conversation with you.

USER REQUEST: "{user_prompt}"

Respond naturally and conversationally. You can:
- Answer questions
- Explain concepts
- Help with math and calculations
- Provide general information
- Have friendly conversations

Respond directly as a helpful assistant. Do NOT suggest using tools or mention any integrations.

RESPONSE FORMAT: Respond with plain text, no JSON structure needed."""

        tools_info_str = json.dumps(tools_info, indent=2) if tools_info else "[]"
        
        return f"""You are an expert AI assistant that helps users accomplish tasks using available tools.

AVAILABLE TOOLS:
{tools_info_str}

USER REQUEST: "{user_prompt}"

YOUR TASK:
1. Analyze the user's request and break it down into specific actions
2. For each action, select the most appropriate tool
3. Generate detailed, high-quality content for content creation tasks
4. Extract all necessary parameters from the user's request
5. If the request involves multiple steps, create a sequence of actions

RESPONSE FORMAT:

Return a JSON object with this structure:
{{
  "plan": "Brief description of your overall plan",
  "actions": [
    {{
      "tool": "exact_name_of_tool",
      "reasoning": "Why this tool is appropriate",
      "parameters": {{ ... }}  // All required parameters with detailed values
    }}
  ],
  "confidence": 0-100  // Your confidence in this plan
}}

CONTENT GUIDELINES:
- For emails: Write complete emails with subject, body, and proper formatting
- For social posts: Create engaging, well-written content with appropriate hashtags
- For any content: Be specific, detailed, and professional
- Don't just repeat the user's request - expand on it with quality content"""