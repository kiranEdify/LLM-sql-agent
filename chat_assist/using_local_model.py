import os
import json
import requests
from dotenv import load_dotenv
import gradio as gr
from db_setup.place_order_v2 import place_order
from db_setup.cancel_order import cancel_order
from sql_agent.sql_agent_v2 import sql_agent

# Initialization
load_dotenv(override=True)

OLLAMA_API_URL = 'http://localhost:11434/api/chat'
MODEL = "llama3.1"

def chatAssist():
    system_message = (
        "You are a helpful assistant for an Electronic distributor company. "
        "Give short, courteous answers, no more than 1 sentence. "
        "Before placing an order, depict a bill representation as a table. "
        "After placing an order, use creative emojis and end gracefully. "
        "Before canceling an order, depict order details as a table. "
        "Always be accurate. If you don't know the answer, say so."
    )

    tools = [
        {"name": "sql_agent", "description": "Query inventory.", "parameters": ["query"]},
        {"name": "place_order", "description": "Place an order.", "parameters": ["customer_id", "order_items"]},
        {"name": "cancel_order", "description": "Cancel an order.", "parameters": ["order_id"]}
    ]

    def handle_tool_call(tool_name, arguments):
        response_content = ""
        if tool_name == "place_order":
            response_content = place_order(arguments["customer_id"], arguments["order_items"])
        elif tool_name == "cancel_order":
            response_content = cancel_order(arguments["order_id"])
        elif tool_name == "sql_agent":
            response_content = sql_agent(arguments["query"])
        return response_content

    def chat(message, history):
        payload = {
            "model": MODEL,
            "messages": [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}],
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        response_json = response.json()

        if "tool_calls" in response_json.get("choices", [{}])[0]:
            tool_call = response_json["choices"][0]["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            tool_response = handle_tool_call(tool_name, arguments)

            # Send the response back to the model
            payload["messages"].append({"role": "assistant", "content": tool_response})
            response = requests.post(OLLAMA_API_URL, json=payload)
            response_json = response.json()

        return response_json["choices"][0]["message"]["content"]

    gr.ChatInterface(fn=chat, type="messages").launch()

if __name__ == "__main__":
    chatAssist()
