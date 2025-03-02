import os
import json
from dotenv import load_dotenv
import gradio as gr
from ollama import  Client
from db_setup.place_order_v2 import place_order
from db_setup.cancel_order import cancel_order
from sql_agent.sql_agent_v2 import sql_agent
from .prompts import prompts

# Initialization
load_dotenv(override=True)

ollama_client = Client(
    host ="http://localhost:11434",

)

MODEL = "llama3.1"




# Define functions

def chatAssist_ollama():
        
    def handle_tool_call(tool,llm_to_use):
        function_name = tool.function.name
        arguments = tool.function.arguments
        response_content = ""

        if function_name == "sql_agent":
            response_content = sql_agent(arguments.get('user_query'),model=llm_to_use)
        elif function_name == "place_order":
            customer_id = arguments.get('customer_id')
            order_items = arguments.get('order_items')
            response_content = place_order(customer_id, order_items)
        elif function_name == "cancel_order":
            order_id = arguments.get('order_id')
            response_content = cancel_order(order_id)
        
        return {
                'role': 'tool', 
                'content': str(response_content),
                'name': tool.function.name
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
            "user_query": {
              "type": "string",
              "description": "Natural language query being converted to SQL and data fetched from db"
            }
          },
          "required": ["user_query"],
          "additionalProperties": False
        }
      }
    }

    place_order_function = {
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

    cancel_order_function = {
            "name": "cancel_order",
            "description": "cancel an existingly placed order for a product",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "unique id of the existing order placed by the particular customer",
                    },
                },
                "required": ["order_id"],
                "additionalProperties": False
            }
        }

    tools = [
        {"type": "function", "function": sql_agent_function},
        {"type": "function", "function": place_order_function},
        {"type": "function", "function": cancel_order_function}

        ]

    def chat_interface(message, history,llm):
        system_message = """
            You are a helpful customer support chatbot assistant for an electronic distributor company named CED. 
            Follow these rules:
                - You must assist the user in a polite and kind way.
                - If the user ask for anything unrelated to electronics 
                - If any user statement is unclear ask for a clear statement to contiune the conversation.
                
                -use provided tools only when necessary
                    Available tools:
                        1. `sql_agent`:call this function when you want to fetch details from database. for example "list all products available" and not for general greeting like for example "hi"
                        2. `place_order`:To Place a new order 
                        3. `cancel_order`:To cancel an existingly placed order for a product
                -Give short, courteous answers, no more than 1 sentence. 
                -Before placing an order, display a bill representation as a table. 
                -After placing an order, use creative emojis and end gracefully. 
                -Before canceling an order, represent the order details fetched from db as a table. 
                -Always be accurate. If you don't know the answer, say so. 
                -Do not assume anything on your own.
        """
        # system_message = prompts["ollama_llama_prompt"]
        messages = [{'role': 'system', 'content': system_message}] + history + [{'role': 'user', 'content': message}]

        response = ollama_client.chat(
            model=MODEL,
            messages=messages,
            tools=tools,
        )
        print(f"\n====BEGIN-Chat-{llm}=======\n")
        print("\nMessage:\n",message)
        if response.message.tool_calls:
            print("\nTool calls: \n", response.message.tool_calls)
            for tool in response.message.tool_calls:
                tool_response = handle_tool_call(tool,llm_to_use=llm)
                print("\nTool Response: \n", tool_response)
                messages.append(response.message)
                messages.append(tool_response)
            
            response = ollama_client.chat(
                model=MODEL, 
                messages=messages,
                
            )

        print("\nResponse:\n", response.message.content) 
        print("\n====END-Chat=======\n")
        return response.message.content

    #EXPERIMENTING
    with gr.Blocks() as chat_assist:
        gr.Markdown("### Multi-LLM Chat Interface")

        # Store the selected model in state
        selected_model = gr.State("llama3.1")

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

        # Chat interface with state
        gr.ChatInterface(
            # fn=lambda msg, history: chat_interface(msg, history, model_state.value),
            fn=chat_with_selected_model,
            type="messages",
            examples=["What can you assist?", "Hi", "View all products"],
            fill_height=True
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

