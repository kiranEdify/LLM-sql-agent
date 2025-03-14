import os
import fitz  # PyMuPDF for extracting text from PDFs
import docx  # Python-docx for extracting text from DOCX files
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv(override=True)


# Initialize ChromaDB with persistence
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="sql_schema")  # Collection to store schema and documents

# Initialize the Sentence Transformer Model (using a pre-trained model)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page in document:
        text += page.get_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text.strip() + "\n"  # Strip unnecessary spaces and add a new line after each paragraph.
    return text

# Function to create embeddings for the text
def create_embeddings(text):
    return model.encode([text])

# Define schema chunks with tables and relationships (given schema)
schema_chunks = [
    # Tables
    {"id": "suppliers_table", "text": "table: suppliers", "metadata": {"type": "table", "table_name": "suppliers"}},
    {"id": "categories_table", "text": "table: categories", "metadata": {"type": "table", "table_name": "categories"}},
    {"id": "products_table", "text": "table: products", "metadata": {"type": "table", "table_name": "products"}},
    {"id": "customers_table", "text": "table: customers", "metadata": {"type": "table", "table_name": "customers"}},
    {"id": "orders_table", "text": "table: orders", "metadata": {"type": "table", "table_name": "orders"}},
    {"id": "order_items_table", "text": "table: order_items", "metadata": {"type": "table", "table_name": "order_items"}},
    
    # Columns
    {"id": "suppliers_columns", "text": "Columns: supplier_id, name, contact_name, phone, address", "metadata": {"type": "column", "table": "suppliers", "columns": "supplier_id, name, contact_name, phone, address"}},
    {"id": "categories_columns", "text": "Columns: category_id, name", "metadata": {"type": "column", "table": "categories", "columns": "category_id, name"}},
    {"id": "products_columns", "text": "Columns: product_id, name, category_id, supplier_id, price, stock_quantity", "metadata": {"type": "column", "table": "products", "columns": "product_id, name, category_id, supplier_id, price, stock_quantity"}},
    {"id": "customers_columns", "text": "Columns: customer_id, name, email, phone, address", "metadata": {"type": "column", "table": "customers", "columns": "customer_id, name, email, phone, address"}},
    {"id": "orders_columns", "text": "Columns: order_id, customer_id, order_date, total_amount", "metadata": {"type": "column", "table": "orders", "columns": "order_id, customer_id, order_date, total_amount"}},
    {"id": "order_items_columns", "text": "Columns: order_item_id, order_id, product_id, quantity, unit_price", "metadata": {"type": "column", "table": "order_items", "columns": "order_item_id, order_id, product_id, quantity, unit_price"}},
    
    # Relationships
    {"id": "products_suppliers_relationship", "text": "Relationship: products.supplier_id → suppliers.supplier_id", "metadata": {"type": "relationship", "table1": "products", "table2": "suppliers", "relationship_type": "foreign_key"}},
    {"id": "products_categories_relationship", "text": "Relationship: products.category_id → categories.category_id", "metadata": {"type": "relationship", "table1": "products", "table2": "categories", "relationship_type": "foreign_key"}},
    {"id": "orders_customers_relationship", "text": "Relationship: orders.customer_id → customers.customer_id", "metadata": {"type": "relationship", "table1": "orders", "table2": "customers", "relationship_type": "foreign_key"}},
    {"id": "order_items_orders_relationship", "text": "Relationship: order_items.order_id → orders.order_id", "metadata": {"type": "relationship", "table1": "order_items", "table2": "orders", "relationship_type": "foreign_key"}},
    {"id": "order_items_products_relationship", "text": "Relationship: order_items.product_id → products.product_id", "metadata": {"type": "relationship", "table1": "order_items", "table2": "products", "relationship_type": "foreign_key"}},
] 



# Check existing documents to avoid duplication
existing_ids = set(collection.get()["ids"])
# Add schema chunks to the ChromaDB collection
for chunk in schema_chunks:
    if chunk["id"] not in existing_ids:
        collection.add(
            ids=[chunk["id"]],
            documents=[chunk["text"]],  # Chroma will automatically generate embeddings
            metadatas=[chunk["metadata"]]
        )

# Function to store text from documents in Chroma DB
def store_document_in_chroma(document_path, document_name):
    # Extract text from the document
    if document_path.endswith('.pdf'):
        document_text = extract_text_from_pdf(document_path)
    elif document_path.endswith('.docx'):
        document_text = extract_text_from_docx(document_path)
    else:
        raise ValueError("Unsupported file format")
    
    # Generate embeddings for the extracted text
    embedding = create_embeddings(document_text)
    
    # Add document to Chroma DB
    collection.add(
        ids=[document_name],
        documents=[document_text],
        embeddings=embedding,
        metadatas=[{"document_name": document_name}]
    )

# Store a sample DOCX in Chroma DB

docx_path = os.getenv("SYS_PATH")  # Update this path to your docx file
store_document_in_chroma(docx_path, "tax_rate")

print("\n\nSchema and documents stored persistently in ChromaDB.\n\n")

# Function to search for similar documents in Chroma DB
def search_similar_documents(query, top_k=5):
    query_embedding = create_embeddings(query)
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    
    # Print the results for better understanding
    print("Search Results:")
    for result in results['documents']:
        print(result)
    
    return results

# Example search query
query = "What is the tax rate of california?"
search_results = search_similar_documents(query)
print(f"Search results: {search_results}")
