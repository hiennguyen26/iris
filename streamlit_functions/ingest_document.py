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
import PyPDF2

# # Get the NYDFS PDF file
# pdf_file_path = "nydfs_cyber_req.pdf"

# # Read the PDF file
# with open(pdf_file_path, "rb") as file:
#     pdf_reader = PyPDF2.PdfReader(file)
#     nydfs_text = ""
#     for page in pdf_reader.pages:
#         nydfs_text += page.extract_text()

# # Store the text content in a variable
# nydfs_content = nydfs_text.strip()

load_dotenv()
api_key = os.getenv('open_ai')

instructor_client = instructor.patch(AsyncOpenAI(api_key=api_key))

class BulletPoint(BaseModel):
    name: str = Field(description="Give a name to the bullet point")
    topics: List[str] = Field(description="The 2-3 word topic name that the bullet point belongs to. This will be used to group bullet points together.")
    text: str = Field(description="The exact copy of the extracted text from the PDF that was used to generate this bullet point. The extraction should be at least 100 words.")
    description: str = Field(description="The description of the bullet point in reference to the PDF")
    context: str = Field(description="The context of the bullet point in reference to the PDF")
    pagenum: str = Field(description="The page number of the bullet point in reference to the PDF")
    
class ListBulletPoints(BaseModel):
    list_bullet_points: List[BulletPoint] = Field(description="The list of bullet points")

class StandardRequirement(BaseModel):
    isRelevantforStandard: bool = Field(description="Is the bullet point relevant to become a standard requirement")
    id: str = Field(description="The ID of the standard requirement")
    name: str = Field(description="The name of the standard requirement")
    description: str = Field(description="The description of the standard requirement, including the purpose and applicability, and the key principles and requirements as it relates to the bullet point")
    text: str = Field(description="The text of the standard requirement per the bullet point")
    
class ListStandardRequirements(BaseModel):
    list_standard_requirements: List[StandardRequirement] = Field(description="The list of standard requirements extracted from the text's bullet points")

async def generate_BulletPoints(page_content: str) -> ListBulletPoints:
    user_prompt = f"""
    You are an expert auditor with extensive knowledge of risk management and compliance. Given a page of the NYDFS Cybersecurity Regulation, your task is to mark bullet points for further processing.
    
    The page content of the NYDFS Cybersecurity Regulation is as follows: {page_content}
    """
    
    try:
        response = await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=ListBulletPoints,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert compliance auditor whose job is to parse the latest NYDFS Cybersecurity Requirements for Financial Services Companies (Cybersecurity Regulation) and extract bullet points. 
                    """
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        return response
    except Exception as e:
        print(f"Error generating bullet points for page content: {str(e)}")
        return ListBulletPoints(list_bullet_points=[])
    
async def generate_standard_requirements(bulletpoint: BulletPoint) -> ListStandardRequirements:
    user_prompt = f"""
    You are an expert auditor with extensive knowledge of risk management and compliance. Given a bullet point {bulletpoint}, your task is to analyze whether a given bullet point should be passed down to compliance team for their review for further processing. 
    """
    
    try:
        response = await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=ListStandardRequirements,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an expert compliance auditor whose job is to parse the latest NYDFS Cybersecurity Requirements for Financial Services Companies (Cybersecurity Regulation) and convert each bullet point into a standard requirement. Any bullet point that is not relevant to the NYDFS Cybersecurity Regulation should be marked as not relevant for a standard requirement.
                    The NYDFS Cybersecurity Regulation is as follows: {nydfs_content}"""
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        return response
    except Exception as e:
        print(f"Error generating standard requirements for {bulletpoint}: {str(e)}")
        return ListStandardRequirements(list_standard_requirements=[])

async def main(pdf_file_path: str):
    # Read the PDF file
    with open(pdf_file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        nydfs_text = ""
        for page in pdf_reader.pages:
            nydfs_text += page.extract_text()

    # Store the text content in a variable
    nydfs_content = nydfs_text.strip()

    all_bullet_points = []
    
    # Generate bullet points for each page
    for page_num, page in enumerate(tqdm(pdf_reader.pages, desc="Processing Pages")):
        page_content = page.extract_text().strip()
        bullet_points = await generate_BulletPoints(page_content)
        all_bullet_points.extend(bullet_points.list_bullet_points)
    
    # Save all bullet points to JSON
    output_file = 'bullet_points.json'
    with open(output_file, 'w') as f:
        json.dump({"list_bullet_points": [bp.dict() for bp in all_bullet_points]}, f, indent=2)
    
    print(f"Number of bullet points generated: {len(all_bullet_points)}")
    print(f"Process completed. Results saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main("nydfs_cyber_req.pdf"))