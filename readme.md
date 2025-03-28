# SQL Chatbot &#x20;

# LLMs (GPT-4o-mini & Qwen2.5-32B)

This project is a conversational SQL chatbot designed to generate and execute SQL queries on a database using 
**Streamlit**, **gradio**,**fastapi**, **ChromaDB**, and **LLMs (GPT-4o-mini from OpenAI and Qwen2.5-32B via Ollama)**.

## 🚀 Features

- 🧠 **LLM Integration**: Supports both OpenAI's `GPT-4o-mini` and Ollama's `Qwen2.5-32B` for SQL query generation.
- 🗄️ **ChromaDB**: Provides database schema retrieval and contextual understanding for more accurate SQL generation.
- 🔍 **SQL Validation**: Ensures only `SELECT` queries are executed for security.
- 💬 **Interactive Chat Interface**: Built with Streamlit for an easy-to-use chatbot experience.
- ⏱️ **Performance Monitoring**: Displays response generation time for each query.

## 📂 Project Structure

```
.
├── backend
│   ├── sql_agent
│   │   ├── with_ui_select_model_v3.py  # Streamlit-based UI for SQL chatbot
│   │   ├── chat_assist
│   │   │   ├── using_ollama_qwen_api_gradio.py # Gradio UI for testing with 
|   |   |   ├── using_ollama.py # main function to run the ollama chat
Qwen2.5-32B
│   ├── web
│   │   ├── api.py  # FastAPI-based chat backend
│   ├── vector_store_setup
│   │   ├── using_chroma_v2.py  # ChromaDB setup script
│   ├── db_setup
│   │   ├── using_sqlite_v2.py  # SQLite setup script
├── frontend /chat-ui
│   ├── React-based chat interface 
└── README.md
```


## 🛠️ Initial setup:

### 1️⃣ Running ChromaDB Setup

To set up ChromaDB for vector storage:

```bash
cd LLM-sql_agent/backend/vector_store_setup
python -m using_chroma_v2.py
```

### 2️⃣ Running SQLite Setup

To set up the SQLite database:

```bash
cd LLM-sql_agent/backend/db_setup
python using_sqlite_v2.py
```

## 🏃‍♂️ Usage Commands:

### Running the SQL Agent with UI (Testing & Development)

Use Streamlit to run the chatbot with a UI:

```bash
streamlit run backend/sql_agent/with_ui_select_model_v3.py
```

### Starting the Chat Web Server (using ollama)

Run the backend API server using `uvicorn`:

```bash
uvicorn LLM-sql-agent.backend.web.api_v2:app --reload
```

### Running the React-based Chat App 

Navigate to the `frontend` directory and start the React app:

```bash
cd frontend/chat-ui
npm install
npm run dev
```

### Running the Gradio UI (For Backend Development & Testing with Ollama)

To test the chatbot using Ollama's Qwen2.5-32B, run:

```bash
python -m LLM-sql-agent.chat_assist.using_ollama_qwen_api
```



## 📝 Notes

- This project currently supports both **OpenAI's GPT-4o-mini** and **Qwen2.5-32B via Ollama**.
- The chatbot **only executes SELECT queries** for security.

## 📌 Future Enhancements

- ✅ Add support for more databases beyond SQLite.
- ✅ Improve query optimization using feedback loops.
- ✅ Enhance frontend UI with real-time query validation.

---

###

