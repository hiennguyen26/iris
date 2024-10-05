# Gap Analysis Tool

## Overview
This tool performs automated gap analysis between internal organizational standards and external regulatory requirements. It uses AI-powered analysis to identify gaps, suggest remediations, and provide severity assessments.

## Features
- Analyzes gaps between internal facts (risks, controls, standards) and external requirements
- Uses GPT-4 for intelligent gap analysis
- Retrieves relevant internal documents using ChromaDB and sentence embeddings
- Generates detailed gap analysis reports with reasoning and remediation suggestions
- Provides statistical overview and visualizations of gap analysis results

## Prerequisites
- Python 3.7+
- OpenAI API key
- ChromaDB
- Required Python packages (see `requirements.txt`)

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables:
   - Create a `.env` file with `open_ai=your_api_key_here`
4. Prepare data files:
   - `gap_analysis_rubrics.json`: Contains analysis questions
   - `standard_requirements.json`: External regulatory requirements
   - Populate ChromaDB with internal documents (risks, controls, standards)

## Usage
Run the main script: