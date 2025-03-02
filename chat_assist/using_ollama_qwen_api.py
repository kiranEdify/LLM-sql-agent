import os
import json
from dotenv import load_dotenv
import gradio as gr
from ollama import  Client
from db_setup.place_order_v2 import place_order
from db_setup.cancel_order import cancel_order
from sql_agent.sql_agent_v2 import sql_agent
from .prompts import prompts
import requests

# Initialization
load_dotenv(override=True)

# ollama_client = Client(
#     host ="http://localhost:11434",

# )

# MODEL = "llama3.1"


OLLAMA_HOST = "http://localhost:11434"
# MODEL = "qwen2.5-coder:32b"
MODEL = "qwen2.5:32b"

def chat_with_ollama(messages, tools=None):
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "seed": 101,
            "temperature": 0
        }
    }
    if tools:
        payload["tools"] = tools

    # print("================ LLM-payload-START ===========")
    # print(json.dumps(payload,indent=2))
    # print("================ LLM-payload-END ===========")
    
    response = requests.post(url, json=payload)
    # print("================ LLM response-START ===========")
    # print(json.dumps(response.json(),indent=2))
    # print("================ LLM response-END ===========")
    if response.status_code == 200:
        
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")

# Define functions

def chatAssist_ollama():
        
    def handle_tool_call(tool, llm_to_use):
        function_name = tool.get("function", {}).get("name")
        arguments = tool.get("function", {}).get("arguments", {})

        if not function_name:
            return {"role": "tool", "content": "Error: Missing function name.", "name": "unknown"}

        if function_name == "sql_agent":
            response_content = sql_agent(arguments.get("query"), model=llm_to_use)
        elif function_name == "place_order":
            response_content = place_order(arguments.get("customer_id"), arguments.get("order_items"))
        elif function_name == "cancel_order":
            response_content = cancel_order(arguments.get("order_id"))
        else:
            response_content = f"Error: Unknown function '{function_name}'."

        return {
            "role": "tool", 
            "content": str(response_content), 
            "name": function_name
        }

    # Tools
    sql_agent_function = {
        "type": "function",
        "function": {
            "name": "sql_agent",
            "description": "call this function when you want to query inventory. for example list all products available",
            "parameters": {
            "type": "object",
            "properties": {
                "query": {
                "type": "string",
                "description": "Natural language query being converted to SQL and data fetched from db"
                }
            },
            "required": ["query"],
            }
        }
    }

    place_order_function = {
        "type": "function",
        "function": {
            "name": "place_order",
            "description": "Place a new order for electrical components",
            "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                "type": "string",
                "description": "Unique identifier for the customer"
                },
                "order_items": {
                "type": "array",
                "description": "List of products and their quantities",
                "items": {
                    "type": "object",
                    "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "Unique identifier for the product"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of items to order"
                    }
                    },
                    "required": ["product_id", "quantity"]
                }
                }
            },
            "required": ["customer_id", "order_items"]
            }
        }
    }

    cancel_order_function = {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": "cancel an existingly placed order for a product",
            "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                "type": "string",
                "description": "unique id of the existing order placed by the particular customer"
                }
            },
            "required": ["order_id"],
            }
        }
    }

    tools = [
        sql_agent_function,
        place_order_function,
        cancel_order_function
        ]

    def chat_interface(message, history,llm):
        # system_message = """
        #     You are a helpful assistant for an Electronic distributor company. 
        #     Give short, courteous answers, no more than 1 sentence.
        #     Before placing an order, depict a bill representation as a table.
        #     After placing an order, use creative emoji and end gracefully.
        #     Before canceling an order, depict order details as a table fetched from db.
        #     Always be accurate. If you don't know the answer, say so. and do not assume anything
        # """
        system_message = prompts["ollama_qwen_v1"]
        messages = [{'role': 'system', 'content': system_message}] + history + [{'role': 'user', 'content': message}]

        response = chat_with_ollama(messages,tools)
        print(f"\n====BEGIN-Chat-{MODEL}=======\n")

        if "message" in response:
            message = response["message"]
            print("\nMessage:\n", message["content"])

            if "tool_calls" in message and message["tool_calls"]:
                print("\nTool calls: \n", message["tool_calls"])
                for tool in message["tool_calls"]:
                    tool_response = handle_tool_call(tool, llm_to_use=MODEL)
                    print("\nTool Response: \n", tool_response)

                    messages.append(message)  # Append the original response
                    messages.append(tool_response)  # Append tool response

                # Call API again with updated messages
                response = chat_with_ollama(messages)

            if "message" in response:
                print("\nResponse:\n", response["message"]["content"])

                print("\n====END-Chat=======\n")
        return response["message"]["content"]

    #EXPERIMENTING
    with gr.Blocks(fill_height=True) as chat_assist:
        gr.Markdown("### Multi-LLM Chat Interface")

        # Store the selected model in state
        selected_model = gr.State("qwen2.5-coder:14b")

        # Dropdown for LLM model selection
        model_selector = gr.Dropdown(
            choices=["llama3.1","llama3.1:70b" ,"deepseek-r1:32b","deepseek-r1:8b","mistral","qwen2.5:14b","qwen2.5","qwen2.5-coder:14b"],
            label="Select LLM Model",
            # value="GPT-4",
            interactive=True
        )

        # Update selected_model dynamically
        def update_model(selected):
            selected_model.value = selected  # Update the state directly

        model_selector.change(
            update_model,
            inputs=[model_selector],
        )

        # Chat interface using closures to access the model
        def chat_with_selected_model(messages,history):
            return chat_interface(messages,history, selected_model.value)

      
        gr.ChatInterface(
            fn=chat_with_selected_model,
            type="messages",
            examples=["What can you assist?", "Hi", "View all products"],
            fill_height=True,
            
        )

    chat_assist.launch(share=True)

    # OLD - WAY
    # gr.ChatInterface(
    #     fn=chat_interface,
    #     additional_inputs=[
    #         gr.Dropdown(
    #         ["cat", "dog", "bird"], label="animal", info="Will add more animals later!"
    #     )
    #     ],
    #     type="messages",
    #     title="Chat bot",
    #     # examples=["What can you assist", "Hi", "view all products"],
    #     ).launch()


if __name__ == '__main__':
    chatAssist_ollama()

