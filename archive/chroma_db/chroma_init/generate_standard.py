import pandas as pd
from pydantic import BaseModel, Field, ConfigDict
from openai import AsyncOpenAI
import instructor
from typing import List, Dict, Any
import os
import asyncio
import json
from dotenv import load_dotenv
import glob
from tqdm.auto import tqdm

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

async def main():
    with open('init_list.txt', 'r') as file:
        processes = [line.strip() for line in file if line.strip()]
    
    results = []
    for process in tqdm(processes, desc="Generating RCMs"):
        print(f"Processing: {process}")
        rcm = await generate_RCMs(process)
        results.append(rcm)
    
    # Save to JSON file
    with open('rcm_output.json', 'w') as f:
        json.dump([result.dict() for result in results], f, indent=2)
    
    print("RCM generation complete. Results saved to rcm_output.json")

if __name__ == "__main__":
    asyncio.run(main())