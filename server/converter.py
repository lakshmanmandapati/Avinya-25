import json
import os
import requests
from dotenv import load_dotenv
from typing import Any

# Load environment variables from a .env file
load_dotenv()

class JsonToNaturalLanguage:
    """
    A class to convert JSON data into clean, structured natural language summaries
    focused on user-relevant information from various applications.
    """
    _PROMPT_TEMPLATE = """
    Convert the following JSON data into a clear, structured natural language summary.
    Focus on information that would be most relevant to an end user.

    Guidelines:
    1. Identify the application/service type (LinkedIn, Gmail, etc.) from the JSON structure
    2. Extract only the most important information for the end user
    3. Organize information in a logical, hierarchical structure
    4. Use clear section headings without markdown formatting
    5. Exclude technical details like IDs, server information unless absolutely necessary
    6. For emails: focus on sender, subject, date, and key content
    7. For social media posts: focus on content, visibility, and success status
    8. For other apps: identify the key action and result
    9. Keep the summary concise but informative

    JSON Data:
    {json_str}

    Provide your response in this structured format:
    [Application Type] Summary:
    Status: [success/failure/other]
    Key Action: [what was done]
    Main Content: [primary information]
    Additional Details: [other relevant info]
    Result/Outcome: [what happened as a result]
    """

    def __init__(self):
        """Initializes the converter and sets up the API client."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Please set the GEMINI_API_KEY environment variable.")
        
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def convert(self, json_data: Any) -> str:
        """Converts JSON data into a clean, structured natural language summary."""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            if not isinstance(data, (dict, list)):
                return str(data)

            prompt = self._create_prompt(data)
            return self._call_gemini_api(prompt)
        except Exception as e:
            print(f"An unexpected error occurred during conversion: {e}")
            return str(json_data)

    def _create_prompt(self, data: dict | list) -> str:
        """Builds the instruction prompt for the Gemini API."""
        json_str = json.dumps(data, indent=2)
        return self._PROMPT_TEMPLATE.format(json_str=json_str)

    def _call_gemini_api(self, prompt: str) -> str:
        """Sends the request to the Gemini API."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
                "topP": 0.8,
                "topK": 40
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        try:
            response = self.session.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            api_response = response.json()
            return self._parse_api_response(api_response)
        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}")
            return "Error: Could not connect to the API."

    def _parse_api_response(self, response_data: dict) -> str:
        """Safely extracts the text content from the Gemini API response."""
        try:
            # Check for errors in response
            if 'error' in response_data:
                return f"API Error: {response_data['error']['message']}"
            
            # Extract text from successful response
            text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean up response by removing any markdown artifacts
            cleaned_text = text.replace('###', '').replace('**', '').replace('*', '').strip()
            
            return cleaned_text
        except (KeyError, IndexError, TypeError) as e:
            print(f"Could not parse Gemini response: {e}")
            return "Error: Failed to parse the API response."


# Example usage
if __name__ == "__main__":
    converter = JsonToNaturalLanguage()
    
    # Example 1: LinkedIn post JSON
    linkedin_json = {
        "status": "SUCCESS",
        "content": [
            {
                "type": "text",
                "text": "{\"id\": \"21d7737d-95e3-4798-9272-2c3e95c99314\", \"actionId\": \"63508e62-bea0-41b6-8733-8e83c6aba234\", \"serverId\": \"583783e7-ed66-4f50-90c3-520536daf7bc\", \"instructions\": \"Post an update on LinkedIn about MCP servers.\", \"parameters\": {\"comment\": \"Exciting news for IT professionals! We're diving deep into the capabilities of MCP servers, exploring how they streamline operations, enhance security, and boost performance for modern infrastructures. What are your experiences or insights with MCP servers? Share below! #MCP #ServerManagement #ITInfrastructure #TechInnovation\", \"instructions\": \"Post an update on LinkedIn about MCP servers.\", \"visibility__code\": \"CONNECTIONS\"}, \"resolvedParameters\": {\"comment\": {\"value\": \"Exciting news for IT professionals! We're diving deep into the capabilities of MCP servers, exploring how they streamline operations, enhance security, and boost performance for modern infrastructures. What are your experiences or insights with MCP servers? Share below! #MCP #ServerManagement #ITInfrastructure #TechInnovation\", \"label\": \"Comment\", \"status\": \"locked\", \"reason\": \"top-level-hint\"}, \"visibility__code\": {\"value\": \"connections-only\", \"label\": \"Connections-only\", \"status\": \"guessed\", \"reason\": \"llm-guess\"}}, \"status\": \"SUCCESS\", \"created\": \"2025-09-17T07:31:54.730Z\", \"invocationId\": \"8dc21e29-4216-4e48-be0e-77b07ba504b0\", \"feedbackUrl\": \"https://mcp.zapier.com/mcp/servers/583783e7-ed66-4f50-90c3-520536daf7bc/history/executions/21d7737d-95e3-4798-9272-2c3e95c99314\", \"result\": {\"url\": \"https://www.linkedin.com/feed/update/urn:li:share:7373982013701222400/\"}, \"isPreview\": false}"
            }
        ]
    }
    
    # Example 2: Gmail emails JSON
    gmail_json = {
        "status": "SUCCESS",
        "content": [
            {
                "type": "text",
                "text": "{\"id\": \"6beeee3b-c942-45b7-99ce-7973744bb065\", \"actionId\": \"eef51b9e-1044-463c-98d4-bd68db3e4d07\", \"serverId\": \"583783e7-ed66-4f50-90c3-520536daf7bc\", \"instructions\": \"Find the most recent emails in the user's Gmail inbox.\", \"parameters\": {\"query\": \"in:inbox\"}, \"resolvedParameters\": {\"query\": {\"value\": \"in:inbox\", \"label\": \"Query\", \"status\": \"locked\", \"reason\": \"top-level-hint\"}}, \"status\": \"SUCCESS\", \"created\": \"2025-09-17T07:21:15.355Z\", \"invocationId\": \"9620a4fb-f083-4031-8c84-60d9d539e2b1\", \"isPreview\": false, \"feedbackUrl\": \"https://mcp.zapier.com/mcp/servers/583783e7-ed66-4f50-90c3-520536daf7bc/history/executions/6beeee3b-c942-45b7-99ce-7973744bb065\", \"result\": [{\"id\": \"123\", \"message_id\": \"msg123\", \"thread_id\": \"thread123\", \"message_url\": \"https://mail.google.com/mail/u/0/#inbox/msg123\", \"to\": {\"names\": [], \"emails\": [\"imadabathuniharsha@gmail.com\"]}, \"cc\": {\"names\": [], \"emails\": []}, \"from\": {\"name\": \"\", \"email\": \"imadabathuniharsha@gmail.com\"}, \"reply_to\": {\"name\": \"\", \"email\": \"\"}, \"subject\": \"Regarding MCP\", \"body_plain\": \"Hello, I wanted to discuss the MCP implementation.\", \"date\": \"2025-09-16T10:30:00Z\", \"labels\": [\"UNREAD\", \"INBOX\"], \"attachment_count\": 0, \"all_attachments\": null}]}"
            }
        ]
    }
    
    print("LinkedIn Conversion Result:")
    result1 = converter.convert(linkedin_json)
    print(result1)
    
    print("\n" + "="*50 + "\n")
    
    print("Gmail Conversion Result:")
    result2 = converter.convert(gmail_json)
    print(result2)