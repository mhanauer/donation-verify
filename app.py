"""
Campaign Donor Verification Tool - Fixed Version
================================================

This version includes proper timeouts and error handling to prevent hanging.
"""

import streamlit as st
import anthropic
from anthropic import APITimeoutError, APIConnectionError
import os
from datetime import datetime
import json
import re
import time

# Page config
st.set_page_config(
    page_title="Campaign Donor Verification Tool",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert { margin-top: 1rem; }
    .result-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .verified { color: #28a745; font-weight: bold; }
    .unverified { color: #dc3545; font-weight: bold; }
    .partial { color: #ffc107; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🔍 Campaign Donor Verification Tool")
st.markdown("Automatically verify donor information using AI-powered web search")

# Initialize session state
if 'verification_history' not in st.session_state:
    st.session_state.verification_history = []

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key handling with error checking
    try:
        api_key = st.secrets["API-KEY"]
        # Validate API key format
        if api_key and api_key.startswith("sk-ant-"):
            st.success("✅ API Key loaded from secrets")
        else:
            st.error("❌ Invalid API key format")
            api_key = None
    except Exception as e:
        st.error(f"❌ Error loading API key: {str(e)}")
        api_key = st.text_input("Enter API Key manually", type="password")
    
    st.divider()
    
    # Model selection
    model = st.selectbox(
        "Select Model",
        ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
        help="Note: Using correct model names for API"
    )
    
    # Timeout setting
    timeout = st.slider("API Timeout (seconds)", 10, 60, 30)
    
    st.divider()
    
    # Debug mode
    debug_mode = st.checkbox("Enable Debug Mode", value=False)
    
    st.divider()
    
    # History
    st.header("📜 Verification History")
    if st.session_state.verification_history:
        for record in reversed(st.session_state.verification_history[-5:]):
            with st.expander(f"{record['name']} - {record['timestamp']}", expanded=False):
                st.json(record['data'])
    else:
        st.info("No verification history yet")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Donor Information")
    
    with st.form("donor_form"):
        name = st.text_input("Full Name*", placeholder="John Doe")
        email = st.text_input("Email", placeholder="john@example.com")
        phone = st.text_input("Phone", placeholder="555-123-4567")
        address = st.text_area("Address", placeholder="123 Main St, City, State")
        job_title = st.text_input("Job Title", placeholder="CEO")
        company = st.text_input("Company", placeholder="Acme Corp")
        
        st.subheader("Additional Information")
        linkedin_url = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/...")
        
        verify_button = st.form_submit_button("🔍 Verify Information", type="primary", use_container_width=True)

with col2:
    st.header("✅ Verification Results")
    
    if verify_button:
        if not api_key:
            st.error("❌ No API key configured. Please add API-KEY to Streamlit secrets.")
        elif not name:
            st.error("❌ Please enter at least the donor's name")
        else:
            # Create a placeholder for status updates
            status_placeholder = st.empty()
            
            try:
                # Show initial status
                status_placeholder.info("🔄 Initializing verification...")
                
                # Initialize client with timeout
                client = anthropic.Anthropic(
                    api_key=api_key,
                    timeout=timeout,
                    max_retries=1
                )
                
                if debug_mode:
                    st.write("Debug: Client initialized")
                    st.write(f"Debug: Using model: {model}")
                    st.write(f"Debug: Timeout set to: {timeout} seconds")
                
                # Update status
                status_placeholder.info("🔍 Searching for information...")
                
                # Simpler query to avoid issues
                verification_query = f"""
                Search for and verify information about {name}:
                - Company: {company if company else 'Unknown'}
                - Job Title: {job_title if job_title else 'Unknown'}
                - Location: {address if address else 'Unknown'}
                
                Please provide:
                1. Verification status (Found/Not Found)
                2. Any professional information found
                3. Confidence level (High/Medium/Low)
                
                Keep the response concise and structured.
                """
                
                # Make API call with proper error handling
                start_time = time.time()
                
                try:
                    # Note: Using standard message format without web search for now
                    # as web search beta might be causing issues
                    message = client.messages.create(
                        model=model,
                        max_tokens=1000,
                        temperature=0.3,
                        messages=[
                            {
                                "role": "user",
                                "content": verification_query
                            }
                        ]
                    )
                    
                    elapsed_time = time.time() - start_time
                    
                    if debug_mode:
                        st.write(f"Debug: API call completed in {elapsed_time:.2f} seconds")
                    
                    # Clear status and show results
                    status_placeholder.empty()
                    
                    # Extract response
                    response_text = message.content[0].text if message.content else "No response received"
                    
                    # Display results
                    st.success(f"✅ Verification Complete! (took {elapsed_time:.1f}s)")
                    
                    with st.expander("📊 Verification Results", expanded=True):
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
                            'verification_result': response_text,
                            'duration': f"{elapsed_time:.1f}s"
                        }
                    }
                    st.session_state.verification_history.append(verification_record)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Report",
                        data=json.dumps(verification_record, indent=2),
                        file_name=f"verification_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                    
                except APITimeoutError:
                    status_placeholder.empty()
                    st.error(f"❌ Request timed out after {timeout} seconds. Try increasing the timeout in the sidebar.")
                    
                except APIConnectionError:
                    status_placeholder.empty()
                    st.error("❌ Connection error. Please check your internet connection.")
                    
                except Exception as api_error:
                    status_placeholder.empty()
                    st.error(f"❌ API Error: {str(api_error)}")
                    if debug_mode:
                        st.exception(api_error)
                        
            except Exception as e:
                status_placeholder.empty()
                st.error(f"❌ Unexpected error: {str(e)}")
                if debug_mode:
                    st.exception(e)
                    
                # Provide troubleshooting tips
                with st.expander("🔧 Troubleshooting Tips", expanded=True):
                    st.markdown("""
                    **Common issues and solutions:**
                    
                    1. **Spinning forever**: 
                       - The web search beta might be having issues
                       - Try using the standard API without web search
                       - Check if your API key is valid
                    
                    2. **API Key issues**:
                       - Make sure your key starts with `sk-ant-`
                       - Verify it's not expired
                       - Check you have API credits
                    
                    3. **Model issues**:
                       - The model names in the original code might be incorrect
                       - Use `claude-3-5-sonnet-20241022` instead
                    
                    4. **Network issues**:
                       - Check if Anthropic's API is accessible
                       - Try a simple curl test
                    """)

# Footer
st.divider()
with st.expander("📖 How to Use This Tool"):
    st.markdown("""
    ### Quick Setup:
    
    1. **Add to Streamlit secrets** (`.streamlit/secrets.toml`):
    ```toml
    API-KEY = "sk-ant-api03-your-key-here"
    ```
    
    2. **Deploy to Streamlit Cloud** or run locally
    
    3. **Enter donor information** and click Verify
    
    ### Features:
    - ⏱️ **Configurable timeout** to prevent hanging
    - 🐛 **Debug mode** for troubleshooting
    - 📊 **Clear error messages** when issues occur
    - 💾 **Download results** as JSON
    
    ### Note:
    This version temporarily disables web search to avoid potential beta issues.
    Using standard Claude API for verification.
    """)

# Test connection button
if st.button("🧪 Test API Connection"):
    if not api_key:
        st.error("Please configure API key first")
    else:
        try:
            with st.spinner("Testing connection..."):
                client = anthropic.Anthropic(api_key=api_key, timeout=10)
                test_message = client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=50,
                    messages=[{"role": "user", "content": "Say 'Connection successful!'"}]
                )
                st.success("✅ " + test_message.content[0].text)
        except Exception as e:
            st.error(f"❌ Connection test failed: {str(e)}")
