import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
from db_setup.place_order_v2 import place_order
from db_setup.cancel_order import cancel_order
from sql_agent.sql_agent_v2 import sql_agent

# Initialization

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
MODEL = "gpt-4o-mini"
openai = OpenAI()

# As an alternative, if you'd like to use Ollama instead of OpenAI
# Check that Ollama is running for you locally (see week1/day2 exercise) then uncomment these next 2 lines
# MODEL = "llama3.2"
# openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')


def chatAssist():


    system_message = "You are a helpful assistant for an Electronic distributor company. \n"
    system_message += "Give short, courteous answers, no more than 1 sentence. \n"
    system_message += "Before placing a order dipict a bill representaion as a table\n"
    system_message += "After placing a order use creative emoji and end greacefully\n"
    system_message += "Before canceling a order dipict a order detail as a table\n"
    system_message += "Always be accurate. If you don't know the answer, say so."


    sql_agent_function = {
        "name": "sql_agent",
        "description": "call this function when you want to query inventory. for example list all products available",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query being converted to SQL and data fetched from db",
                },
            },
            "required": ["query"],
            "additionalProperties": False
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


    def handle_tool_call(message):
        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        response_content=""
        
        if function_name == "place_order":
            customer_id = arguments.get('customer_id')
            order_items = arguments.get('order_items')
            # Here you would typically call your actual order processing logic
            # For now, returning a mock response
            response_content =  place_order(customer_id,order_items)
        
        elif function_name == "cancel_order":
            order_id = arguments.get('order_id')
            # Here you would typically call your order cancellation logic
            response_content = cancel_order(order_id)
        
        elif function_name == "sql_agent":
            query = arguments.get('query')
            # Here you would typically call your SQL agent
            response_content = sql_agent(query)
        
        response = {
            "role": "tool",
            "content": json.dumps(response_content),
            "tool_call_id": tool_call.id
        }

        print("\n\n From Handle tool call - response")
        print(response)

        return response


    def chat(message, history):
        messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
        response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)

        print("Message list:")
        print(messages)
        print(response)
        
        
        if response.choices[0].finish_reason=="tool_calls":
            message = response.choices[0].message
            response = handle_tool_call(message)
            messages.append(message)
            messages.append(response)
            response = openai.chat.completions.create(model=MODEL, messages=messages)

            print("\n\nMessage list:")
            print(messages)
            print(response)
        
        return response.choices[0].message.content



    gr.ChatInterface(fn=chat, type="messages").launch()



if __name__ == "__main__":
    chatAssist()