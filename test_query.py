import json
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import numpy as np

# Initialize Chroma client with persistence
client = chromadb.PersistentClient(path="./chroma_db")

# Create embedding function
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Get the risks collection
risks_collection = client.get_collection('risks', embedding_function=embedding_function)

# Query for risks related to identity access management
query_text = "strategy"
results = risks_collection.query(
    query_texts=[query_text],
    n_results=5  # Adjust this number as needed
)

# Print the results
print(f"Risks related to '{query_text}':")
for i, (risk_id, document, metadata) in enumerate(zip(results['ids'][0], results['documents'][0], results['metadatas'][0]), 1):
    print(f"\n{i}. Risk ID: {risk_id}")
    print(f"   Description: {document}")
    print(f"   Metadata: {metadata}")
