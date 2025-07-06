import streamlit as st
import anthropic
import os
from datetime import datetime
import json
import re

# Page config
st.set_page_config(
    page_title="Campaign Donor Verification Tool",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stAlert {
        margin-top: 1rem;
    }
    .result-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .verified {
        color: #28a745;
        font-weight: bold;
    }
    .unverified {
        color: #dc3545;
        font-weight: bold;
    }
    .partial {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🔍 Campaign Donor Verification Tool")
st.markdown("Automatically verify donor information using AI-powered web search")

# Initialize session state
if 'verification_history' not in st.session_state:
    st.session_state.verification_history = []

# Sidebar for API key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        help="Enter your Anthropic API key to use the web search feature"
    )
    
    if api_key:
        st.success("✅ API Key configured")
    else:
        st.warning("⚠️ Please enter your API key to proceed")
    
    st.divider()
    
    # Model selection
    model = st.selectbox(
        "Select Model",
        ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        help="Choose the Claude model to use for verification"
    )
    
    st.divider()
    
    # History section
    st.header("📜 Verification History")
    if st.session_state.verification_history:
        for i, record in enumerate(reversed(st.session_state.verification_history[-5:])):
            with st.expander(f"{record['name']} - {record['timestamp']}", expanded=False):
                st.json(record['data'])
    else:
        st.info("No verification history yet")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Donor Information")
    
    # Input form
    with st.form("donor_form"):
        name = st.text_input("Full Name", placeholder="Matthew Hanauer")
        email = st.text_input("Email", placeholder="matthewhanauer99@gmail.com")
        phone = st.text_input("Phone", placeholder="260-409-5700")
        address = st.text_area("Address", placeholder="730 Crestview Drive, Durham, NC 27712")
        job_title = st.text_input("Job Title", placeholder="Senior Director Data Science")
        company = st.text_input("Company", placeholder="MedeAnalytics")
        
        # Additional fields
        st.subheader("Additional Information (Optional)")
        linkedin_url = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/...")
        notes = st.text_area("Notes", placeholder="Any additional information...")
        
        verify_button = st.form_submit_button("🔍 Verify Information", type="primary", use_container_width=True)

with col2:
    st.header("✅ Verification Results")
    
    if verify_button and api_key:
        if not name:
            st.error("Please enter at least the donor's name")
        else:
            with st.spinner("🔄 Verifying donor information..."):
                try:
                    # Initialize Anthropic client
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    # Prepare the verification query
                    verification_query = f"""
                    Please verify the following information about {name}:
                    
                    Name: {name}
                    Email: {email if email else 'Not provided'}
                    Phone: {phone if phone else 'Not provided'}
                    Address: {address if address else 'Not provided'}
                    Job Title: {job_title if job_title else 'Not provided'}
                    Company: {company if company else 'Not provided'}
                    LinkedIn: {linkedin_url if linkedin_url else 'Not provided'}
                    
                    Please search for information about this person and verify:
                    1. Is this person's job title and company correct?
                    2. Can you find any professional information about them?
                    3. Is the location (city/state) consistent with available information?
                    4. Are there any red flags or inconsistencies?
                    
                    Provide a structured response with:
                    - Verification status for each piece of information (Verified/Unable to Verify/Contradictory)
                    - Confidence level (High/Medium/Low)
                    - Any additional relevant information found
                    - Sources used for verification
                    """
                    
                    # Make API call with web search
                    message = client.beta.messages.create(
                        model=model,
                        max_tokens=2000,
                        temperature=0.3,
                        messages=[
                            {
                                "role": "user",
                                "content": verification_query
                            }
                        ],
                        tools=[
                            {
                                "name": "web_search",
                                "type": "web_search_20250305"
                            }
                        ],
                        betas=["web-search-2025-03-05"]
                    )
                    
                    # Display results
                    st.success("✅ Verification Complete!")
                    
                    # Parse and display the response
                    response_text = message.content[0].text if message.content else "No response received"
                    
                    # Create expandable sections for results
                    with st.expander("📊 Verification Summary", expanded=True):
                        st.markdown(response_text)
                    
                    # Store in history
                    verification_record = {
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'name': name,
                        'data': {
                            'input': {
                                'name': name,
                                'email': email,
                                'phone': phone,
                                'address': address,
                                'job_title': job_title,
                                'company': company,
                                'linkedin': linkedin_url
                            },
                            'verification_result': response_text
                        }
                    }
                    st.session_state.verification_history.append(verification_record)
                    
                    # Download button for results
                    st.download_button(
                        label="📥 Download Verification Report",
                        data=json.dumps(verification_record, indent=2),
                        file_name=f"verification_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error during verification: {str(e)}")
                    st.info("Please check your API key and try again.")
    
    elif verify_button and not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar to use the verification feature.")

# Footer with instructions
st.divider()
with st.expander("📖 How to Use This Tool"):
    st.markdown("""
    ### Instructions:
    1. **Enter your Anthropic API key** in the sidebar (required for web search functionality)
    2. **Fill in the donor information** you want to verify
    3. **Click "Verify Information"** to start the verification process
    4. **Review the results** which will show what could be verified
    5. **Download the report** for your records
    
    ### Features:
    - 🔍 **Web Search Verification**: Uses Claude's web search to find public information
    - 📊 **Structured Results**: Get clear verification status for each field
    - 📜 **History Tracking**: Keep track of all verifications
    - 💾 **Export Reports**: Download verification results as JSON files
    
    ### Tips:
    - The more information you provide, the better the verification
    - LinkedIn URLs can help with professional verification
    - The tool searches public information only
    - Results show confidence levels to help you assess reliability
    """)

# Batch processing section
st.divider()
with st.expander("📋 Batch Processing (Beta)"):
    st.markdown("### Upload CSV for Batch Verification")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="CSV should have columns: name, email, phone, address, job_title, company"
    )
    
    if uploaded_file is not None:
        import pandas as pd
        
        try:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
            
            if st.button("🚀 Start Batch Verification", type="primary"):
                st.info("Batch processing feature coming soon!")
                # TODO: Implement batch processing logic
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
