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

load_dotenv()
api_key = os.getenv('open_ai')

instructor_client = instructor.patch(AsyncOpenAI(api_key=api_key))

list_personalities = ["Structual & Contextual Gap Analysis", "Relevance & Specificity Gap Analysis", "Modality & Possibility Gap Analysis", "Directive & Outcome Gap Analysis"]

class GapAnalysisQuestion(BaseModel):
    question: str = Field(description="The question that is posed to determine the gap between a fact and a dot point")
    
class GapAnalysisRubric(BaseModel):
    personality: str
    gap_analysis_rubric: List[GapAnalysisQuestion] = Field(description="The list of gap analyzing questions based on a specific speciality for gap analysis")

async def generate_gap_analysis_rubric(personality: str) -> GapAnalysisRubric:
    user_prompt = f"""
    Your task is to embody the world's greatest leading expert in language gap analysis between standards and regulations. Your speciality is {personality}. Now return a rubric and list of questions that would best accomplish your task to fully determine the gap between a fact and a dot point.
    """
    
    try:
        response = await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=GapAnalysisRubric,
            messages=[
                {
                    "role": "system",
                    "content": f"""Assume that you are given a fact (internal standard requirement/information) and a dot point (external standard/regulation). Your task is to determine if there is a gap between the fact and the dot point. If there is a gap, you will provide a gap analysis question that can be used to determine if there is a gap between the fact and the dot point based on the specific speciality of {personality}.
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
        print(f"Error generating questions for gap analysis: {str(e)}")
        return GapAnalysisRubric(personality=personality, gap_analysis_rubric=[])

async def main():
    all_rubrics = []
    for personality in tqdm(list_personalities, desc="Generating Gap Analysis Rubrics"):
        rubric = await generate_gap_analysis_rubric(personality)
        all_rubrics.append(rubric)
    
    # Convert to dict for JSON serialization
    rubrics_dict = [rubric.dict() for rubric in all_rubrics]
    
    # Save to JSON file
    with open('gap_analysis_rubrics.json', 'w') as f:
        json.dump(rubrics_dict, f, indent=2)
    
    print("Gap Analysis Rubrics generation complete. Results saved to gap_analysis_rubrics.json")

if __name__ == "__main__":
    asyncio.run(main())
