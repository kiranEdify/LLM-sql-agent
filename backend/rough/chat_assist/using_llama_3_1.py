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

        if function_name == "get_inventory_details":
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
    "name": "get_inventory_details",
    "description": """
        This function **retrieves inventory data** from the database.(i.e product details,supplier details,stock details,order details)
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": """
                       user question realated to the inventory,supplier,order details.
                    """,
                },
            },
            "required": ["user_query"],
            "additionalProperties": False
        }
    }



    place_order_function = {
        "name": "place_order",
        "description": """
            Use this function **only** when the user explicitly requests to place an order.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Unique identifier for the customer placing the order."
                },
                "order_items": {
                    "type": "array",
                    "description": "A list of products and their quantities for the order.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "integer",
                                "description": "The unique identifier of the product to order."
                            },
                            "quantity": {
                                "type": "integer",
                                "description": "The number of units to order."
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
        "description": """
            Use this function **only** when the user requests to cancel an existing order.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The unique identifier of the order to cancel."
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
            You are a helpful AI chat  assistant for an electronic distributor company. Follow these rules strictly:

            # CHAT RULES:
                1. for general talk do not use tools provided , response with your knowledge in a polite manner
                    eg. user : hi
                        you : Hello , how can i assist you
                2. Keep the response short 
                2. Do not assume or hallucinate always generate response with data provided
                3. if unclear ask follow up question to the user or simple state 'Please provide more details!'

            # RULES FOR PLACING ORDER:
                1. Before placing an order list the items with price and units the customer ordered in a table format
                2. And ask for confirmation before placing the order

            # RULES FOR CANCELING ORDER:
                1. Before canceling an order list the items with price and units the customer ordered in a table format
                2. And ask for confirmation before canceling the order

            # TOOL CALL RULES:
                Do not be tempted to use tools always, use it only when it is absolutely needed to fulfil the user query.

                **available tools:
                    1. `get_inventory_details` - used to get product,stock,order,supplier details.(eg. list me all products available)
                    2. `place_order` - used to place order. (eg. i want to place an order)
                    3. `cancel_order` -  used to cancel order. (eg. i want to cancel an order)

        """
        # system_message = prompts["ollama_llama_prompt"]
        messages = [{'role': 'system', 'content': system_message}] + history + [{'role': 'user', 'content': message}]

        response = ollama_client.chat(
            model=MODEL,
            messages=messages,
            tools=tools,
        )
        print("\n====BEGIN-Chat=======\n")
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
            choices=["llama3.1","llama3.1:70b" ,"deepseek-r1:32b","deepseek-r1:8b","mistral"],
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

