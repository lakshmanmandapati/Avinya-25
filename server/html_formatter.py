import json
import re

def convert_json_to_text(data):
    """
    Convert JSON data to a formatted text representation
    """
    if not data:
        return "No data received"
    
    # Handle error responses
    if "error" in data:
        error_msg = data.get("error", "Unknown error")
        details = data.get("details", "")
        return f"Error: {error_msg}\nDetails: {details}"
    
    # Handle tool listing responses
    if "result" in data and "tools" in data["result"]:
        return format_tools_list(data["result"]["tools"])
    
    # Handle tool execution results
    if "result" in data:
        return format_tool_result(data["result"])
    
    # Handle AI plan responses
    if "plan" in data and "actions" in data:
        return format_ai_plan(data)
    
    # Handle chat responses
    if "response" in data:
        return data["response"]
    
    # Handle execution results
    if "results" in data:
        return format_execution_results(data)
    
    # Default: return pretty-printed JSON
    return json.dumps(data, indent=2)

def format_tools_list(tools):
    """
    Format a list of tools into a readable text format
    """
    if not tools:
        return "No tools available"
    
    result = "Available Tools:\n"
    result += "=" * 50 + "\n\n"
    
    for i, tool in enumerate(tools, 1):
        result += f"{i}. {tool.get('name', 'Unnamed Tool')}\n"
        result += f"   Description: {tool.get('description', 'No description available')}\n"
        
        # Add input schema information if available
        if "inputSchema" in tool and "properties" in tool["inputSchema"]:
            result += "   Parameters:\n"
            for param, details in tool["inputSchema"]["properties"].items():
                param_type = details.get("type", "any")
                param_desc = details.get("description", "")
                result += f"     - {param} ({param_type}): {param_desc}\n"
        
        result += "\n"
    
    return result

def format_tool_result(result):
    """
    Format a tool execution result into readable text
    """
    if isinstance(result, dict):
        # Check for specific tool result formats
        if "content" in result:
            # This might be a response from an email or message tool
            return result.get("content", "No content returned")
        
        # Generic dictionary formatting
        formatted = ""
        for key, value in result.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            
            formatted += f"{key}: {value_str}\n"
        
        return formatted if formatted else "Operation completed successfully"
    
    elif isinstance(result, list):
        return "\n".join([str(item) for item in result])
    
    else:
        return str(result)

def format_ai_plan(plan_data):
    """
    Format an AI plan into readable text
    """
    plan = plan_data.get("plan", "No plan provided")
    actions = plan_data.get("actions", [])
    confidence = plan_data.get("confidence", "N/A")
    
    result = f"Plan: {plan}\n\n"
    result += f"Confidence: {confidence}%\n\n"
    result += "Actions:\n"
    result += "-" * 50 + "\n"
    
    for i, action in enumerate(actions, 1):
        result += f"{i}. {action.get('tool', 'Unknown Tool')}\n"
        result += f"   Reasoning: {action.get('reasoning', 'No reasoning provided')}\n"
        
        parameters = action.get("parameters", {})
        if parameters:
            result += "   Parameters:\n"
            for param, value in parameters.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=4).replace("\n", "\n      ")
                else:
                    value_str = str(value)
                result += f"     - {param}: {value_str}\n"
        
        result += "\n"
    
    return result

def format_execution_results(execution_data):
    """
    Format execution results into readable text
    """
    results = execution_data.get("results", [])
    status = execution_data.get("status", "Unknown status")
    
    result_text = f"Execution Status: {status}\n\n"
    result_text += "Results:\n"
    result_text += "=" * 50 + "\n"
    
    for i, action_result in enumerate(results, 1):
        action = action_result.get("action", "Unknown Action")
        success = action_result.get("success", False)
        error = action_result.get("error")
        result = action_result.get("result", {})
        
        result_text += f"{i}. {action}: {'✅ Success' if success else '❌ Failed'}\n"
        
        if error:
            result_text += f"   Error: {error}\n"
        
        if result:
            if isinstance(result, dict) and "content" in result:
                result_text += f"   Result: {result['content']}\n"
            else:
                result_str = str(result)
                if len(result_str) > 200:
                    result_str = result_str[:200] + "..."
                result_text += f"   Result: {result_str}\n"
        
        result_text += "\n"
    
    return result_text

# For testing the converter
if __name__ == "__main__":
    # Test with sample data
    sample_tools = {
        "result": {
            "tools": [
                {
                    "name": "send_email",
                    "description": "Send an email to a recipient",
                    "inputSchema": {
                        "properties": {
                            "to": {"type": "string", "description": "Recipient email address"},
                            "subject": {"type": "string", "description": "Email subject"},
                            "body": {"type": "string", "description": "Email content"}
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            ]
        }
    }
    
    sample_plan = {
        "plan": "Send an email to John about the meeting",
        "actions": [
            {
                "tool": "send_email",
                "reasoning": "User requested to send an email to John",
                "parameters": {
                    "to": "john@example.com",
                    "subject": "Meeting Tomorrow",
                    "body": "Hi John, let's meet tomorrow at 10 AM to discuss the project."
                }
            }
        ],
        "confidence": 95
    }
    
    print("=== Tools List ===")
    print(convert_json_to_text(sample_tools))
    print("\n=== AI Plan ===")
    print(convert_json_to_text(sample_plan))