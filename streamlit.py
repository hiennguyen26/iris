import streamlit as st
from document_ingestion import generate_processes_and_controls
from inventory_search import search_inventory
import json
import time
import asyncio
from iris_full_test import analyze_all_gaps

def main():
    st.title("Business Process and Control Generator")

    # User input for business description
    business_description = st.text_area("Describe your business or topic:")

    if st.button("Generate Processes and Controls"):
        if business_description:
            processes = generate_processes_and_controls(business_description)
            st.session_state.processes = processes
            st.success("Processes and controls generated successfully!")
        else:
            st.warning("Please provide a business description.")

    # Display generated processes and controls
    if 'processes' in st.session_state:
        st.subheader("Generated Processes and Controls")
        for i, process in enumerate(st.session_state.processes, 1):
            st.write(f"Process {i}: {process['name']}")
            for j, control in enumerate(process['controls'], 1):
                st.write(f"  Control {j}: {control}")

    st.divider()

    # New section for showing rubrics
    st.subheader("Gap Analysis Rubrics")
    show_rubrics()

    st.divider()

    # New section for live gap analysis progress
    st.subheader("Gap Analysis Progress")
    if st.button("Start Gap Analysis"):
        run_gap_analysis()

def show_rubrics():
    # Load rubrics from JSON file
    with open('gap_analysis_rubrics.json', 'r') as f:
        rubrics = json.load(f)

    # Display rubrics and their questions
    for rubric in rubrics:
        st.write(f"**{rubric['personality']}**")
        for question in rubric['gap_analysis_rubric']:
            st.write(f"- {question['question']}")
        st.write("---")

def run_gap_analysis():
    # Create placeholders for progress bars and statistics
    progress_bar = st.progress(0)
    stats_container = st.empty()

    # Run the gap analysis
    asyncio.run(analyze_all_gaps_with_progress(progress_bar, stats_container))

async def analyze_all_gaps_with_progress(progress_bar, stats_container):
    total_analyses = 0
    completed_analyses = 0
    total_gaps = 0
    high_severity_gaps = 0
    medium_severity_gaps = 0
    low_severity_gaps = 0

    async for analysis in analyze_all_gaps():
        total_analyses += 1
        completed_analyses += 1
        
        # Update progress
        progress = completed_analyses / total_analyses
        progress_bar.progress(progress)

        # Update statistics
        for ga in analysis.gap_analysis:
            if ga.gap_answer.gap_exists:
                total_gaps += 1
                if ga.gap_answer.gap_severity == "high":
                    high_severity_gaps += 1
                elif ga.gap_answer.gap_severity == "medium":
                    medium_severity_gaps += 1
                elif ga.gap_answer.gap_severity == "low":
                    low_severity_gaps += 1

        # Display live statistics
        stats_container.write(f"""
        Completed analyses: {completed_analyses}
        Total gaps identified: {total_gaps}
        High severity gaps: {high_severity_gaps}
        Medium severity gaps: {medium_severity_gaps}
        Low severity gaps: {low_severity_gaps}
        """)

        # Simulate some delay to show progress (remove this in production)
        await asyncio.sleep(0.1)

    # Final update
    progress_bar.progress(1.0)
    st.success("Gap analysis completed!")

if __name__ == "__main__":
    main()
