
import requests
from dotenv import load_dotenv
from ..db_setup.place_order_v2 import place_order
from ..db_setup.cancel_order import cancel_order
from ..sql_agent.sql_agent_v2 import sql_agent
from .prompts import prompts
from ..data_model.request_payload import OllamaChatRequest
from ..utils.loggers import log_message  # Import the logging function
from .tools import get_tools
from ..db_setup.tax_check_v3 import check_tax_rate, store_tax_rate  # Import the tax_check function

# Initialization
load_dotenv(override=True)


OLLAMA_HOST = "http://localhost:11434"



def chat_with_ollama(messages, tools=None,model="qwen2.5:32b"):
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        # "options": {
        #     "seed": 101,
        #     "temperature": 0
        # }
    }
    if tools:
        payload["tools"] = tools


    log_message("LLM-payload", payload)
    
    response = requests.post(url, json=payload)

    log_message("LLM-response", response.json())
    
    if response.status_code == 200:
        
        return response.json()
    else:
        # raise Exception(f"Error: {response.status_code}, {response.text}")
        error_message = f"LLM API Error: {response.status_code}, {response.text}.\n Clear message history or refresh and try again with different LLM"
        # print(f"LLM API Error: {error_message}\nClear message history or refresh and try again with different LLM")
        return {"message": {"role": "assistant", "content": error_message}}

# Define functions

def handle_tool_call(tool, model):
        
        function_name = tool.get("function", {}).get("name")
        arguments = tool.get("function", {}).get("arguments", {})

        
        if not function_name:
            return {"role": "tool", "content": "Error: Missing function name.", "name": "unknown"}
        
        
        log_message("TOOL-CALL-START", f"function_name: {function_name}\narguments: {arguments}")

        if function_name == "sql_agent":
            response_content = sql_agent(arguments.get("query"), model=model)
        elif function_name == "place_order":
            response_content = place_order(arguments.get("customer_id"), arguments.get("order_items"))
        elif function_name == "cancel_order":
            response_content = cancel_order(arguments.get("order_id"))
        elif function_name == "check_tax_rate":
            response_content = check_tax_rate(arguments.get("state"))  
        else:
            response_content = f"Error: Unknown function '{function_name}'."
        

        log_message("TOOL-CALL-ENDED", f"response_content: {response_content}")

        return {
            "role": "tool", 
            "content": str(response_content), 
            "name": function_name
        }

def ollama_chat_assist(chat_request:OllamaChatRequest):
        
        log_message("CHAT-Payload", {
        "message": chat_request.user_msg,
        "history": chat_request.history,
        "model": chat_request.model
        })
        
        #Building Agent behaviour
        system_message = prompts["ollama_qwen_v2"] + "\n" + chat_request.context
        
        #Building Conversation list  
        messages = [{'role': 'system', 'content': system_message}] + chat_request.history + [{'role': 'user', 'content': chat_request.user_msg}]

        #Initiating the LLM call
        response = chat_with_ollama(
             messages,
             tools=get_tools(),
             model=chat_request.model
            )

        if "message" in response:
            message = response["message"]
            log_message("\nMessage:\n",chat_request.user_msg)

            # Deciding whether to use a tool or not
            if "tool_calls" in message and message["tool_calls"]:
                for tool in message["tool_calls"]:
                    tool_response = handle_tool_call(tool, model=chat_request.model)
                    messages.append(message)  # Append the original response
                    messages.append(tool_response)  # Append tool response

                # Call API again with updated tool-call response messages
                response = chat_with_ollama(messages,model=chat_request.model)

            if "message" in response:
                log_message("CHAT-Response", response["message"]["content"])


        return response["message"]["content"]
    

    

