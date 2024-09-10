import json
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import numpy as np

# Load RCM data
with open('rcm_output.json', 'r') as f:
    rcm_data = json.load(f)

# Initialize Chroma client with persistence
client = chromadb.PersistentClient(path="./chroma_db")

# Create embedding function
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Create collections
collections = {
    'processes': client.get_or_create_collection('processes', embedding_function=embedding_function),
    'standards': client.get_or_create_collection('standards', embedding_function=embedding_function),
    'requirements': client.get_or_create_collection('requirements', embedding_function=embedding_function),
    'controls': client.get_or_create_collection('controls', embedding_function=embedding_function),
    'risks': client.get_or_create_collection('risks', embedding_function=embedding_function)
}

# Helper function to generate unique IDs
def generate_id(prefix, process_index, item_index):
    return f"{prefix}_{process_index:02d}_{item_index:03d}"

# Process and insert data
for process_index, process in enumerate(rcm_data):
    process_id = generate_id('PROC', process_index, 0)
    
    # Insert process
    collections['processes'].add(
        ids=[process_id],
        documents=[process['process_name']],
        metadatas=[{'description': process['process_name']}]
    )
    
    # Access the 'list_standards' key, then the first (and only) item in that list
    standards_data = process['list_standards'][0]
    
    for standard_index, standard in enumerate(standards_data['standard']):
        standard_id = generate_id('STD', process_index, standard_index)
        
        # Insert standard
        collections['standards'].add(
            ids=[standard_id],
            documents=[standard['name']],
            metadatas=[{'process_id': process_id, 'description': standard['description']}]
        )
        
        for req_index, requirement in enumerate(standard['requirements']):
            req_id = generate_id('REQ', process_index, req_index)
            
            # Insert requirement
            collections['requirements'].add(
                ids=[req_id],
                documents=[requirement['description']],
                metadatas=[{'standard_id': standard_id, 'process_id': process_id, 'name': requirement['name']}]
            )
    
    for control_index, control in enumerate(standards_data['controls']):
        control_id = generate_id('CTRL', process_index, control_index)
        
        # Insert control
        collections['controls'].add(
            ids=[control_id],
            documents=[control['description']],
            metadatas=[{'standard_id': control['standard_id'], 'process_id': process_id, 'name': control['name']}]
        )
    
    for risk_index, risk in enumerate(standards_data['risks']):
        risk_id = generate_id('RISK', process_index, risk_index)
        
        # Insert risk
        collections['risks'].add(
            ids=[risk_id],
            documents=[risk['description']],
            metadatas=[{'control_id': risk['control_id'], 'process_id': process_id, 'name': risk['name']}]
        )

print("Chroma DB initialization complete.")

# Example queries
def print_query_results(results):
    if not results['ids']:
        print("No results found.")
        return
    for i, item in enumerate(results['ids']):
        print(f"ID: {item}")
        print(f"Document: {results['documents'][i]}")
        print(f"Metadata: {results['metadatas'][i]}")
        print("---")

print("\nExample Queries:")

# 1. Find all controls related to a specific standard
print("1. Controls related to the first standard:")
standard_id = collections['standards'].get(limit=1)['ids'][0]
controls = collections['controls'].get(where={"standard_id": standard_id})
print_query_results(controls)

# 2. Retrieve risks associated with a particular process
print("\n2. Risks associated with the first process:")
process_id = collections['processes'].get()['ids'][0]
risks = collections['risks'].get(where={"process_id": process_id})
print_query_results(risks)

# 3. Search for requirements containing specific keywords across all standards
print("\n3. Requirements containing 'security':")
requirements = collections['requirements'].query(query_texts=["security"], n_results=5)
print_query_results(requirements)

# 4. Identify controls that address multiple risks
print("\n4. Controls addressing multiple risks:")
all_controls = collections['controls'].get()
control_risk_count = {}
for control_id in all_controls['ids']:
    risks = collections['risks'].get(where={"control_id": control_id})
    risk_count = len(risks['ids'])
    if risk_count > 1:
        control_risk_count[control_id] = risk_count

for control_id, risk_count in sorted(control_risk_count.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"Control ID: {control_id}, Number of risks addressed: {risk_count}")
    control_info = collections['controls'].get(ids=[control_id])
    print(f"Control description: {control_info['documents'][0]}")
    print("---")

# 5. Find all standards related to a specific process
print("\n5. Standards related to the first process:")
standards = collections['standards'].get(where={"process_id": process_id})
print_query_results(standards)

# 6. Search for controls containing specific keywords
print("\n6. Controls containing 'monitoring':")
monitoring_controls = collections['controls'].query(query_texts=["monitoring"], n_results=5)
print_query_results(monitoring_controls)

# 7. Find requirements for a specific standard
print("\n7. Requirements for the first standard:")
requirements = collections['requirements'].get(where={"standard_id": standard_id})
print_query_results(requirements)

# 8. Identify processes with the most standards
print("\n8. Processes with the most standards:")
process_standard_count = {}
for process in collections['processes'].get()['ids']:
    standards = collections['standards'].get(where={"process_id": process})
    process_standard_count[process] = len(standards['ids'])

for process_id, standard_count in sorted(process_standard_count.items(), key=lambda x: x[1], reverse=True)[:5]:
    process_info = collections['processes'].get(ids=[process_id])
    print(f"Process: {process_info['documents'][0]}, Number of standards: {standard_count}")

# 9. Find risks without associated controls
print("\n9. Risks without associated controls:")
all_risks = collections['risks'].get()
risks_without_controls = [risk_id for risk_id, control_id in zip(all_risks['ids'], all_risks['metadatas']) if not control_id.get('control_id')]
for risk_id in risks_without_controls[:5]:
    risk_info = collections['risks'].get(ids=[risk_id])
    print(f"Risk ID: {risk_id}")
    print(f"Risk description: {risk_info['documents'][0]}")
    print("---")

# 10. Search for similar processes
print("\n10. Processes similar to 'Risk Management':")
similar_processes = collections['processes'].query(query_texts=["Risk Management"], n_results=5)
print_query_results(similar_processes)