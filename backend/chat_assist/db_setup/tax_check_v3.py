from sqlalchemy import create_engine, text
import chromadb
from sentence_transformers import SentenceTransformer
import json
import requests
import re

# Initialize ChromaDB with persistence
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="sql_schema")  # Use the collection where tax info is stored

# Initialize the Sentence Transformer Model
model = SentenceTransformer('all-MiniLM-L6-v2')

# LLM API Configuration
OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "qwen2.5:32b"

def create_embeddings(text):
    return model.encode([text])

def store_tax_rate(state, tax_rate):
    """Stores the retrieved tax rate into the SQLite database."""
    state = state.lower()  # Ensure state is always stored in lowercase
    tax_rate = float(tax_rate)  # Ensure tax rate is a float
    engine = create_engine("sqlite:///electrical_parts.db", echo=True)
    try:
        with engine.begin() as connection:
            print(f"Storing tax rate in database: {state} -> {tax_rate * 100}%")
            connection.execute(
                text("INSERT INTO taxes (state, tax_rate) VALUES (:state, :tax_rate) "
                     "ON CONFLICT(state) DO UPDATE SET tax_rate = :tax_rate"),
                {"state": state, "tax_rate": tax_rate},
            )
            print(f"Successfully stored tax rate for {state}: {tax_rate * 100}%")

            # Confirm the tax rate was stored correctly
            stored_result = connection.execute(
                text("SELECT tax_rate FROM taxes WHERE state = :state"),
                {"state": state},
            ).fetchone()
            print(f"Confirmed tax rate in DB: {stored_result[0] * 100}%")
    except Exception as e:
        print(f"Failed to store tax rate in database: {str(e)}")

def extract_tax_rate_from_llm(state, context):
    """Uses LLM to extract the specific tax rate for the given state from the provided text."""
    url = f"{OLLAMA_HOST}/api/chat"
    messages = [
        {"role": "system", "content": "Extract only the numerical tax rate for the given state from the provided text. Return only the tax rate in percentage format."},
        {"role": "user", "content": f"Given the following information, extract only the tax rate for {state}: {context}"}
    ]
    payload = {"model": MODEL_NAME, "messages": messages, "stream": False}
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        llm_response = response.json().get("message", {}).get("content", "")
        print(f"LLM Response: {llm_response}")
        
        # Extract tax rate using broader regex
        match = re.search(rf"{state}.*?(\d+\.?\d*)%", llm_response, re.IGNORECASE) or re.search(r"(\d+\.?\d*)%", llm_response)
        print(f"Regex match result: {match}")
        if match:
            try:
                extracted_tax_rate = float(match.group(1)) / 100  # Normalize percentage format
                print(f"Extracted tax rate for {state}: {extracted_tax_rate * 100}%")
                return extracted_tax_rate
            except ValueError:
                print("Failed to extract valid tax rate from LLM response.")
        else:
            print("No match found for tax rate in LLM response.")
    return None

def check_tax_rate(state):
    state = state.lower()  # Ensure state is always queried in lowercase
    engine = create_engine("sqlite:///electrical_parts.db", echo=True)
    response = {}
    try:
        with engine.begin() as connection:
            state_tax_result = connection.execute(
                text("SELECT tax_rate FROM taxes WHERE state = :state"),
                {"state": state},
            ).fetchone()
            
            if state_tax_result:
                state_tax_rate = state_tax_result[0]
                response["status"] = "success"
                response["message"] = f"Tax rate for {state} is {state_tax_rate * 100}%."
                response["state"] = state
                response["tax_rate"] = state_tax_rate
                return json.dumps(response)
            
    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Failed to fetch tax rate: {str(e)}"
        return json.dumps(response)
    
    # If SQL database query fails, fall back to ChromaDB
    try:
        query = f"tax rate of {state}"
        query_embedding = create_embeddings(query)
        results = collection.query(query_embeddings=query_embedding, n_results=5)

        if results['documents']:
            top_results = []
            extracted_context = ""
            
            for i, doc in enumerate(results['documents'][:4]):  # Get top 4 results
                top_results.append(doc[0])
                extracted_context += doc[0] + "\n"
            
            response["status"] = "success"
            response["message"] = " | ".join(top_results)  # Bundle top 4 results into message
            response["state"] = state
            
            # Pass extracted context to LLM to retrieve tax rate
            extracted_tax_rate = extract_tax_rate_from_llm(state, extracted_context)
            
            # Store the extracted tax rate in SQLite if found
            if extracted_tax_rate is not None:
                store_tax_rate(state, extracted_tax_rate)
                response["tax_rate"] = extracted_tax_rate
                response["message"] += f" | Extracted tax rate: {extracted_tax_rate * 100}% stored in database."
        else:
            response["status"] = "error"
            response["message"] = f"No tax information available for state: {state}."

    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Failed to fetch tax rate from ChromaDB: {str(e)}"
    
    return json.dumps(response)

if __name__ == "__main__":
    state = "arizona"  # Replace with the state you want to check
    print(check_tax_rate(state))