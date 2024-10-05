import asyncio
import json
import lancedb
from sentence_transformers import SentenceTransformer
import torch

async def initialize_lancedb():
    # Connect to LanceDB
    db = await lancedb.connect_async("./lancedb")

    # Load the JSON data
    with open("./../chroma_init/rcm_output.json", "r") as file:
        data = json.load(file)

    # Initialize the SentenceTransformer model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer("dunzhang/stella_en_400M_v5", trust_remote_code=True).to(device)
    print(f"Using device: {device}")
    query_prompt_name = "s2p_query"

    # Flatten the nested structure and generate embeddings
    flattened_data = []
    for process in data:
        for standard_list in process["list_standards"]:
            for standard in standard_list["standard"]:
                for requirement in standard["requirements"]:
                    text = f"{requirement['name']} {requirement['description']}"
                    embedding = model.encode(text, prompt_name=query_prompt_name).tolist()
                    flattened_data.append({
                        "process_name": process["process_name"],
                        "standard_id": standard["id"],
                        "standard_name": standard["name"],
                        "requirement_id": requirement["id"],
                        "requirement_name": requirement["name"],
                        "requirement_description": requirement["description"],
                        "embedding": embedding
                    })
            for control in standard_list.get("controls", []):
                text = f"{control['name']} {control['description']}"
                embedding = model.encode(text, prompt_name=query_prompt_name).tolist()
                flattened_data.append({
                    "process_name": process["process_name"],
                    "control_id": control["id"],
                    "control_name": control["name"],
                    "control_description": control["description"],
                    "standard_id": control["standard_id"],
                    "embedding": embedding
                })
            for risk in standard_list.get("risks", []):
                text = f"{risk['name']} {risk['description']}"
                embedding = model.encode(text, prompt_name=query_prompt_name).tolist()
                flattened_data.append({
                    "process_name": process["process_name"],
                    "risk_id": risk["id"],
                    "risk_name": risk["name"],
                    "risk_description": risk["description"],
                    "control_id": risk["control_id"],
                    "embedding": embedding
                })

    # Create or overwrite the table
    table = await db.create_table("rcm_data", data=flattened_data, mode="overwrite")

    print(f"Table 'rcm_data' created with {len(flattened_data)} rows")

    # List all tables to verify
    tables = await db.table_names()
    print("Available tables:", tables)

if __name__ == "__main__":
    asyncio.run(initialize_lancedb())
