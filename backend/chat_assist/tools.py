


def get_tools():
    '''
        Tools are the functions that the chatbot can perform.
        The chatbot can call these functions to perform specific tasks.
    '''

   
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
                "description": "Unique identifier for the customer, will be provided as context"
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

    # Tax check function - just keep the function definition as it's already in place
    check_tax_rate_function = {
        "type": "function",
        "function": {
            "name": "check_tax_rate",
            "description": "Check the tax rate for a specific state",
            "parameters": {
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "The state for which the tax rate is checked"
                    }
                },
                "required": ["state"],
            }
        }
    }

    tools = [
        sql_agent_function,
        place_order_function,
        cancel_order_function,
        check_tax_rate_function
        ]
    
    return tools