import os
import json
from dotenv import load_dotenv
import gradio as gr
from ollama import Client
from db_setup.place_order_v3 import place_order
from db_setup.cancel_order import cancel_order
from db_setup.tax_check_v3 import check_tax_rate, store_tax_rate  # Import the tax_check function
from sql_agent.sql_agent_v2 import sql_agent
import prompts
import requests
import chromadb
from chromadb.config import Settings
import json
import threading
from flask import Flask, jsonify, request
from kafka import KafkaConsumer, TopicPartition

# Initialization
load_dotenv(override=True)


OLLAMA_HOST = "http://localhost:11434"

def initialize_chroma():
    client = chromadb.PersistentClient(path="./chroma_db")
    try:
        collection = client.get_collection(name="sql_schema")  # Try to get collection
        print("✅ Collection 'sql_schema' found.")
        return collection
    except chromadb.errors.InvalidCollectionException:
        print("⚠️ Collection 'sql_schema' not found. Creating a new one...")
        return client.create_collection(name="sql_schema")  # Create if not exists

collection = initialize_chroma()

app = Flask(__name__)

def chat_with_ollama(messages, tools=None, model="qwen2.5:7b"):
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools

    print("================ LLM-payload-START ===========\n")
    print(json.dumps(payload, indent=2))
    print("================ LLM-payload-END ===========\n")

    response = requests.post(url, json=payload)
    print("================ LLM response-START ===========\n")
    print(json.dumps(response.json(), indent=2))
    print("================ LLM response-END ============\n")
    if response.status_code == 200:
        return response.json()
    else:
        error_message = f"LLM API Error: {response.status_code}, {response.text}.\n Clear message history or refresh and try again with different LLM"
        print(f"LLM API Error: {error_message}\n Clear message history or refresh and try again with different LLM")
        return {"message": {"role": "assistant", "content": error_message}}


# Define functions
def chatAssist_ollama():

    def handle_tool_call(tool, llm_to_use):
        function_name = tool.get("function", {}).get("name")
        arguments = tool.get("function", {}).get("arguments", {})

        if not function_name:
            return {"role": "tool", "content": "Error: Missing function name.", "name": "unknown"}

        print("\n====== Tool call - START ==========\n")
        print(f"function/tool Name: {function_name}")
        print(f"arguments : {arguments}")
        if function_name == "sql_agent":
            response_content = sql_agent(arguments.get("query"), model=llm_to_use)
        elif function_name == "place_order":
            response_content = place_order(arguments.get("customer_id"), arguments.get("order_items"))
        elif function_name == "cancel_order":
            response_content = cancel_order(arguments.get("order_id"))
        elif function_name == "check_tax_rate":
            # Call the actual tax_check function here
            response_content = check_tax_rate(arguments.get("state"))  # Invoke the function
        else:
            response_content = f"Error: Unknown function '{function_name}'."
        print("\n====== Tool call - END ==========\n")

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
        check_tax_rate_function  # Add the tax_check function as a tool
    ]

    def chat_interface(user_msg, history, model="qwen2.5"):
        system_message = prompts.ollama_qwen_v1
        messages = [{'role': 'system', 'content': system_message}] + history + [{'role': 'user', 'content': user_msg}]

        response = chat_with_ollama(messages, tools, model=model)
        print(f"\n====BEGIN-Chat-{model}=======\n")

        if "message" in response:
            message = response["message"]
            print("\nMessage:\n", user_msg)

            if "tool_calls" in message and message["tool_calls"]:
                for tool in message["tool_calls"]:
                    tool_response = handle_tool_call(tool, llm_to_use=model)
                    messages.append(message)  # Append the original response
                    messages.append(tool_response)  # Append tool response

                # Call API again with updated messages
                response = chat_with_ollama(messages, model=model)

            if "message" in response:
                print("\nResponse:\n", response["message"]["content"])

                print("\n====END-Chat=======\n")
        return response["message"]["content"]

    # EXPERIMENTING
    with gr.Blocks(fill_height=True) as chat_assist:
        gr.Markdown("### Multi-LLM Chat Interface")

        # Store the selected model in state
        selected_model = gr.State("qwen2.5")

        # Dropdown for LLM model selection
        model_selector = gr.Dropdown(
            choices=["qwen2.5:32b","qwen:7b", "qwen2.5:72b", "gemma2:27b", "falcon:40b", "llama3.1", "llama3.1:70b", "deepseek-r1:32b", "deepseek-r1:8b", "mistral", "qwen2.5:14b", "qwen2.5", "qwen2.5-coder:14b"],
            label="Select LLM Model",
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
        def chat_with_selected_model(messages, history):
            return chat_interface(messages, history, selected_model.value)

        gr.ChatInterface(
            fn=chat_with_selected_model,
            type="messages",
            examples=["What can you assist?", "Hi", "View all products", "Check tax for California"],  # Added example for tax check
            fill_height=True,
        )

    chat_assist.launch(share=True)

def consume_kafka_messages():
    topic = 'sa.edify.dbo.sql_query_log'
    partition = 0 
    
    print(f"\n=== Starting Kafka Consumer ===")
    print(f"Connecting to Kafka at localhost:29092")
    print(f"Topic: {topic}, Partition: {partition}")

    try:
        consumer = KafkaConsumer(
            bootstrap_servers='localhost:29092',
            enable_auto_commit=False,
            value_deserializer=lambda x: x.decode('utf-8'),
            group_id='chat_assist_group',  # Add a consumer group ID
            auto_offset_reset='earliest'    # Start from earliest if no offset is stored
        )
        print("✅ Successfully created Kafka consumer")

        tp = TopicPartition(topic, partition)
        consumer.assign([tp])
        print("✅ Successfully assigned to topic partition")

        beginning_offset = consumer.beginning_offsets([tp])[tp]
        latest_offset = consumer.end_offsets([tp])[tp]
        print(f"📊 Kafka Partition '{topic}-0' Offsets: Earliest={beginning_offset}, Latest={latest_offset}")

        start_offset = max(113, beginning_offset)
        if start_offset >= latest_offset:
            print(f"⚠️ Offset {start_offset} is out of range! No new messages available.")
            return

        consumer.seek(tp, start_offset)
        print(f"✅ Kafka Consumer started listening from offset {start_offset} on topic '{topic}'...")

        while True:  # Add continuous polling loop
            try:
                # Poll for messages with a timeout
                messages = consumer.poll(timeout_ms=1000)
                if not messages:
                    print("⏳ No messages received in this poll, continuing...")
                    continue

                for tp, msgs in messages.items():
                    for message in msgs:
                        print(f"\n📥 Received message:")
                        print(f"Offset: {message.offset}")
                        print(f"Value: {message.value}")
                        process_kafka_message(message.value)

            except Exception as e:
                print(f"❌ Error while polling messages: {str(e)}")
                continue

    except Exception as e:
        print(f"❌ Failed to create Kafka consumer: {str(e)}")
        raise

def get_table_info_from_ollama(query_text):
    prompt = f"""
    You are an AI that extracts table names, column modifications, and relationships from SQL queries.
    Given the following SQL query:
    "{query_text}"
    
    Return a JSON object in this format:
    {{
        "table_name": "<table_name>",
        "add_columns": ["<column1>", "<column2>"], 
        "drop_columns": ["<column3>", "<column4>"],
        "relationships": [
            {{
                "table1": "<table_name>",
                "table2": "<referenced_table>",
                "column1": "<column_name>",
                "column2": "<referenced_column>",
                "type": "foreign_key"
            }}
        ]
    }}

    Rules:
    - For CREATE TABLE, list all columns in add_columns
    - For ALTER TABLE ADD, list new columns in add_columns
    - For ALTER TABLE DROP, list removed columns in drop_columns
    - For DROP TABLE, return table_name with empty lists
    - Include any FOREIGN KEY constraints in relationships
    - Return strictly valid JSON format
    """

    try:
        messages = [{"role": "user", "content": prompt}]
        response = chat_with_ollama(messages, model="qwen2.5")
        
        if "message" in response and "content" in response["message"]:
            content = response["message"]["content"]
            # Clean up the response to ensure it's valid JSON
            cleaned_response = content.strip("```json").strip("```").strip()
            cleaned_response = cleaned_response[:cleaned_response.rfind("}") + 1]
            result = json.loads(cleaned_response)
            return (
                result["table_name"], 
                result["add_columns"], 
                result["drop_columns"],
                result.get("relationships", [])
            )
        else:
            print("Invalid response format from Ollama")
            return None, None, None, []
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return None, None, None, []

def process_kafka_message(message):
    data = json.loads(message)
    after = data.get("after", {})
    event_type = after.get("event_type", "")
    query_text = after.get("query_text", "")

    if not query_text:
        print("Skipping message: query_text is empty or None")
        return

    table_name, add_columns, drop_columns, relationships = get_table_info_from_ollama(query_text)

    if not table_name:
        print(f"Skipping message: Could not extract table from query: {query_text}")
        return

    if event_type == "CREATE_TABLE":
        add_table_schema(collection, table_name, add_columns)
        # Add relationships if any
        for rel in relationships:
            add_relationship(
                collection,
                rel["table1"],
                rel["table2"],
                rel["column1"],
                rel["column2"],
                rel["type"]
            )
    elif event_type == "ALTER_TABLE":
        alter_table_schema(collection, table_name, add_columns, drop_columns)
        # Add new relationships if any
        for rel in relationships:
            add_relationship(
                collection,
                rel["table1"],
                rel["table2"],
                rel["column1"],
                rel["column2"],
                rel["type"]
            )
    elif event_type == "DROP_TABLE":
        drop_table_schema(collection, table_name)

def drop_table_schema(collection, table_name):
    # Delete both table and columns entries
    table_id = f"{table_name}_table"
    columns_id = f"{table_name}_columns"
    collection.delete(ids=[table_id, columns_id])
    print(f"Schema for table '{table_name}' dropped successfully.")

def get_table_schema(collection, table_name):
    # Query only for the specific table's columns with minimal fields
    results = collection.get(
        where={
            "$and": [
                {"type": {"$eq": "column"}},
                {"table": {"$eq": table_name}}
            ]
        },
        include=['metadatas']  # Only fetch metadata, we don't need documents
    )
    
    if results["metadatas"]:
        metadata = results["metadatas"][0]
        return {
            "table_name": table_name,
            "columns": metadata["columns"].split(", ")
        }
    return None

def alter_table_schema(collection, table_name, add_columns=[], drop_columns=[]):
    schema = get_table_schema(collection, table_name)
    if schema:
        current_columns = set(schema["columns"])
        updated_columns = (current_columns | set(add_columns)) - set(drop_columns)
        
        # Update columns entry
        columns_id = f"{table_name}_columns"
        columns_text = f"Columns: {', '.join(updated_columns)}"
        columns_metadata = {
            "type": "column",
            "table": table_name,
            "columns": ", ".join(updated_columns)
        }
        
        collection.update(
            ids=[columns_id],
            documents=[columns_text],
            metadatas=[columns_metadata]
        )
        print(f"Schema for table '{table_name}' altered successfully: Added {add_columns}, Removed {drop_columns}")
    else:
        print(f"Table '{table_name}' not found. Cannot alter schema.")

def add_relationship(collection, table1, table2, column1, column2, relationship_type="foreign_key"):
    relationship_id = f"{table1}_{table2}_relationship"
    relationship_text = f"Relationship: {table1}.{column1} → {table2}.{column2}"
    relationship_metadata = {
        "type": "relationship",
        "table1": table1,
        "table2": table2,
        "column1": column1,
        "column2": column2,
        "relationship_type": relationship_type
    }
    
    collection.add(
        ids=[relationship_id],
        documents=[relationship_text],
        metadatas=[relationship_metadata]
    )
    print(f"Relationship between {table1} and {table2} added successfully.")
    
def add_table_schema(collection, table_name, columns):
    # Create table entry
    table_id = f"{table_name}_table"
    table_text = f"table: {table_name}"
    table_metadata = {
        "type": "table",
        "table_name": table_name
    }
    
    # Create columns entry
    columns_id = f"{table_name}_columns"
    columns_text = f"Columns: {', '.join(columns)}"
    columns_metadata = {
        "type": "column",
        "table": table_name,
        "columns": ", ".join(columns)
    }
    
    collection.add(
        ids=[table_id, columns_id],
        documents=[table_text, columns_text],
        metadatas=[table_metadata, columns_metadata]
    )
    print(f"Schema for table '{table_name}' added successfully.")

def start_kafka_consumer():
    print("\n=== Starting Kafka Consumer Thread ===")
    try:
        kafka_thread = threading.Thread(target=consume_kafka_messages, daemon=True)
        kafka_thread.start()
        print("✅ Kafka consumer thread started successfully")
    except Exception as e:
        print(f"❌ Failed to start Kafka consumer thread: {str(e)}")
        raise


if __name__ == '__main__':
    print("\n=== Starting Application ===")
    try:
        start_kafka_consumer()
        print("Starting Gradio interface...")
        chatAssist_ollama()
    except Exception as e:
        print(f"❌ Application failed to start: {str(e)}")
        raise
