import os
import json
import re
import time
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
from pathlib import Path
from google.cloud import speech

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Configure CORS to allow requests from your frontend
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:4000", "*"])

# Modal endpoint for Groq provider
MODAL_ENDPOINT = "https://imadabathuniharsha--llama3-serve-optimized-model-web-generate.modal.run"

# Initialize Google Cloud Speech client using environment variables
# This supports both production (env vars) and development (local file)
client = None
try:
    # Try to initialize using environment variables first (PRODUCTION - Render)
    if os.getenv("GOOGLE_CLOUD_CREDENTIALS_JSON"):
        # Use credentials from environment variable (for production)
        import tempfile
        import json
        
        credentials_json = os.getenv("GOOGLE_CLOUD_CREDENTIALS_JSON")
        credentials_dict = json.loads(credentials_json)
        
        # Create temporary file for credentials
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(credentials_dict, temp_file)
            temp_credentials_path = temp_file.name
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_credentials_path
        client = speech.SpeechClient()
        print("✅ Google Cloud Speech client initialized from environment variables.")
        
        # Clean up temporary file
        os.unlink(temp_credentials_path)
        
    elif os.path.exists("server/gcp_key.json"):
        # Fallback to local file for development (NOT for production)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "server/gcp_key.json"
        client = speech.SpeechClient()
        print("✅ Google Cloud Speech client initialized from local file (development mode).")
        print("⚠️  WARNING: Using local credentials file. Use environment variables in production!")
        
    else:
        print("❌ No Google Cloud credentials found. Set GOOGLE_CLOUD_CREDENTIALS_JSON environment variable.")
        
except Exception as e:
    print(f"❌ FATAL ERROR: Could not initialize Google Cloud client.")
    print(f"DETAILS: {e}")
    print("💡 SOLUTION: Set GOOGLE_CLOUD_CREDENTIALS_JSON environment variable with your service account JSON.")

# Speech-to-text endpoint
@app.route("/speech-to-text", methods=["POST"])
def speech_to_text():
    print("\n--- Received a request on /speech-to-text ---")
    if client is None:
        print("❌ Request failed because Google client is not initialized.")
        return jsonify({"error": "Google Cloud client not initialized on server."}), 500
        
    if "file" not in request.files:
        print("❌ Request failed because no 'file' was found.")
        return jsonify({"error": "No audio file found in the request."}), 400

    try:
        audio_file = request.files["file"]
        content = audio_file.read()
        print(f"✅ Received an audio file of size: {len(content)} bytes.")

        # Check if audio content is empty
        if len(content) == 0:
            print("❌ Empty audio file received.")
            return jsonify({"error": "Empty audio file"}), 400

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_short"  # Use latest short-form model for better accuracy
        )

        print("... Sending audio to Google API for transcription ...")
        response = client.recognize(config=config, audio=audio)
        print("✅ Received response from Google API.")
        
        if not response.results:
            print("- Google API returned no results.")
            return jsonify({"text": ""})

        transcription = response.results[0].alternatives[0].transcript
        print(f"✅ Transcription successful: '{transcription}'")
        return jsonify({"text": transcription})

    except Exception as e:
        print(f"❌ An error occurred during transcription: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



# Global counter for JSON-RPC IDs
rpc_counter = 1

# Load MCP servers configuration
def load_mcp_config():
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ config.json not found, using default configuration")
        return {
            "mcpServers": {
                "Default": {"url": "http://localhost:5000/mcp"}
            }
        }
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing config.json: {e}")
        return {"mcpServers": {}}

mcp_config = load_mcp_config()

# Helper function to get server URL by name
def get_server_url(server_name):
    servers = mcp_config.get("mcpServers", {})
    if server_name in servers:
        return servers[server_name]["url"]
    # Fallback to first available server if name not found
    if servers:
        first_server = next(iter(servers.values()))
        return first_server["url"]
    return None

# Helper function to wrap responses in Cursor MCP format
def wrap_tools_response(data):
    """Ensure tools/list responses are properly wrapped"""
    if isinstance(data, dict):
        if "result" in data and "tools" in data["result"]:
            return data  # Already properly wrapped
        elif "tools" in data:
            return {"result": {"tools": data["tools"]}}
        elif isinstance(data.get("result"), list):
            return {"result": {"tools": data["result"]}}
        elif "error" in data or "parseError" in data:
            # For errors, create mock tools response to maintain format
            return {"result": {"tools": []}}
    # Default fallback - create empty tools array
    return {"result": {"tools": []}}

def wrap_tool_call_response(data):
    """Ensure tools/call responses are properly wrapped"""
    if isinstance(data, dict):
        if "result" in data and "output" in data["result"]:
            return data  # Already properly wrapped
        elif "result" in data:
            return {"result": {"output": data["result"]}}
        elif "error" in data or "parseError" in data:
            # For errors, wrap in output format
            return {"result": {"output": {"error": data.get("error", data.get("parseError", "Unknown error"))}}}
    # Default fallback
    return {"result": {"output": data}}

# Import converter module
try:
    from converter import JsonToNaturalLanguage
    converter = JsonToNaturalLanguage()
    print("✅ JSONConverter loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import JSONConverter: {e}")
    # Create a fallback converter
    class FallbackConverter:
        def convert_json(self, json_data):
            try:
                return json.dumps(json_data, indent=2)
            except:
                return str(json_data)
    converter = FallbackConverter()

# Import IntentParser from separate file
try:
    from intentParser import IntentParser
    intent_parser = IntentParser()
    print("✅ IntentParser loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import IntentParser: {e}")
    # Create a fallback intent parser
    class FallbackIntentParser:
        def analyze_intent(self, user_input, available_tools=None):
            return {"mode": "chat", "response": "Intent parser not available"}
        def get_enhanced_system_prompt(self, tools_info, prompt, mode):
            return "You are a helpful assistant."
    intent_parser = FallbackIntentParser()

# Import conversation management with error handling
try:
    from conversation_manager import conversation_manager
    from title_generator import title_generator
    print("✅ Conversation management loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import conversation management: {e}")
    print("⚠️ Conversation features will be disabled")
    # Create fallback objects
    class FallbackConversationManager:
        def create_conversation(self, title=None):
            return f"fallback_{int(time.time())}"
        def add_message(self, *args, **kwargs):
            return True
        def get_conversation(self, conversation_id):
            return {"id": conversation_id, "messages": [], "title": "Fallback Chat"}
        def get_all_conversations(self):
            return []
        def delete_conversation(self, conversation_id):
            return True
        def update_conversation_title(self, conversation_id, title):
            return True
    
    class FallbackTitleGenerator:
        def generate_title(self, query, provider="gemini", model=None):
            return query[:30] + "..." if len(query) > 30 else query
    
    conversation_manager = FallbackConversationManager()
    title_generator = FallbackTitleGenerator()

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# SSE endpoint for streaming responses
@app.route("/proxy/stream", methods=["POST", "OPTIONS"])
def proxy_stream():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    global rpc_counter
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
        
    # Support both direct URL and serverName routing
    url = data.get("url")
    server_name = data.get("serverName")
    action = data.get("action")
    
    if not url and server_name:
        url = get_server_url(server_name)
        if not url:
            # Return wrapped error response based on action
            if action == "listTools":
                return jsonify({"result": {"tools": []}})
            elif action == "callTool":
                return jsonify({"result": {"output": {"error": f"Server '{server_name}' not found in configuration"}}})
            return jsonify({"error": f"Server '{server_name}' not found in configuration"}), 400
    elif not url:
        # Return wrapped error response based on action
        if action == "listTools":
            return jsonify({"result": {"tools": []}})
        elif action == "callTool":
            return jsonify({"result": {"output": {"error": "Missing MCP webhook URL or serverName"}}})
        return jsonify({"error": "Missing MCP webhook URL or serverName"}), 400
        
    tool_name = data.get("toolName")
    args = data.get("args", {})
    headers = data.get("headers", {})
    raw_payload = data.get("rawPayload")
    
    # Build payload
    payload = raw_payload
    if not payload:
        if action == "listTools":
            payload = {
                "jsonrpc": "2.0",
                "id": str(rpc_counter),
                "method": "tools/list",
                "params": {}
            }
            rpc_counter += 1
        elif action == "callTool":
            if not tool_name:
                return jsonify({"error": "Missing toolName for callTool"}), 400
            payload = {
                "jsonrpc": "2.0",
                "id": str(rpc_counter),
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args}
            }
            rpc_counter += 1
        else:
            return jsonify({"error": "Invalid action or payload"}), 400
    
    print("➡️ Sent to MCP:", json.dumps(payload, indent=2))
    
    def generate():
        # Send initial status
        yield f"data: {json.dumps({'type': 'status', 'message': 'Sending request to MCP server...', 'payload': payload})}\n\n"
        
        try:
            # Make request to MCP server
            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    **headers
                },
                json=payload,
                stream=True,
                timeout=60
            )
            
            content_type = response.headers.get('content-type', '')
            
            if 'text/event-stream' in content_type:
                # Handle SSE response from MCP server
                yield f"data: {json.dumps({'type': 'status', 'message': 'Processing SSE response...'})}\n\n"
                
                # Process SSE lines
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith('data: '):
                        event_data = line[6:].strip()
                        if event_data:
                            try:
                                parsed = json.loads(event_data)
                                # Convert JSON to readable format
                                if action == "callTool" and "result" in parsed and "output" in parsed["result"]:
                                    readable_output = converter.convert(parsed["result"]["output"])
                                    parsed["result"]["output"] = readable_output
                                
                                # Wrap in Cursor-compatible envelope
                                cursor_chunk = {'type': 'chunk', 'data': parsed}
                                yield f"data: {json.dumps(cursor_chunk)}\n\n"
                            except json.JSONDecodeError:
                                cursor_chunk = {'type': 'chunk', 'data': {'raw': event_data}}
                                yield f"data: {json.dumps(cursor_chunk)}\n\n"
                
                yield f"data: {json.dumps({'type': 'status', 'message': 'Response complete'})}\n\n"
            else:
                # Handle regular JSON response
                text = response.text
                print("⬅️ Received from MCP:", text)
                
                data = {}
                try:
                    # Check if response is SSE format
                    if text.startswith('event:') or 'data:' in text:
                        print("🔄 Detected SSE format, parsing...")
                        lines = text.split('\n')
                        json_data = None
                        
                        for line in lines:
                            if line.startswith('data: '):
                                event_data = line[6:].strip()
                                if event_data:
                                    try:
                                        json_data = json.loads(event_data)
                                        break
                                    except json.JSONDecodeError:
                                        print("⚠️ Failed to parse SSE data line:", event_data)
                        
                        data = json_data or {"raw": text, "error": "Could not parse SSE data"}
                    else:
                        # Regular JSON parsing
                        data = response.json()
                        
                        # Apply proper wrapping based on action
                        if action == "listTools":
                            data = wrap_tools_response(data)
                        elif action == "callTool":
                            data = wrap_tool_call_response(data)
                            
                            # Convert JSON output to readable format
                            if "result" in data and "output" in data["result"]:
                                data["result"]["output"] = converter.convert(data["result"]["output"])
                        
                except json.JSONDecodeError:
                    data = {"raw": text}
                
                yield f"data: {json.dumps({'type': 'complete', 'data': data})}\n\n"
                yield f"data: {json.dumps({'type': 'status', 'message': 'Response complete'})}\n\n"
                
        except Exception as err:
            print("Proxy error:", err)
            yield f"data: {json.dumps({'type': 'error', 'error': 'Failed to reach MCP server', 'details': str(err)})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive',
                           'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Cache-Control'})

# Regular JSON endpoint (fallback)
@app.route("/proxy", methods=["POST", "OPTIONS"])
def proxy():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    global rpc_counter
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
        
    # Support both direct URL and serverName routing
    url = data.get("url")
    server_name = data.get("serverName")
    action = data.get("action")
    
    if not url and server_name:
        url = get_server_url(server_name)
        if not url:
            # Return wrapped error response based on action
            if action == "listTools":
                return jsonify({"result": {"tools": []}})
            elif action == "callTool":
                return jsonify({"result": {"output": {"error": f"Server '{server_name}' not found in configuration"}}})
            return jsonify({"error": f"Server '{server_name}' not found in configuration"}), 400
    elif not url:
        # Return wrapped error response based on action
        if action == "listTools":
            return jsonify({"result": {"tools": []}})
        elif action == "callTool":
            return jsonify({"result": {"output": {"error": "Missing MCP webhook URL or serverName"}}})
        return jsonify({"error": "Missing MCP webhook URL or serverName"}), 400
        
    tool_name = data.get("toolName")
    args = data.get("args", {})
    headers = data.get("headers", {})
    raw_payload = data.get("rawPayload")
    
    # Build payload
    payload = raw_payload
    if not payload:
        if action == "listTools":
            payload = {
                "jsonrpc": "2.0",
                "id": str(rpc_counter),
                "method": "tools/list",
                "params": {}
            }
            rpc_counter += 1
        elif action == "callTool":
            if not tool_name:
                return jsonify({"error": "Missing toolName for callTool"}), 400
            payload = {
                "jsonrpc": "2.0",
                "id": str(rpc_counter),
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args}
            }
            rpc_counter += 1
        else:
            return jsonify({"error": "Invalid action or payload"}), 400
    
    print("➡️ Sent to MCP:", json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                **headers
            },
            json=payload,
            timeout=60
        )
        
        print("📊 Response Status:", response.status_code, response.reason)
        print("📋 Response Headers:", dict(response.headers))
        
        text = response.text
        print("⬅️ Received Raw from MCP:", text)
        
        data = {}
        try:
            # Check if response is SSE format
            if text.startswith('event:') or 'data:' in text:
                print("🔄 Detected SSE format, parsing...")
                lines = text.split('\n')
                json_data = None
                
                for line in lines:
                    if line.startswith('data: '):
                        event_data = line[6:].strip()
                        if event_data:
                            try:
                                json_data = json.loads(event_data)
                                break
                            except json.JSONDecodeError:
                                print("⚠️ Failed to parse SSE data line:", event_data)
                
                data = json_data or {"raw": text, "error": "Could not parse SSE data"}
            else:
                # Regular JSON parsing
                data = response.json()
                
                # Apply proper wrapping based on action
                if action == "listTools":
                    data = wrap_tools_response(data)
                elif action == "callTool":
                    data = wrap_tool_call_response(data)
                    
                    # Convert JSON output to readable format
                    if "result" in data and "output" in data["result"]:
                        data["result"]["output"] = converter.convert(data["result"]["output"])
                
                print("✅ Parsed JSON:", json.dumps(data, indent=2))
                
                # Debug tools parsing specifically
                if data.get("result") and data["result"].get("tools"):
                    print("🔧 Found tools:", len(data["result"]["tools"]))
                    for idx, tool in enumerate(data["result"]["tools"]):
                        print(f"  Tool {idx + 1}: {tool.get('name')} - {tool.get('description')}")
                else:
                    print("❌ No tools found in result. Full response structure:", list(data.keys()))
                    if data.get("result"):
                        print("📝 Result keys:", list(data["result"].keys()))
                        
        except json.JSONDecodeError as parse_error:
            print("❌ JSON Parse Error:", str(parse_error))
            data = {"raw": text, "parseError": str(parse_error)}
        
        # Always ensure proper wrapping for ALL responses
        if action == "listTools":
            data = wrap_tools_response(data)
        elif action == "callTool":
            data = wrap_tool_call_response(data)
            
            # Convert JSON output to readable format if not already done
            if "result" in data and "output" in data["result"] and isinstance(data["result"]["output"], (dict, list)):
                data["result"]["output"] = converter.convert(data["result"]["output"])
        
        return jsonify(data)
        
    except Exception as err:
        print("Proxy error:", err)
        return jsonify({"error": "Failed to reach MCP server", "details": str(err)}), 500

# AI endpoint for processing prompts
@app.route("/proxy/ai", methods=["POST", "OPTIONS"])
def proxy_ai():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        print(f"Received AI request: {data}")
        
        provider = data.get("provider")
        prompt = data.get("prompt")
        mcp_url = data.get("mcpUrl")
        server_name = data.get("serverName")
        conversation_id = data.get("conversation_id")
        
        # Support serverName routing
        if not mcp_url and server_name:
            mcp_url = get_server_url(server_name)
            if not mcp_url:
                return jsonify({"error": f"Server '{server_name}' not found in configuration"}), 400
        
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400
        
        # Create new conversation if not provided
        if not conversation_id:
            conversation_id = conversation_manager.create_conversation()
            print(f"Created new conversation: {conversation_id}")
        
        # Save user message to conversation
        conversation_manager.add_message(
            conversation_id, 
            "user", 
            prompt, 
            "text",
            {"provider": provider, "mcp_url": mcp_url}
        )
        
        # Check if provider is groq - use Modal endpoint
        if provider == "groq":
            print("🔄 Using Groq provider - routing to Modal endpoint")
            
            try:
                # Call Modal endpoint directly
                modal_response = requests.post(
                    MODAL_ENDPOINT,
                    headers={"Content-Type": "application/json"},
                    json={"prompt": prompt},
                    timeout=60
                )
                
                if modal_response.status_code == 200:
                    modal_data = modal_response.json()
                    response_text = modal_data.get("response", "No response from Modal endpoint")
                    
                    # Return in the expected format
                    cursor_response = {
                        "mode": "chat",
                        "response": response_text,
                        "plan": "Tensora AI response",
                        "actions": [],
                        "confidence": 100,
                        "conversation_id": conversation_id
                    }
                    
                    # Save assistant response to conversation
                    conversation_manager.add_message(
                        conversation_id,
                        "assistant",
                        response_text,
                        "chat",
                        {"mode": "chat", "provider": "groq", "confidence": 100}
                    )
                    
                    # Generate and update title for new conversations
                    try:
                        conversation = conversation_manager.get_conversation(conversation_id)
                        if conversation and conversation.get("message_count", 0) <= 2:
                            title = title_generator.generate_title(prompt, "groq")
                            conversation_manager.update_conversation_title(conversation_id, title)
                            print(f"Generated title for conversation {conversation_id}: {title}")
                    except Exception as title_error:
                        print(f"Failed to generate title: {title_error}")
                    
                    return jsonify(cursor_response)
                else:
                    error_msg = f"Modal endpoint error: {modal_response.status_code}"
                    print(error_msg)
                    return jsonify({"error": error_msg}), 500
                    
            except Exception as modal_error:
                print(f"Modal endpoint call failed: {modal_error}")
                return jsonify({"error": f"Failed to call Modal endpoint: {str(modal_error)}"}), 500
        
        # For OpenAI and Claude, redirect to Gemini
        if provider in ["openai", "claude"]:
            print(f"🔄 Using {provider} provider - redirecting to Gemini")
            effective_provider = "gemini"
        else:
            effective_provider = provider
        
        # Check for Gemini API key (required for all non-groq providers)
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            return jsonify({"error": "API key for Gemini not configured. All non-Groq providers require Gemini API key."}), 400
            
        api_keys = {"gemini": gemini_api_key}
        
        # First, fetch available tools from MCP
        tools = []
        if mcp_url:
            try:
                print("Fetching tools from MCP server:", mcp_url)
                tools_response = requests.post(
                    "http://localhost:4000/proxy",
                    headers={"Content-Type": "application/json"},
                    json={
                        "url": mcp_url,
                        "action": "listTools"
                    },
                    timeout=10
                )
                
                if tools_response.status_code == 200:
                    tools_data = tools_response.json()
                    tools = tools_data.get("result", {}).get("tools", [])
                    print("Found tools:", len(tools))
                else:
                    print(f"Failed to fetch tools: {tools_response.status_code}")
            except Exception as tools_error:
                print("Failed to fetch tools:", str(tools_error))
                tools = []
        
        # Analyze intent using the intent parser
        intent = intent_parser.analyze_intent(prompt, tools)
        print("Detected intent:", intent)
        
        # Get conversation history for context
        conversation_history = []
        if conversation_id:
            try:
                conversation = conversation_manager.get_conversation(conversation_id)
                if conversation and conversation.get("messages"):
                    recent_messages = conversation["messages"][-10:]
                    for msg in recent_messages:
                        if msg["role"] in ["user", "assistant"]:
                            conversation_history.append({
                                "role": msg["role"],
                                "content": msg["content"]
                            })
            except Exception as e:
                print(f"Failed to get conversation history: {e}")
        
        # Handle chat mode - direct LLM response
        if intent.get("mode") == "chat":
            response = handle_chat_mode(provider, prompt, api_keys, conversation_history)
            response_data = response.get_json()
            
            # Save assistant response to conversation
            conversation_manager.add_message(
                conversation_id,
                "assistant",
                response_data.get("response", ""),
                "chat",
                {"mode": "chat", "confidence": response_data.get("confidence", 100)}
            )
            
            # Generate and update title for new conversations
            try:
                conversation = conversation_manager.get_conversation(conversation_id)
                if conversation and conversation.get("message_count", 0) <= 2:
                    title = title_generator.generate_title(prompt, provider)
                    conversation_manager.update_conversation_title(conversation_id, title)
                    print(f"Generated title for conversation {conversation_id}: {title}")
            except Exception as title_error:
                print(f"Failed to generate title: {title_error}")
            
            # Add conversation_id to response
            response_data["conversation_id"] = conversation_id
            return jsonify(response_data)
        
        # Handle tool mode - existing behavior
        # Prepare tools information for the AI
        tools_info = []
        for tool in tools:
            tool_info = {
                "name": tool.get("name"),
                "description": tool.get("description"),
                "parameters": tool.get("inputSchema", {}).get("properties", {}),
                "required": tool.get("inputSchema", {}).get("required", [])
            }
            tools_info.append(tool_info)
        
        system_prompt = intent_parser.get_enhanced_system_prompt(tools_info, prompt, "tool")
        
        # Use Gemini for all providers
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        
        # Build conversation contents for Gemini
        contents = []
        
        # Add system prompt as first message
        contents.append({
            "parts": [{"text": system_prompt}],
            "role": "user"
        })
        contents.append({
            "parts": [{"text": "I understand. I'll help you with your questions and remember our conversation context."}],
            "role": "model"
        })
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "parts": [{"text": msg["content"]}],
                    "role": role
                })
        
        # Add current user message
        contents.append({
            "parts": [{"text": prompt}],
            "role": "user"
        })
        
        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7, 
                "maxOutputTokens": 2000,
                "response_mime_type": "application/json"
            }
        }
        
        print(f"Sending request to Gemini API (for {provider} provider)")
        response = requests.post(
            endpoint,
            headers=headers,
            json=body,
            timeout=60
        )
        
        if not response.ok:
            error_data = response.json()
            print(f"Gemini API error:", error_data)
            return jsonify({"error": f"Gemini API error: {error_data.get('error', {}).get('message', response.reason)}"}), 500
        
        response_data = response.json()
        
        # Parse response from Gemini
        response_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Extract JSON from response
        ai_response = {}
        try:
            ai_response = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response if it's not pure JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    ai_response = json.loads(json_match.group())
                except json.JSONDecodeError as parse_error:
                    print("Failed to parse JSON, using fallback structure:", parse_error)
                    print("Raw response:", response_text)
                    ai_response = {
                        "plan": response_text.strip(),
                        "actions": [],
                        "confidence": 75
                    }
            else:
                print("No JSON found, creating fallback structure from response:", response_text)
                ai_response = {
                    "plan": response_text.strip() if response_text.strip() else "AI generated plan",
                    "actions": [],
                    "confidence": 70
                }
        
        # Ensure response follows Cursor format
        cursor_response = {
            "plan": ai_response.get("plan", "AI generated plan"),
            "actions": ai_response.get("actions", []),
            "confidence": ai_response.get("confidence", 85),
            "mode": "tool",
            "conversation_id": conversation_id
        }
        
        # Save assistant plan to conversation
        conversation_manager.add_message(
            conversation_id,
            "assistant",
            ai_response.get("plan", "AI generated plan"),
            "plan",
            {
                "mode": "tool",
                "actions": ai_response.get("actions", []),
                "confidence": ai_response.get("confidence", 85)
            }
        )
        
        # Generate and update title for new conversations
        try:
            conversation = conversation_manager.get_conversation(conversation_id)
            if conversation and conversation.get("message_count", 0) <= 2:
                title = title_generator.generate_title(prompt, provider)
                conversation_manager.update_conversation_title(conversation_id, title)
                print(f"Generated title for conversation {conversation_id}: {title}")
        except Exception as title_error:
            print(f"Failed to generate title: {title_error}")
        
        return jsonify(cursor_response)
        
    except Exception as err:
        print("AI processing error:", str(err))
        traceback.print_exc()
        return jsonify({"error": str(err)}), 500

# Execute AI plan endpoint
@app.route("/proxy/ai/execute", methods=["POST", "OPTIONS"])
def proxy_ai_execute():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
        
    actions = data.get("actions")
    mcp_url = data.get("mcpUrl")
    server_name = data.get("serverName")
    
    # Support serverName routing
    if not mcp_url and server_name:
        mcp_url = get_server_url(server_name)
        if not mcp_url:
            return jsonify({"error": f"Server '{server_name}' not found in configuration"}), 400
    
    if not actions or not isinstance(actions, list):
        return jsonify({"error": "Invalid actions"}), 400
    
    try:
        results = []
        for action in actions:
            try:
                print("Executing action:", action.get("tool"))
                action_response = requests.post(
                    "http://localhost:4000/proxy",
                    headers={"Content-Type": "application/json"},
                    json={
                        "url": mcp_url,
                        "action": "callTool",
                        "toolName": action.get("tool"),
                        "args": action.get("parameters", {})
                    },
                    timeout=60
                )
                
                action_result = action_response.json()
                # Ensure proper wrapping for tool call results
                wrapped_result = wrap_tool_call_response(action_result)
                
                # Convert JSON output to readable format
                if "result" in wrapped_result and "output" in wrapped_result["result"]:
                    wrapped_result["result"]["output"] = converter.convert(wrapped_result["result"]["output"])
                
                results.append({
                    "action": action.get("tool"),
                    "success": "error" not in action_result,
                    "result": wrapped_result.get("result", {}).get("output"),
                    "error": action_result.get("error")
                })
                
                # Add a small delay between actions
                time.sleep(0.5)
                
            except Exception as action_error:
                print("Error executing action:", action_error)
                results.append({
                    "action": action.get("tool"),
                    "success": False,
                    "error": str(action_error)
                })
        
        # Return the execution results in Cursor envelope format
        return jsonify({
            "status": "completed",
            "results": results
        })
        
    except Exception as execution_error:
        print("Error executing AI plan:", execution_error)
        return jsonify({
            "error": "Failed to execute AI plan",
            "details": str(execution_error)
        }), 500

def handle_chat_mode(provider, prompt, api_keys, conversation_history=None):
    try:
        # Check if provider is groq - use Modal endpoint
        if provider == "groq":
            print("🔄 Chat Mode: Using Groq provider - routing to Modal endpoint")
            
            try:
                # Call Modal endpoint directly
                modal_response = requests.post(
                    MODAL_ENDPOINT,
                    headers={"Content-Type": "application/json"},
                    json={"prompt": prompt},
                    timeout=60
                )
                
                if modal_response.status_code == 200:
                    modal_data = modal_response.json()
                    response_text = modal_data.get("response", "No response from Modal endpoint")
                    
                    # Return in the expected format
                    return jsonify({
                        "mode": "chat",
                        "response": response_text,
                        "plan": "Tensora AI response",
                        "actions": [],
                        "confidence": 100
                    })
                else:
                    error_msg = f"Modal endpoint error: {modal_response.status_code}"
                    print(error_msg)
                    return jsonify({"error": error_msg}), 500
                    
            except Exception as modal_error:
                print(f"Modal endpoint call failed: {modal_error}")
                return jsonify({"error": f"Failed to call Modal endpoint: {str(modal_error)}"}), 500
        
        # For OpenAI and Claude, redirect to Gemini
        if provider in ["openai", "claude"]:
            print(f"🔄 Chat Mode: Using {provider} provider - redirecting to Gemini")
            effective_provider = "gemini"
        else:
            effective_provider = provider
        
        # Use Gemini for all non-groq providers
        gemini_api_key = api_keys.get("gemini")
        if not gemini_api_key:
            return jsonify({"error": "Gemini API key not configured"}), 400
        
        system_prompt = intent_parser.get_enhanced_system_prompt([], prompt, "chat")
        
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        
        # Build conversation contents for Gemini
        contents = []
        
        # Add system prompt as first message
        contents.append({
            "parts": [{"text": system_prompt}],
            "role": "user"
        })
        contents.append({
            "parts": [{"text": "I understand. I'll help you with your questions and remember our conversation context."}],
            "role": "model"
        })
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "parts": [{"text": msg["content"]}],
                    "role": role
                })
        
        # Add current user message
        contents.append({
            "parts": [{"text": prompt}],
            "role": "user"
        })
        
        body = {
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1000}
        }
        
        print(f"Sending chat request to Gemini API (for {provider} provider)")
        response = requests.post(
            endpoint,
            headers=headers,
            json=body,
            timeout=60
        )
        
        if not response.ok:
            error_data = response.json()
            print(f"Gemini API error:", error_data)
            return jsonify({
                "error": f"Gemini API error: {error_data.get('error', {}).get('message', response.reason)}"
            }), 500
        
        response_data = response.json()
        
        # Parse response from Gemini
        response_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Return chat response in a format compatible with the frontend
        return jsonify({
            "mode": "chat",
            "response": response_text,
            "plan": "Conversational response",
            "actions": [],
            "confidence": 100
        })
        
    except Exception as err:
        print("Chat mode error:", str(err))
        traceback.print_exc()
        return jsonify({
            "error": "I tried to respond but something went wrong. Please try again.",
            "details": str(err)
        }), 500

# Title generation endpoint
@app.route("/title", methods=["POST", "OPTIONS"])
def generate_title():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        query = data.get("query")
        provider = data.get("provider", "gemini")
        model = data.get("model")
        
        if not query:
            return jsonify({"error": "Missing query parameter"}), 400
        
        title = title_generator.generate_title(query, provider, model)
        
        return jsonify({
            "title": title,
            "query": query,
            "provider": provider
        })
        
    except Exception as err:
        print("Title generation error:", str(err))
        return jsonify({"error": str(err)}), 500

# Conversation management endpoints
@app.route("/conversations", methods=["GET", "OPTIONS"])
def get_conversations():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        conversations = conversation_manager.get_all_conversations()
        return jsonify({
            "conversations": conversations,
            "total": len(conversations)
        })
    except Exception as err:
        print("Get conversations error:", str(err))
        return jsonify({"error": str(err)}), 500

@app.route("/conversation/<conversation_id>", methods=["GET", "OPTIONS"])
def get_conversation(conversation_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify(conversation)
    except Exception as err:
        print("Get conversation error:", str(err))
        return jsonify({"error": str(err)}), 500

@app.route("/conversation", methods=["POST", "OPTIONS"])
def create_conversation():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        data = request.get_json() or {}
        title = data.get("title")
        
        conversation_id = conversation_manager.create_conversation(title)
        
        return jsonify({
            "conversation_id": conversation_id,
            "title": title or "New Chat",
            "created": True
        })
    except Exception as err:
        print("Create conversation error:", str(err))
        return jsonify({"error": str(err)}), 500

@app.route("/conversation/<conversation_id>", methods=["DELETE", "OPTIONS"])
def delete_conversation(conversation_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        success = conversation_manager.delete_conversation(conversation_id)
        if not success:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify({"deleted": True, "conversation_id": conversation_id})
    except Exception as err:
        print("Delete conversation error:", str(err))
        return jsonify({"error": str(err)}), 500

@app.route("/add_message", methods=["POST", "OPTIONS"])
def add_message():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        conversation_id = data.get("conversation_id")
        role = data.get("role")
        content = data.get("content")
        message_type = data.get("type", "text")
        metadata = data.get("metadata", {})
        
        if not all([conversation_id, role, content]):
            return jsonify({"error": "Missing required fields: conversation_id, role, content"}), 400
        
        success = conversation_manager.add_message(
            conversation_id, role, content, message_type, metadata
        )
        
        if not success:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify({
            "added": True,
            "conversation_id": conversation_id,
            "role": role,
            "type": message_type
        })
    except Exception as err:
        print("Add message error:", str(err))
        return jsonify({"error": str(err)}), 500

@app.route("/conversation/<conversation_id>/title", methods=["PUT", "OPTIONS"])
def update_conversation_title(conversation_id):
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
        
        title = data.get("title")
        if not title:
            return jsonify({"error": "Missing title"}), 400
        
        success = conversation_manager.update_conversation_title(conversation_id, title)
        if not success:
            return jsonify({"error": "Conversation not found"}), 404
        
        return jsonify({
            "updated": True,
            "conversation_id": conversation_id,
            "title": title
        })
    except Exception as err:
        print("Update title error:", str(err))
        return jsonify({"error": str(err)}), 500

# Health check endpoint for Docker/Render
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})

if __name__ == '__main__':
    port = int(os.getenv("PORT", 4000))
    print(f"🚀 MCP Proxy running at http://0.0.0.0:{port}")
    print(f"🔗 Groq provider uses Modal endpoint: {MODAL_ENDPOINT}")
    print(f"🔄 OpenAI and Claude providers redirect to Gemini")
    app.run(host='0.0.0.0', port=port, debug=True)
