"""
Campaign Donor Verification Tool - Streamlit Community Version
==============================================================
Uses st.secrets for API key management
"""

import streamlit as st
import anthropic
import os
from datetime import datetime
import json
import re
import pandas as pd

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

# Get API key from secrets
try:
    api_key = st.secrets["API-KEY"]
    api_key_status = True
except Exception as e:
    api_key = None
    api_key_status = False
    st.error("❌ API Key not found in secrets. Please add 'API-KEY' to your Streamlit app secrets.")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key status
    if api_key_status:
        st.success("✅ API Key loaded from secrets")
    else:
        st.error("❌ API Key not configured")
        with st.expander("How to add API key"):
            st.markdown("""
            1. Go to your app settings in Streamlit Cloud
            2. Navigate to 'Secrets' section
            3. Add:
            ```
            API-KEY = "sk-ant-api03-your-key-here"
            ```
            """)
    
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
        # Clear history button
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.verification_history = []
            st.rerun()
        
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
    
    if verify_button:
        if not api_key:
            st.error("❌ API Key not configured. Please add it to your Streamlit app secrets.")
        elif not name:
            st.error("❌ Please enter at least the donor's name")
        else:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Update progress
                progress_bar.progress(10)
                status_text.text("🔄 Initializing client...")
                
                # Initialize Anthropic client
                client = anthropic.Anthropic(api_key=api_key)
                
                # Update progress
                progress_bar.progress(30)
                status_text.text("🔍 Preparing verification query...")
                
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
                
                # Update progress
                progress_bar.progress(50)
                status_text.text("🌐 Performing web search verification...")
                
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
                
                # Update progress
                progress_bar.progress(90)
                status_text.text("📊 Processing results...")
                
                # Parse response
                response_text = message.content[0].text if message.content else "No response received"
                
                # Complete progress
                progress_bar.progress(100)
                status_text.empty()
                progress_bar.empty()
                
                # Display results
                st.success("✅ Verification Complete!")
                
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
                col_download1, col_download2 = st.columns(2)
                with col_download1:
                    st.download_button(
                        label="📥 Download as JSON",
                        data=json.dumps(verification_record, indent=2),
                        file_name=f"verification_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                with col_download2:
                    # Create a simple text report
                    text_report = f"""DONOR VERIFICATION REPORT
========================
Generated: {verification_record['timestamp']}

DONOR INFORMATION:
Name: {name}
Email: {email}
Phone: {phone}
Address: {address}
Job Title: {job_title}
Company: {company}
LinkedIn: {linkedin_url}

VERIFICATION RESULTS:
{response_text}
"""
                    st.download_button(
                        label="📄 Download as Text",
                        data=text_report,
                        file_name=f"verification_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
            except Exception as e:
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                st.error(f"❌ Error during verification: {str(e)}")
                
                # Provide specific error guidance
                if "api_key" in str(e).lower():
                    st.info("🔑 This appears to be an API key issue. Please verify your API key is correct.")
                elif "rate" in str(e).lower():
                    st.info("⏱️ You may have hit a rate limit. Please wait a moment and try again.")
                elif "timeout" in str(e).lower():
                    st.info("⌛ The request timed out. Please try again.")
                else:
                    st.info("Please check your configuration and try again.")

# Footer with instructions
st.divider()
with st.expander("📖 How to Use This Tool"):
    st.markdown("""
    ### Setup Instructions:
    1. **Deploy to Streamlit Community Cloud**
    2. **Add your API key to Secrets**:
       - Go to app settings → Secrets
       - Add: `API-KEY = "sk-ant-api03-your-key-here"`
    3. **Start verifying donors!**
    
    ### Features:
    - 🔍 **Web Search Verification**: Uses Claude's web search to find public information
    - 📊 **Structured Results**: Get clear verification status for each field
    - 📜 **History Tracking**: Keep track of recent verifications
    - 💾 **Export Options**: Download as JSON or text file
    - 🔐 **Secure**: API key stored in Streamlit secrets
    
    ### Tips:
    - The more information you provide, the better the verification
    - LinkedIn URLs can help with professional verification
    - The tool searches public information only
    - Results show confidence levels to help you assess reliability
    """)

# Batch processing section
st.divider()
with st.expander("📋 Batch Processing"):
    st.markdown("### Upload CSV for Batch Verification")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv",
        help="CSV should have columns: name, email, phone, address, job_title, company"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
            
            if st.button("🚀 Start Batch Verification", type="primary") and api_key:
                # Create a container for batch results
                batch_container = st.container()
                
                with batch_container:
                    st.info(f"Processing {len(df)} records...")
                    
                    # Progress bar for batch processing
                    batch_progress = st.progress(0)
                    results = []
                    
                    # Process each row
                    for idx, row in df.iterrows():
                        try:
                            # Update progress
                            progress = (idx + 1) / len(df)
                            batch_progress.progress(progress)
                            
                            # Extract data from row
                            donor_name = row.get('name', '')
                            if not donor_name:
                                continue
                            
                            # Create verification query
                            query = f"""
                            Please verify: {donor_name}
                            Company: {row.get('company', 'Not provided')}
                            Job Title: {row.get('job_title', 'Not provided')}
                            Email: {row.get('email', 'Not provided')}
                            
                            Provide a brief verification summary.
                            """
                            
                            # Make API call
                            client = anthropic.Anthropic(api_key=api_key)
                            message = client.beta.messages.create(
                                model=model,
                                max_tokens=500,  # Shorter for batch processing
                                temperature=0.3,
                                messages=[{"role": "user", "content": query}],
                                tools=[{"name": "web_search", "type": "web_search_20250305"}],
                                betas=["web-search-2025-03-05"]
                            )
                            
                            # Store result
                            result = {
                                'name': donor_name,
                                'status': 'Verified',
                                'details': message.content[0].text if message.content else 'No response'
                            }
                            results.append(result)
                            
                        except Exception as e:
                            results.append({
                                'name': donor_name,
                                'status': 'Error',
                                'details': str(e)
                            })
                    
                    # Clear progress bar
                    batch_progress.empty()
                    
                    # Display results
                    st.success(f"✅ Batch processing complete! Processed {len(results)} records.")
                    
                    # Convert results to dataframe
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df)
                    
                    # Download batch results
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Batch Results",
                        data=csv,
                        file_name=f"batch_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")

# App info in sidebar
with st.sidebar:
    st.divider()
    st.markdown("### 📱 App Info")
    st.info("""
    **Version**: 1.0.0
    **Model**: Claude Web Search
    **Python**: 3.11 recommended
    """)
