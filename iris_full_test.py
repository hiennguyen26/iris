import enum
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
import json
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import numpy as np
import math

load_dotenv()
api_key = os.getenv('open_ai')

instructor_client = instructor.patch(AsyncOpenAI(api_key=api_key))

# Initialize Chroma client with persistence
client = chromadb.PersistentClient(path="./chroma_db")

# Create embedding function
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Import the gap analysis rubrics and standard requirements
with open('gap_analysis_rubrics.json', 'r') as f:
    gap_analysis_rubrics = json.load(f)

with open('standard_requirements.json', 'r') as f:
    standard_requirements = json.load(f)

class GapAnswer(BaseModel):
    reasoning: str = Field(description="The reasoning for the answer")
    answer: str = Field(description="The answer to the gap analysis question given a internal fact and external dot point")
    gap_exists: bool = Field(description="Whether a gap exists between the internal fact and external dot point")
    remediation: str = Field(description="The remediation suggestion for the gap if it exists, otherwise 'No remediation needed'")
    gap_severity: str = Field(description="The level of severity for the gap if it exists (high, medium, low), otherwise 'No gap'")
    
class GapAnalysis(BaseModel):
    question: str = Field(description="The gap analysis question")
    gap_answer: GapAnswer = Field(description="The answer to the gap analysis question")

class FullGapAnalysis(BaseModel):
    requirement: str = Field(description="The standard requirement being analyzed")
    internal_facts: Dict[str, List[str]] = Field(description="The relevant internal facts (risks, controls, standards)")
    external_dot_point: str = Field(description="The external dot point being compared against")
    gap_analysis: List[GapAnalysis] = Field(description="The list of gap analysis questions and answers")

class RemediationSuggestion(BaseModel):
    remediation_suggestion: str = Field(description="The full remediation suggestion for the gap analysis")


async def perform_gap_analysis(requirement: str, internal_facts: Dict[str, List[str]], external_dot_point: str, rubric: List[Dict[str, str]]) -> FullGapAnalysis:
    gap_analyses = []
    for question_dict in rubric:
        question = question_dict['question']
        response = await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=GapAnswer,
            messages=[
                {"role": "system", "content": "You are an expert in gap analysis between internal standards and external regulations. If a gap exists, provide a detailed remediation plan."},
                {"role": "user", "content": f"Analyze the following:\nRequirement: {requirement}\nInternal facts:\nRisks: {', '.join(internal_facts['risks'])}\nControls: {', '.join(internal_facts['controls'])}\nStandards: {', '.join(internal_facts['standards'])}\nExternal dot point: {external_dot_point}\n\nQuestion: {question}\n\nProvide a detailed remediation plan if a gap exists."}
            ]
        )
        gap_analyses.append(GapAnalysis(question=question, gap_answer=response))
    
    return FullGapAnalysis(requirement=requirement, internal_facts=internal_facts, external_dot_point=external_dot_point, gap_analysis=gap_analyses)

async def get_relevant_items(collection_name: str, query_text: str, n_results: int = 2) -> List[Dict[str, str]]:
    collection = client.get_collection(collection_name, embedding_function=embedding_function)
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["documents", "metadatas"]
    )
    return [{"document": doc, "description": meta.get("description", "")} for doc, meta in zip(results['documents'][0], results['metadatas'][0])]

async def analyze_all_gaps():
    all_analyses = []
    n_relevant_items = 2
    
    for requirement in tqdm(standard_requirements[:5]):  # Analyze first 5 requirements for brevity
        if requirement['isRelevantforStandard']:
            # Retrieve relevant risks, controls, and standards
            risks = await get_relevant_items('risks', requirement['text'], n_relevant_items)
            controls = await get_relevant_items('controls', requirement['text'], n_relevant_items)
            standards = await get_relevant_items('standards', requirement['text'], n_relevant_items)
            
            internal_facts = {
                'risks': [item['document'] for item in risks],
                'controls': [item['document'] for item in controls],
                'standards': [f"{item['document']} - {item['description']}" for item in standards]
            }
            
            for rubric in gap_analysis_rubrics:
                analysis = await perform_gap_analysis(
                    requirement['text'],
                    internal_facts,
                    requirement['description'],
                    rubric['gap_analysis_rubric']
                )
                yield analysis  # Yield each analysis as it's completed

    # Save the results to a JSON file
    with open('gap_analysis_results.json', 'w') as f:
        json.dump([analysis.dict() for analysis in all_analyses], f, indent=2)

# Run the analysis
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    import time

    start_time = time.time()
    all_analyses = asyncio.run(analyze_all_gaps())
    
    # Calculate stats
    total_gaps = sum(any(ga.gap_answer.gap_exists for ga in analysis.gap_analysis) for analysis in all_analyses)
    total_questions = sum(len(analysis.gap_analysis) for analysis in all_analyses)
    
    # Count gaps by severity
    high_severity_gaps = sum(sum(1 for ga in analysis.gap_analysis if ga.gap_answer.gap_exists and ga.gap_answer.gap_severity == "high") for analysis in all_analyses)
    medium_severity_gaps = sum(sum(1 for ga in analysis.gap_analysis if ga.gap_answer.gap_exists and ga.gap_answer.gap_severity == "medium") for analysis in all_analyses)
    low_severity_gaps = sum(sum(1 for ga in analysis.gap_analysis if ga.gap_answer.gap_exists and ga.gap_answer.gap_severity == "low") for analysis in all_analyses)

    end_time = time.time()
    print(f"Time taken to run main: {end_time - start_time:.2f} seconds")
    
    # Print stats
    print(f"Total number of analyses: {len(all_analyses)}")
    print(f"Total number of gaps identified: {total_gaps}")
    print(f"Total number of questions analyzed: {total_questions}")
    print(f"Percentage of questions with gaps: {(total_gaps / total_questions) * 100:.2f}%")
    print(f"Number of high severity gaps: {high_severity_gaps}")
    print(f"Number of medium severity gaps: {medium_severity_gaps}")
    print(f"Number of low severity gaps: {low_severity_gaps}")

    # Create pie chart for gap severity
    labels = 'High', 'Medium', 'Low'
    sizes = [high_severity_gaps, medium_severity_gaps, low_severity_gaps]
    colors = ['red', 'orange', 'yellow']
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    plt.title('Gap Severity Distribution')
    plt.savefig('gap_severity_distribution.png')
    plt.close()

    # Create bar chart for gap analysis
    labels = ['Total Questions', 'Questions with Gaps']
    values = [total_questions, total_gaps]
    plt.bar(labels, values)
    plt.title('Gap Analysis Overview')
    plt.ylabel('Number of Questions')
    for i, v in enumerate(values):
        plt.text(i, v, str(v), ha='center', va='bottom')
    plt.savefig('gap_analysis_overview.png')
    plt.close()

    print("Graphs have been saved as 'gap_severity_distribution.png' and 'gap_analysis_overview.png'")
