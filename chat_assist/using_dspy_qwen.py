import os
from pprint import pprint
import chromadb
import json
import dspy
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from db_setup.place_order_v2 import place_order
from db_setup.cancel_order import cancel_order
from sql_agent.sql_agent_v2 import sql_agent

load_dotenv()




class ChatbotAssistant(dspy.Signature):
    """You are helpful chatbot assistant for Electronic parts distributor company named CED"""
    question: str = dspy.InputField()
    answer: str = dspy.OutputField(
        desc="Answer to the user's question based on the query being executed"
    )


chat_module = dspy.ReAct(
    ChatbotAssistant,
    tools=[sql_agent,place_order,cancel_order],
)


def chat_bot(user_query: str,model=None):
    # Configure DSPy Language Model
    # lm = dspy.LM("openai/gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
    lm = dspy.LM(f"ollama_chat/{model}", endpoint="http://localhost:11434")
    dspy.configure(lm=lm)

    
    response = chat_module(question=user_query)

    
    print("\nMESSAGE:\n", user_query)
    print("\n\n")
    print(response)
    print("\n\n")

    return response.answer


if __name__ == "__main__":
    # main()
    # user_query = " list me all the customers names"
    # user_query = (
    #     "list the stock quantity of product id 1 with price and it's category name"
    # )
    # # user_query = "what is the total amount for customer alice cooper"
    # # user_query = "what are the products purchased by customer bob martin"
    # # user_query = "what is the supplier name of product id '1' and give his address"
    # # user_query = "what is the supplier name of product Electrical Socket and give his address also state the category of the product list the customer name purchased the product and total amount for overall order"
    # user_query = "delete the customers table"
    user_query = "what can you assist me with"
    
    response = chat_bot(user_query,model="qwen2.5:14b")

    print(response)


