import dspy
from typing import Literal 


# Configure DSPy Language Model
# lm = dspy.LM("openai/gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))

def intentClassifier(model="llama3.1",query=""):
    lm = dspy.LM(f"ollama_chat/{model}", endpoint="http://localhost:11434")
    dspy.configure(lm=lm)

    class UserQueryProcessor(dspy.Signature):
        """Analyze whether the provided query's intent is to query the database to get details of product stock, order or place order or cancel order"""
        
        user_statement: str = dspy.InputField(desc="User's query statement.")
        answer: Literal["get_db_data","place_order","cancel_order","general"] = dspy.OutputField(
            desc="Indicates whether the query is related to database retrieval."
        )

    predictor = dspy.Predict(UserQueryProcessor)
    response = predictor(user_statement=query)

    return response



if __name__ == "__main__":

    # List of test queries
    queries = [
        "hi",
        "how can i assist you?",
        "show me details on stocks available?",
        "I want to place an order",
        "How many customers placed orders last week?",
        "What is the price of the latest iPhone?",
        "Cancel my last order",
        "Show me the list of available products",
        "Tell me a joke",
        "How many orders did supplier X fulfill last month?",
    ]

    # Process and print results
    print("\nQuery Processing Results:\n" + "="*30)
    for query in queries:
        response = intentClassifier(query=query)

        print(f"STATEMENT: {query}\nDATABASE QUERY: {response.answer}\n" + "-"*30)