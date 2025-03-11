from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str = ""
    history: list = []


class OllamaChatRequest(BaseModel):
    user_msg: str = ""
    history: list = []
    model:str = "qwen2.5:32b"
