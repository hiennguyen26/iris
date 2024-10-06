import json
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import numpy as np
import math

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
    n_results=5,  # Adjust this number as needed
    include=["documents", "metadatas", "distances"]
)

# Function to calculate similarity from distance
def calculate_similarity(distance):
    return math.exp(-distance)

# Print the results with raw distance and cosine similarity percentage
print(f"Risks related to '{query_text}':")
for i, (risk_id, document, metadata, distance) in enumerate(zip(results['ids'][0], results['documents'][0], results['metadatas'][0], results['distances'][0]), 1):
    print(f"\n{i}. Risk ID: {risk_id}")
    print(f"   Description: {document}")
    print(f"   Metadata: {metadata}")
    print(f"   Raw distance: {distance}")
    
    similarity = calculate_similarity(distance)
    similarity_percentage = similarity * 100
    print(f"   Similarity: {similarity_percentage:.2f}%")
