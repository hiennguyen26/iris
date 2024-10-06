import streamlit as st
from streamlit_functions.generate_rcm import main as generate_rcm_async
from streamlit_functions.ingest_document import main as process_document
import json
import asyncio
import os
import plotly.graph_objects as go
import openai
import pandas as pd
import PyPDF2
from streamlit_pdf_viewer import pdf_viewer
from PyPDF2 import PdfWriter

# Set up OpenAI API key
openai.api_key = os.getenv("open_ai")

async def generate_rcm(business_description):
    return await generate_rcm_async(business_description)

def load_rcm_data(file_name='rcm_output.json'):
    file_path = os.path.join('streamlit_functions', file_name)
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

    col1, col2, col3 = st.columns(3)
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

    with col3:
        if st.button("Use Financial Institution Case"):
            st.session_state.rcm_data = load_rcm_data('rcm_output_base.json')
            st.success("Loaded financial institution case successfully!")

    # Display generated processes and controls
    rcm_data = st.session_state.get('rcm_data') or load_rcm_data()
    if rcm_data:
        st.subheader("Generated Processes:")
        
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

    # Initialize session state for processing status and PDF viewing
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'show_pdf' not in st.session_state:
        st.session_state.show_pdf = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        # Save the uploaded file to @manual_docs
        file_path = os.path.join("./streamlit_functions/manual_docs", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File uploaded: {uploaded_file.name}")

    # Display files in @manual_docs
    st.subheader("Uploaded Files")
    manual_docs_files = [f for f in os.listdir("./streamlit_functions/manual_docs") if f.endswith('.pdf')]
    if manual_docs_files:
        file_data = []
        for file in manual_docs_files:
            file_path = os.path.join("./streamlit_functions/manual_docs", file)
            file_size = os.path.getsize(file_path) / 1024  # Size in KB
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
            file_data.append({"Select": False, "Filename": file, "Size (KB)": f"{file_size:.2f}", "Pages": num_pages})

        df = pd.DataFrame(file_data)
        edited_df = st.data_editor(df, hide_index=True, column_config={
            "Select": st.column_config.CheckboxColumn(required=True),
            "Filename": st.column_config.TextColumn(width="large"),
            "Size (KB)": st.column_config.NumberColumn(format="%.2f"),
            "Pages": st.column_config.NumberColumn(width="small")
        })

        # Buttons for actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Analyze Document"):
                selected_files = edited_df[edited_df['Select']]['Filename'].tolist()
                if selected_files:
                    with st.spinner("Processing document..."):
                        # Get the first selected file
                        file_to_process = selected_files[0]
                        temp_file_path = os.path.join("./streamlit_functions/manual_docs", file_to_process)
                        
                        # Process the document
                        asyncio.run(process_document(temp_file_path))
                        
                        st.session_state.processing_complete = True
                    
                    st.success("Document processed successfully!")
                else:
                    st.warning("Please select a document to analyze.")

        with col2:
            if st.button("Delete Selected Files"):
                selected_files = edited_df[edited_df['Select']]['Filename'].tolist()
                if selected_files:
                    for file in selected_files:
                        os.remove(os.path.join("./streamlit_functions/manual_docs", file))
                    st.success(f"Deleted {len(selected_files)} file(s).")
                    st.rerun()
                else:
                    st.warning("Please select files to delete.")

        with col3:
            if st.button("View PDF" if not st.session_state.show_pdf else "Hide PDF"):
                st.session_state.show_pdf = not st.session_state.show_pdf

        # PDF Viewer
        if st.session_state.show_pdf:
            selected_files = edited_df[edited_df['Select']]['Filename'].tolist()
            if selected_files:
                file_to_view = selected_files[0]
                file_path = os.path.join("./streamlit_functions/manual_docs", file_to_view)
                
                # Open the PDF file once
                with open(file_path, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    total_pages = len(pdf_reader.pages)
                
                    # Page slider
                    st.session_state.current_page = st.slider("Page", 1, total_pages, st.session_state.current_page)
                    
                    # Extract and save the selected page
                    pdf_writer = PdfWriter()
                    pdf_writer.add_page(pdf_reader.pages[st.session_state.current_page - 1])
                    temp_file_path = os.path.join("./streamlit_functions/manual_docs", f"temp_{file_to_view}")
                    with open(temp_file_path, "wb") as temp_f:
                        pdf_writer.write(temp_f)
                
                # Display current page
                pdf_viewer(temp_file_path)
                st.write(f"Showing page {st.session_state.current_page} of {total_pages}")
                
                # Clean up temporary file
                os.remove(temp_file_path)
            else:
                st.warning("Please select a file to view.")

    else:
        st.info("No files uploaded yet.")

    # Display bullet points if processing is complete
    if st.session_state.processing_complete:
        st.subheader("Extracted Bullet Points")
        
        try:
            with open('bullet_points.json', 'r') as f:
                bullet_points_data = json.load(f)
            
            # Group bullet points by topics
            grouped_bullet_points = {}
            for bullet_point in bullet_points_data['list_bullet_points']:
                for topic in bullet_point['topics']:
                    if topic not in grouped_bullet_points:
                        grouped_bullet_points[topic] = []
                    grouped_bullet_points[topic].append(bullet_point)

            # Calculate topic counts
            topic_counts = {topic: len(bullet_points) for topic, bullet_points in grouped_bullet_points.items()}

            # Add a slider for filtering topics
            min_bullet_points = st.slider("Minimum number of bullet points per topic", 1, max(topic_counts.values()), 1)

            # Filter topics based on the slider value
            filtered_topics = {topic: count for topic, count in topic_counts.items() if count >= min_bullet_points}

            # Update the bar chart to use filtered topics
            fig = go.Figure(data=[go.Bar(x=list(filtered_topics.keys()), y=list(filtered_topics.values()))])
            fig.update_layout(title='Topics and Number of Bullet Points', xaxis_title='Topics', yaxis_title='Number of Bullet Points')
            st.plotly_chart(fig)

            # Display grouped bullet points (filtered)
            for topic, bullet_points in grouped_bullet_points.items():
                if len(bullet_points) >= min_bullet_points:
                    with st.expander(f"Topic: {topic} ({len(bullet_points)} bullet points)"):
                        for bullet_point in bullet_points:
                            st.markdown(f"**{bullet_point['name']}** (Page {bullet_point['pagenum']})")
                            st.write(f"**Text:** {bullet_point['text']}")
                            st.write(f"**Description:** {bullet_point['description']}")
                            st.write(f"**Context:** {bullet_point['context']}")
                            st.divider()
        except FileNotFoundError:
            st.error("bullet_points.json file not found. Please ensure the document was processed correctly.")

# Run the Streamlit app
if __name__ == "__main__":
    main()