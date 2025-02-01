import streamlit as st
import requests
import json
from typing import List

st.set_page_config(page_title="Company Chatbot", page_icon="💬")

def upload_documents(files, company_id: str):
    """Upload documents to the backend"""
    files_data = [('files', file) for file in files]
    response = requests.post(
        f"http://localhost:8000/setup/{company_id}",
        files=files_data
    )
    return response.json()

def send_message(message: str, company_id: str):
    """Send message to chatbot"""
    response = requests.post(
        "http://localhost:8000/chat",
        json={"message": message, "company_id": company_id}
    )
    return response.json()

def get_analytics(company_id: str):
    """Get company analytics"""
    response = requests.get(f"http://localhost:8000/analytics/{company_id}")
    return response.json()

# Sidebar Configuration
with st.sidebar:
    st.header("Setup")
    company_id = st.text_input("Company ID", value="test-company")
    
    # Document Upload
    uploaded_files = st.file_uploader(
        "Upload Company Documents", 
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt']
    )
    
    if uploaded_files and st.button("Upload Documents"):
        with st.spinner("Processing documents..."):
            result = upload_documents(uploaded_files, company_id)
            st.success("Documents uploaded successfully!")
    
    # Display Options
    st.header("Display Options")
    display_context = st.checkbox("Show Source Context", value=False)
    display_source = st.checkbox("Show Document Source", value=True)
    
    # Analytics
    if st.checkbox("Show Analytics", value=False):
        try:
            analytics = get_analytics(company_id)
            st.write("Total Interactions:", analytics.get("total_interactions", 0))
            st.write("Average Confidence:", f"{analytics.get('average_confidence', 0):.2%}")
        except Exception as e:
            st.error(f"Error fetching analytics: {str(e)}")

# Main Chat Interface
st.title("🤖 Company Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if message["role"] == "assistant":
            # Show source information if available and enabled
            if display_source and "source" in message:
                st.info(f"📚 {message['source']}")
            
            # Show context if enabled
            if display_context and "context" in message:
                with st.expander("📄 View Full Context"):
                    st.markdown("---")
                    st.markdown(message["context"])

# Chat input
if prompt := st.chat_input("Ask something about the company..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get and display bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = send_message(prompt, company_id)
                if isinstance(response, dict):
                    # Display main response
                    st.markdown(response.get("response", "Sorry, I couldn't process that request."))
                    
                    # Show source information if available
                    if display_source and "source" in response:
                        st.info(f"📚 {response['source']}")
                    
                    # Show context if enabled
                    if display_context and "context" in response:
                        with st.expander("📄 View Full Context"):
                            st.markdown("---")
                            st.markdown(response["context"])
                    
                    if "confidence" in response:
                        st.caption(f"Confidence: {float(response['confidence']):.2%}")
                else:
                    st.error("Received unexpected response format")
            except requests.exceptions.RequestException as e:
                st.error(f"Error communicating with backend: {str(e)}")
    
    if isinstance(response, dict):
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response.get("response", "Sorry, I couldn't process that request."),
            "context": response.get("context", ""),
            "source": response.get("source", "")
        })