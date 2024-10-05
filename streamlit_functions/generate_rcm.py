import pandas as pd
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import instructor
from typing import List
import os
import asyncio
import json
from dotenv import load_dotenv
from tqdm.auto import tqdm
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()
api_key = os.getenv('open_ai')

instructor_client = instructor.patch(AsyncOpenAI(api_key=api_key))

class StandardRequirement(BaseModel):
    id: str = Field(description="The ID of the standard requirement")
    name: str = Field(description="The name of the standard requirement")
    description: str = Field(description="The description of the standard requirement, including the key principles and why they are important to the process")

class Standard(BaseModel):
    id: str = Field(description="The ID of the standard")
    name: str = Field(description="The name of the standard")
    description: str = Field(description="The description of the standard, including the purpose and applicability, and the key principles and requirements")
    requirements: List[StandardRequirement] = Field(description="The list of standard requirements that belong to the standard")
    
class Control(BaseModel):
    id: str = Field(description="The ID of the control")
    name: str = Field(description="The name of the control")
    description: str = Field(description="The description of the control, including the frequency of implementation or monitoring, and the importance and how it mitigates risks")
    standard_id: str = Field(description="The ID of the standard that the control belongs to")

class Risk(BaseModel):
    id: str = Field(description="The ID of the risk")
    name: str = Field(description="The name of the risk")
    description: str = Field(description="The description of the risk, including the potential impact on the organization, and the consequences if not addressed")
    control_id: str = Field(description="The ID of the control that the risk belongs to")

class RCM(BaseModel):
    standard: List[Standard] = Field(description="The standard that the control belongs to")
    controls: List[Control] = Field(description="The controls that belong to the standard")
    risks: List[Risk] = Field(description="The risks that belong to the control")

class BodyRCMs(BaseModel):
    process_name: str 
    list_standards: List[RCM] = Field(description="The list of risk control matrix that includes the standard, control, and risk")

class Process(BaseModel):
    name: str = Field(description="The name of the business process")
    description: str = Field(description="A brief description of the business process")

class ProcessList(BaseModel):
    processes: List[Process] = Field(description="List of business processes")

# Generate a Risk Control Matrix (RCM) for a given process
async def generate_RCMs(process_name: str) -> BodyRCMs:
    user_prompt = f"""
    As an expert auditor, generate a comprehensive and detailed Risk Control Matrix (RCM) for the process: {process_name}.

    1. Standard:
       - Provide 2-3 relevant industry standard or regulatory framework.
       - Include a detailed description of its purpose and applicability.
       - Assign a unique ID following the format STD-XXXX.
       - For each standard, provide 2-3 specific requirements:
         - Assign a unique ID following the format REQ-XXXX.
         - Provide a name for the requirement.
         - Include a description of the requirement, its key principles, and why it's important to the process.

    2. Controls:
       - Develop 2-3 specific, measurable controls that address key aspects of the process.
       - For each control:
         - Provide a clear, actionable description.
         - Explain its importance and how it mitigates risks.
         - Specify the frequency of implementation or monitoring.
         - Assign a unique ID following the format CTRL-XXXX.

    3. Risks:
       - Identify 2-3 significant risk per process.
       - For each risk:
         - Describe the potential impact on the organization.
         - Explain how it relates to the associated control.
         - Include potential consequences if not addressed.
         - Assign a unique ID following the format RSK-XXXX.

    Ensure all elements are logically connected and provide a cohesive framework for managing risks within the {process_name} process. Use industry-specific terminology and best practices where applicable.
    """
    
    try:
        response = await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=BodyRCMs,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert auditor with extensive knowledge of risk management and compliance. Given a process name, your task is to:
                                1. Analyze the process thoroughly, considering its scope, objectives, and potential impact on the organization.
                                2. Identify relevant industry standards, regulations, and best practices applicable to this process.
                                3. Think critically about the potential risks, vulnerabilities, and control points within the process.
                                4. Draw upon your auditing expertise to create a comprehensive and realistic Risk Control Matrix (RCM) that:
                                a. Accurately reflects the complexities and nuances of the given process.
                                b. Provides meaningful, actionable insights for risk mitigation.
                                c. Aligns with industry standards and regulatory requirements.
                                d. Demonstrates a deep understanding of the interplay between standards, controls, and risks.
                                Your goal is to generate synthetic RCM data that is not only logically consistent but also highly relevant and valuable for real-world risk management scenarios."""
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        return response
    except Exception as e:
        print(f"Error generating RCM for {process_name}: {str(e)}")
        return BodyRCMs(process_name=process_name, list_standards=[])

# Generate a list of business processes based on the given business context
async def generate_process_list(business_context: str) -> ProcessList:
    user_prompt = f"""
    As an expert business analyst, generate a comprehensive list of business processes based on the following business context:

    {business_context}

    For each process:
    1. Provide a clear, concise name for the process.
    2. Include a brief description of the process and its importance to the business.

    Generate 5-10 key processes that are most relevant to the given business context.
    """
    
    try:
        response = await instructor_client.chat.completions.create(
            model="gpt-4",
            response_model=ProcessList,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert business analyst with extensive knowledge of various industries and business processes. Your task is to analyze the given business context and identify the most relevant business processes."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        return response
    except Exception as e:
        print(f"Error generating process list: {str(e)}")
        return ProcessList(processes=[])

# Updated function to initialize Chroma DB
def initialize_chroma_db(rcm_data, db_path="./chroma_db"):
    # Ensure the directory exists
    os.makedirs(db_path, exist_ok=True)
    
    client = chromadb.PersistentClient(path=db_path)
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    collections = {
        'processes': client.get_or_create_collection('processes', embedding_function=embedding_function),
        'standards': client.get_or_create_collection('standards', embedding_function=embedding_function),
        'requirements': client.get_or_create_collection('requirements', embedding_function=embedding_function),
        'controls': client.get_or_create_collection('controls', embedding_function=embedding_function),
        'risks': client.get_or_create_collection('risks', embedding_function=embedding_function)
    }

    def generate_id(prefix, process_index, item_index):
        return f"{prefix}_{process_index:02d}_{item_index:03d}"

    for process_index, process in enumerate(rcm_data):
        process_id = generate_id('PROC', process_index, 0)
        
        collections['processes'].add(
            ids=[process_id],
            documents=[process['process_name']],
            metadatas=[{'description': process['process_name']}]
        )
        
        standards_data = process['list_standards'][0]
        
        for standard_index, standard in enumerate(standards_data['standard']):
            standard_id = generate_id('STD', process_index, standard_index)
            
            collections['standards'].add(
                ids=[standard_id],
                documents=[standard['name']],
                metadatas=[{'process_id': process_id, 'description': standard['description']}]
            )
            
            for req_index, requirement in enumerate(standard['requirements']):
                req_id = generate_id('REQ', process_index, req_index)
                
                collections['requirements'].add(
                    ids=[req_id],
                    documents=[requirement['description']],
                    metadatas=[{'standard_id': standard_id, 'process_id': process_id, 'name': requirement['name']}]
                )
        
        for control_index, control in enumerate(standards_data['controls']):
            control_id = generate_id('CTRL', process_index, control_index)
            
            collections['controls'].add(
                ids=[control_id],
                documents=[control['description']],
                metadatas=[{'standard_id': control['standard_id'], 'process_id': process_id, 'name': control['name']}]
            )
        
        for risk_index, risk in enumerate(standards_data['risks']):
            risk_id = generate_id('RISK', process_index, risk_index)
            
            collections['risks'].add(
                ids=[risk_id],
                documents=[risk['description']],
                metadatas=[{'control_id': risk['control_id'], 'process_id': process_id, 'name': risk['name']}]
            )

    return client

# Update the main function to include Chroma DB initialization
async def main(business_context: str):
    process_list = await generate_process_list(business_context)
    
    with open('init_list.txt', 'w') as file:
        for process in process_list.processes:
            file.write(f"{process.name}\n")
    
    results = []
    for process in tqdm(process_list.processes, desc="Generating RCMs"):
        rcm = await generate_RCMs(process.name)
        results.append(rcm)
    
    with open('rcm_output.json', 'w') as f:
        json.dump([result.dict() for result in results], f, indent=2)
    
    # Initialize Chroma DB
    chroma_client = initialize_chroma_db([result.dict() for result in results], db_path="./chroma_db")
    
    return chroma_client

if __name__ == "__main__":
    business_context = """
    A tech startup called "ByteBoost" specializes in developing artificial 
    intelligence software for optimizing digital marketing campaigns. 
    They provide cutting-edge algorithms that analyze consumer behavior in 
    real-time to help companies maximize their online advertising ROI. 
    ByteBoost's platform offers personalized recommendations and automated adjustments, 
    giving businesses a competitive edge in the crowded digital advertising landscape. 
    Their user-friendly interface caters to both small businesses and large 
    corporations looking to enhance their marketing strategies.
    """
    chroma_client = asyncio.run(main(business_context))

    print("\nRunning Chroma DB tests:")

    # Test 1: Check if all collections exist and have data
    collections = ["processes", "standards", "requirements", "controls", "risks"]
    for collection_name in collections:
        collection = chroma_client.get_collection(collection_name)
        count = collection.count()
        print(f"Test 1: {collection_name.capitalize()} collection count: {count}")

    # Test 2: Perform a simple query on the standards collection
    standards_collection = chroma_client.get_collection("standards")
    query_result = standards_collection.query(
        query_texts=["data protection"],
        n_results=1
    )
    print("\nTest 2: Query result for 'data protection' in standards:")
    if query_result['documents']:
        print(f"Found: {query_result['documents'][0]}")
    else:
        print("No matching standard found.")

    # Test 3: Check relationships between collections
    processes_collection = chroma_client.get_collection("processes")
    controls_collection = chroma_client.get_collection("controls")
    risks_collection = chroma_client.get_collection("risks")

    # Get a random process
    process = processes_collection.get(limit=1)
    process_id = process['ids'][0]
    print(f"\nTest 3: Checking relationships for process: {process['documents'][0]}")

    # Find related controls
    related_controls = controls_collection.get(where={"process_id": process_id})
    print(f"Related controls count: {len(related_controls['ids'])}")

    # Find related risks
    related_risks = risks_collection.get(where={"process_id": process_id})
    print(f"Related risks count: {len(related_risks['ids'])}")

    # Test 4: Test embedding search
    print("\nTest 4: Testing embedding search")
    search_result = processes_collection.query(
        query_texts=["marketing campaign optimization"],
        n_results=2
    )
    print("Top 2 processes related to 'marketing campaign optimization':")
    for doc in search_result['documents']:
        print(f"- {doc}")

    # Test 5: Test filtering
    requirements_collection = chroma_client.get_collection("requirements")
    filtered_requirements = requirements_collection.get(
        where={"standard_id": {"$eq": standards_collection.get(limit=1)['ids'][0]}}
    )
    print(f"\nTest 5: Requirements for the first standard: {len(filtered_requirements['ids'])}")

    # Test 6: Test updating a document
    print("\nTest 6: Testing document update")
    original_process = processes_collection.get(limit=1)
    original_name = original_process['documents'][0]
    updated_name = original_name + " (Updated)"
    processes_collection.update(
        ids=[original_process['ids'][0]],
        documents=[updated_name]
    )
    updated_process = processes_collection.get(ids=[original_process['ids'][0]])
    print(f"Original name: {original_name}")
    print(f"Updated name: {updated_process['documents'][0]}")

    # Revert the change
    processes_collection.update(
        ids=[original_process['ids'][0]],
        documents=[original_name]
    )

    print("\nChroma DB initialization and tests completed.")