# GRC Gap Analysis Tool

This tool provides a comprehensive solution for Governance, Risk, and Compliance (GRC) gap analysis. It allows users to generate processes and controls based on a business description, view gap analysis rubrics, and perform a detailed gap analysis.

## Workflow

1. **Business Process and Control Generation**

   - User inputs a free-form text description of their business or topic.
   - The system generates relevant processes and controls based on this input.
   - Generated processes and controls are displayed to the user.

2. **Gap Analysis Rubrics**

   - The system displays pre-defined gap analysis rubrics.
   - Each rubric contains a set of questions designed to identify gaps in compliance.

3. **Gap Analysis Execution**

   - User initiates the gap analysis process.
   - The system performs the following steps:
     a. Retrieves relevant risks, controls, and standards from a Chroma database.
     b. Applies the gap analysis rubrics to compare internal facts with external requirements.
     c. Generates detailed gap analysis results, including reasoning, gap existence, severity, and remediation suggestions.
   - Progress and statistics are displayed in real-time.

4. **Results Visualization**
   - After completion, the system generates visualizations of the gap analysis results.
   - Pie chart showing the distribution of gap severities.
   - Bar chart comparing total questions to questions with identified gaps.

## Next Steps for Streaming Output

To improve the real-time feedback during the gap analysis process, consider the following enhancements:

1. **Detailed Progress Updates**

   - Modify the `analyze_all_gaps` function in `iris_full_test.py` to yield more granular progress information.
   - Include details such as the current requirement being analyzed, the rubric being applied, and the specific question being processed.

2. **Live Question Display**

   - In the Streamlit app, add a section to display the current question being analyzed in real-time.

3. **Immediate Gap Display**

   - As soon as a gap is identified, display it in the Streamlit app, including its severity and a brief description.

4. **Running Statistics**

   - Continuously update and display statistics such as the number of gaps identified, their severities, and the percentage of completion.

5. **Incremental Visualization**

   - Update the pie chart and bar chart in real-time as new data becomes available, rather than generating them only at the end.

6. **Cancelation Option**
   - Implement a feature allowing users to cancel the ongoing analysis if needed.

## Implementation Example

Here's a code snippet to illustrate how you might modify `analyze_all_gaps` to yield more detailed information:
