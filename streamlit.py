import streamlit as st
from streamlit_functions.generate_rcm import main as generate_rcm_async
import json
import asyncio
import os
import plotly.graph_objects as go
import openai
import pandas as pd

# Set up OpenAI API key
openai.api_key = os.getenv("open_ai")

async def generate_rcm(business_description):
    return await generate_rcm_async(business_description)

def load_rcm_data():
    file_path = os.path.join('streamlit_functions', 'rcm_output.json')
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_random_business_topic():
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a business consultant tasked with generating random business scenarios."},
            {"role": "user", "content": "Generate a brief description of a random company in a particular industry. Keep it concise, about 4-5 sentences."}
        ]
    )
    return response.choices[0].message.content.strip()

def main():
    st.title("Business Process and Control Generator")

    # Sidebar
    st.sidebar.title("Navigation")
    tab = st.sidebar.radio("Select a tab:", ["Inventory", "Document Upload"])

    if tab == "Inventory":
        inventory_tab()
    else:
        document_upload_tab()

def inventory_tab():
    # Initialize session state for business description
    if 'business_description' not in st.session_state:
        st.session_state.business_description = ""

    # User input for business description
    business_description = st.text_area("Describe your business or topic:", value=st.session_state.business_description)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Randomize Business Topic"):
            st.session_state.business_description = generate_random_business_topic()
            st.rerun()

    with col2:
        if st.button("Generate Processes and Controls"):
            if business_description:
                asyncio.run(generate_rcm(business_description))
                st.success("Processes and controls generated successfully!")
            else:
                st.warning("Please provide a business description.")

    # Display generated processes and controls
    rcm_data = load_rcm_data()
    if rcm_data:
        st.subheader("Generated Processes and Controls")
        
        # Create tabs for each process
        tabs = st.tabs([process['process_name'] for process in rcm_data])

        for i, process in enumerate(rcm_data):
            with tabs[i]:
                st.header(process['process_name'])
                
                # Count risks, controls, and standards
                total_risks = sum(len(standard_group['risks']) for standard_group in process['list_standards'])
                total_controls = sum(len(standard_group['controls']) for standard_group in process['list_standards'])
                total_standards = sum(len(standard_group['standard']) for standard_group in process['list_standards'])
                
                # Create charts
                fig = go.Figure(data=[
                    go.Bar(name='Risks', x=['Risks'], y=[total_risks]),
                    go.Bar(name='Controls', x=['Controls'], y=[total_controls]),
                    go.Bar(name='Standards', x=['Standards'], y=[total_standards])
                ])
                fig.update_layout(title='Process Overview', barmode='group')
                st.plotly_chart(fig, key=f"chart_{process['process_name']}")

                for standard_group in process['list_standards']:
                    for standard in standard_group['standard']:
                        with st.expander(f"Standard: {standard['id']}"):
                            st.write(f"**Name:** {standard['name']}")
                            st.write(f"**Description:** {standard['description']}")
                            
                            st.subheader("Requirements")
                            for req in standard['requirements']:
                                st.write(f"- **{req['name']}:** {req['description']}")

                    st.subheader("Controls")
                    for control in standard_group['controls']:
                        st.write(f"- **{control['name']}:** {control['description']}")

                    st.subheader("Risks")
                    for risk in standard_group['risks']:
                        st.write(f"- **{risk['name']}:** {risk['description']}")

    st.divider()

def document_upload_tab():
    st.header("Document Upload")

    # Initialize session state for uploaded files
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        # Add the uploaded file to the session state
        st.session_state.uploaded_files.append(uploaded_file.name)
        st.success(f"File uploaded: {uploaded_file.name}")

    # Display uploaded files in a datatable
    if st.session_state.uploaded_files:
        df = pd.DataFrame(st.session_state.uploaded_files, columns=["Filename"])
        df['Delete'] = False

        edited_df = st.data_editor(df, hide_index=True)

        # Check for files to delete
        files_to_delete = edited_df[edited_df['Delete']]['Filename'].tolist()
        for file in files_to_delete:
            st.session_state.uploaded_files.remove(file)

        if files_to_delete:
            st.rerun()

# Run the Streamlit app
if __name__ == "__main__":
    main()