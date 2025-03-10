from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from ..db_setup.place_order_v2 import place_order
from ..db_setup.cancel_order import cancel_order
from ..sql_agent.sql_agent_v2 import sql_agent
from ..chat_assist.prompts import prompts
from pprint import pprint

origins = [
    "http://localhost",
    "http://localhost:5174",
]

# Load environment variables
load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise RuntimeError("OpenAI API Key not set")

app = FastAPI()
openai = OpenAI()
MODEL = "gpt-4o-mini"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list = []

def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    response_content = ""
    
    if function_name == "place_order":
        response_content = place_order(arguments.get('customer_id'), arguments.get('order_items'))
    elif function_name == "cancel_order":
        response_content = cancel_order(arguments.get('order_id'))
    elif function_name == "sql_agent":
        response_content = sql_agent(arguments.get('query'))
    
    return {"role": "tool", "content": json.dumps(response_content), "tool_call_id": tool_call.id}

@app.post("/chat")
def chat(chat_request: ChatRequest):
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
    
    # system_message=prompts["ollama_qwen_v1"]
    
    messages = [{"role": "system", "content": system_message}] + chat_request.history + [{"role": "user", "content": chat_request.message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages)
    
    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        response = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        response = openai.chat.completions.create(model=MODEL, messages=messages)

    print("============== CHAT-START ===============")
    print({
        "message":chat_request.message,
        "history":chat_request.history
    })
    print("============== CHAT-END ================")
    
    return {"response": response.choices[0].message.content}


@app.get("/test")
def test():
    return {"status":200,"msg":"hello"}
