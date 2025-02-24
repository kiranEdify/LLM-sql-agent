import os
import json
from dotenv import load_dotenv
import gradio as gr
from db_setup.place_order_v2 import place_order
from db_setup.cancel_order import cancel_order
from sql_agent.sql_agent_v2 import sql_agent
import requests

# Initialization
load_dotenv(override=True)

# Supported local models
AVAILABLE_MODELS = ["llama3.1", "mistral", "codellama"]

# Set default model and endpoint
MODEL = "llama3.1"
OLLAMA_API_URL = 'http://localhost:5500'

def call_ollama(model, messages, tools):
    payload = {
        "model": model,
        "messages": messages,
        "tools": tools
    }
    response = requests.post(f"{OLLAMA_API_URL}/chat/completions", json=payload).json()
    return response

def chatAssist():
    system_message = (
        "You are a helpful assistant for an Electronic distributor company. \n"
        "Give short, courteous answers, no more than 1 sentence. \n"
        "Before placing an order, depict a bill representation as a table.\n"
        "After placing an order, use creative emoji and end gracefully.\n"
        "Before canceling an order, depict order details as a table.\n"
        "Always be accurate. If you don't know the answer, say so."
    )

    tools = [
        {"type": "function", "function": {
            "name": "sql_agent",
            "description": "Query inventory, e.g., list all available products",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query from natural language input"},
                },
                "required": ["query"]
            }
        }},
        {"type": "function", "function": {
            "name": "place_order",
            "description": "Place an order for electrical components",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Customer ID"},
                    "order_items": {
                        "type": "array",
                        "description": "Products and quantities",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "integer", "description": "Product ID"},
                                "quantity": {"type": "integer", "description": "Order quantity"},
                            },
                            "required": ["product_id", "quantity"]
                        }
                    }
                },
                "required": ["customer_id", "order_items"]
            }
        }},
        {"type": "function", "function": {
            "name": "cancel_order",
            "description": "Cancel an existing order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID"},
                },
                "required": ["order_id"]
            }
        }}
    ]

    def handle_tool_call(message):
        tool_call = message['tool_calls'][0]
        function_name = tool_call['function']['name']
        arguments = json.loads(tool_call['function']['arguments'])
        
        if function_name == "place_order":
            return place_order(arguments.get('customer_id'), arguments.get('order_items'))
        elif function_name == "cancel_order":
            return cancel_order(arguments.get('order_id'))
        elif function_name == "sql_agent":
            return sql_agent(arguments.get('query'))

    def chat(message, history, model_choice):
        global MODEL
        MODEL = model_choice
        
        messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
        response = call_ollama(MODEL, messages, tools)
        
        if response['choices'][0]['finish_reason'] == "tool_calls":
            tool_response = handle_tool_call(response['choices'][0]['message'])
            messages.append(response['choices'][0]['message'])
            messages.append({"role": "tool", "content": json.dumps(tool_response)})
            response = call_ollama(MODEL, messages, tools)
        
        return response['choices'][0]['message']['content']

    # Gradio UI with model selection
    def gradio_interface(message, history, model_choice):
        return chat(message, history, model_choice)

    model_dropdown = gr.Dropdown(choices=AVAILABLE_MODELS, value=MODEL, label="Choose Model")
    gr.ChatInterface(fn=gradio_interface, inputs=["text", "state", model_dropdown], outputs="text", title="E-Distributor Chatbot").launch()

if __name__ == "__main__":
    chatAssist()
