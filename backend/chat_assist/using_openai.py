
import json
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from ..db_setup.place_order_v2 import place_order
from ..db_setup.cancel_order import cancel_order
from ..sql_agent.sql_agent_v2 import sql_agent
from ..chat_assist.prompts import prompts
from ..utils.loggers import log_message  # Import the logging function


# Load environment variables
load_dotenv(override=True)

openai = OpenAI()
MODEL = "gpt-4o-mini"

openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise RuntimeError("OpenAI API Key not set")


class ChatRequest(BaseModel):
        message: str
        history: list = []


def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    response_content = ""

    log_message("TOOL-CALL-START", f"function_name: {function_name}\narguments: {arguments}")

    if function_name == "place_order":
        response_content = place_order(arguments.get('customer_id'), arguments.get('order_items'))
    elif function_name == "cancel_order":
        response_content = cancel_order(arguments.get('order_id'))
    elif function_name == "sql_agent":
        response_content = sql_agent(arguments.get('query'))

    log_message("TOOL-CALL-ENDED", f"response_content: {response_content}")

    return {"role": "tool", "content": json.dumps(response_content), "tool_call_id": tool_call.id}


def openai_chat_assist(chat_request: ChatRequest):
    
    log_message("CHAT-Payload", {
    "message": chat_request.message,
    "history": chat_request.history
    })

    system_message = ("You are a helpful assistant for an Electronic distributor company named 'CED.inc' "
                      "When asked to list products,stocks,supplier use the appropriate tools/functions given"
                      "Give short, courteous answers, no more than 1 sentence. "
                      "Before placing an order depict a bill representation as a table. "
                      "After placing an order, use creative emoji and end gracefully. "
                      "Before canceling an order, depict an order detail as a table. "
                      "Always be accurate. If you don't know the answer, say so. "
                      "Do not assume or generate data, always respond with factual data."
                      "response format: html"
                      )

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

    messages = [{"role": "system", "content": system_message}] + chat_request.history + [{"role": "user", "content": chat_request.message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)

    if response.choices[0].finish_reason == "tool_calls":
        log_message("TOOL-CALL-START", f"tool-call-msg:\n{response.choices[0].message}")

        message = response.choices[0].message
        response = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        response = openai.chat.completions.create(model=MODEL, messages=messages)

    log_message("CHAT-Response", response.choices[0].message.content)

    return  response.choices[0].message.content