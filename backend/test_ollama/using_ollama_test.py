import requests
import json


def chat_with_ollama(payload):

    OLLAMA_HOST = "http://localhost:11434"
    MODEL = "qwen2.5-coder:14b" 

    url = f"{OLLAMA_HOST}/api/chat"
    # payload = {
    #     "model": MODEL,
    #     "messages": messages,
    #     "stream": False
    # }
    # if tools:
    #     payload["tools"] = tools
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")


if __name__ == "__main__":
    payload = {
    "model": "qwen2.5-coder:14b",
    "tools": [
        {
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
        },
        {
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
        },
        {
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
    ],
    "messages": [
        {
        "role": "system",
        "content": "You are a helpful assistant for an Electronic distributor company. Give short, courteous answers, no more than 1 sentence. Before placing an order, depict a bill representation as a table. After placing an order, use creative emoji and end gracefully. Before canceling an order, depict order details as a table fetched from db. Always be accurate. If you don't know the answer, say so. and do not assume anything"
        },
        {
        "role": "user",
        "content": ""
        }
    ],
    "stream": False
    }

    response  = chat_with_ollama(payload)
    print("Response:\n" + json.dumps(response, indent=4))