# import ollama
# from dotenv import load_dotenv

# load_dotenv(override=True)

from ollama import Client
client = Client(
    host ="http://localhost:5500",

)

try:
   
    
    
    # Make sure your messages are formatted correctly
    messages = [{"role": "user", "content": "Hello!"}]
    
    # Specify the model name if required
    model_name = "llama3.1"  # Replace with your model name if needed

    # Now make the chat request
    response = client.chat(model=model_name, messages=messages)

    print(response)
except Exception as e:
    print(f"Error: {e}")
