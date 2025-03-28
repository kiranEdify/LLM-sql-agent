from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ..chat_assist import ollama_chat_assist
from ..data_model.request_payload import  OllamaChatRequest


# configuring the origins
# origins = [
#     "http://localhost",
#     "http://localhost:5174",
# ]

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# @app.post("/chat/openai")
# def chat(chat_request: ChatRequest):
   
#     try:
#         response = openai_chat_assist(chat_request)
#         return {
#             "status": 200,
#             "response": response
#         }
#     except Exception as e:
#         return {
#             "status": 500,
#             "error": str(e)
#         }

@app.post("/chat")
def chat(chat_request: OllamaChatRequest):
   
    try:
        response = ollama_chat_assist(chat_request)
        return {
            "status": 200,
            "response": response
        }
    except Exception as e:
        return {
            "status": 500,
            "error": str(e)
        }



@app.get("/test")
def test():
    return {"status": 200, "msg": "hello"}