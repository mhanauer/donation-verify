"""
Campaign Donor Verification Tool - Debug Version
================================================
Uses the correct beta web search API with extensive debugging
"""

import streamlit as st
import anthropic
from datetime import datetime
import json
import time
import traceback

# Page config
st.set_page_config(
    page_title="Campaign Donor Verification Tool",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 Campaign Donor Verification Tool - Debug Version")
st.markdown("Verify donor information using Claude's web search")

# Initialize session state
if 'verification_history' not in st.session_state:
    st.session_state.verification_history = []
if 'debug_log' not in st.session_state:
    st.session_state.debug_log = []

# Function to add debug messages
def debug_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] {message}"
    st.session_state.debug_log.append(log_entry)
    return log_entry

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key
    api_key = None
    try:
        api_key = st.secrets["API-KEY"]
        st.success("✅ API Key loaded from secrets")
        # Show first few characters for verification
        st.text(f"Key starts with: {api_key[:15]}...")
    except Exception as e:
        st.error("❌ No API key in secrets")
        api_key = st.text_input("Enter API Key", type="password")
    
    st.divider()
    
    # Model selection
    model = st.selectbox(
        "Select Model",
        ["claude-sonnet-4-20250514", "claude-opus-4-20250514"],
        help="Using the new Claude 4 models"
    )
    
    # Timeout
    timeout = st.number_input("Timeout (seconds)", min_value=10, max_value=300, value=60)
    
    st.divider()
    
    # Debug options
    show_debug = st.checkbox("Show Debug Info", value=True)
    clear_debug = st.button("Clear Debug Log")
    if clear_debug:
        st.session_state.debug_log = []
        st.rerun()
    
    # Test button
    if st.button("🧪 Test API Connection"):
        with st.spinner("Testing..."):
            try:
                debug_log("Starting API test...")
                client = anthropic.Anthropic(api_key=api_key)
                
                # Test without web search first
                debug_log("Testing basic API call...")
                test_msg = client.messages.create(
                    model="claude-3-haiku-3-20240307",
                    max_tokens=50,
                    messages=[{"role": "user", "content": "Say 'Hello'"}]
                )
                debug_log(f"Basic API test successful: {test_msg.content[0].text}")
                
                # Test with web search
                debug_log("Testing web search API...")
                test_msg = client.beta.messages.create(
                    model=model,
                    max_tokens=100,
                    messages=[{"role": "user", "content": "What is 2+2?"}],
                    tools=[{"name": "web_search", "type": "web_search_20250305"}],
                    betas=["web-search-2025-03-05"]
                )
                debug_log("Web search API test successful!")
                st.success("✅ All API tests passed!")
                
            except Exception as e:
                debug_log(f"API test failed: {str(e)}")
                st.error(f"❌ Test failed: {str(e)}")

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Donor Information")
    
    # Simple form for testing
    name = st.text_input("Full Name", value="Tim Cook")
    company = st.text_input("Company", value="Apple")
    job_title = st.text_input("Job Title", value="CEO")
    
    verify_button = st.button("🔍 Verify Information", type="primary", use_container_width=True)

with col2:
    st.header("✅ Verification Results")
    
    # Debug log display
    if show_debug and st.session_state.debug_log:
        with st.expander("🐛 Debug Log", expanded=True):
            for log in st.session_state.debug_log[-20:]:  # Show last 20 entries
                st.text(log)
    
    if verify_button and api_key and name:
        # Clear previous debug logs for this run
        st.session_state.debug_log = []
        
        # Progress tracking
        progress_bar = st.progress(0)
        status = st.empty()
        
        try:
            # Step 1: Initialize
            debug_log("Starting verification process...")
            status.info("🔄 Initializing client...")
            progress_bar.progress(10)
            
            # Create client with explicit timeout
            client = anthropic.Anthropic(
                api_key=api_key,
                timeout=float(timeout),
                max_retries=1
            )
            debug_log(f"Client created with {timeout}s timeout")
            
            # Step 2: Prepare query
            status.info("🔍 Preparing search query...")
            progress_bar.progress(20)
            
            verification_query = f"""
            Please verify this information is correct:
            
            {name} is {job_title} at {company}.
            
            Use web search to find current information about this person and verify:
            1. Is the job title correct?
            2. Is the company correct?
            3. Any other relevant professional information?
            
            Provide a brief, structured response.
            """
            
            debug_log(f"Query prepared, length: {len(verification_query)} chars")
            
            # Step 3: Make API call
            status.info("🌐 Calling Claude API with web search...")
            progress_bar.progress(30)
            
            start_time = time.time()
            debug_log("Making API call...")
            
            try:
                # Use the exact format from Anthropic's documentation
                message = client.beta.messages.create(
                    model=model,
                    max_tokens=2000,
                    temperature=0.3,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": verification_query
                                }
                            ]
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
                
                elapsed = time.time() - start_time
                debug_log(f"API call completed in {elapsed:.2f}s")
                progress_bar.progress(90)
                
                # Step 4: Process results
                status.info("📊 Processing results...")
                
                if message.content:
                    response_text = message.content[0].text
                    debug_log(f"Response received, length: {len(response_text)} chars")
                else:
                    response_text = "No response content"
                    debug_log("Warning: No response content")
                
                progress_bar.progress(100)
                status.empty()
                progress_bar.empty()
                
                # Display results
                st.success(f"✅ Verification complete! (took {elapsed:.1f}s)")
                
                with st.expander("📊 Verification Results", expanded=True):
                    st.markdown(response_text)
                
                # Save to history
                verification_record = {
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'name': name,
                    'company': company,
                    'job_title': job_title,
                    'result': response_text,
                    'duration': f"{elapsed:.1f}s"
                }
                st.session_state.verification_history.append(verification_record)
                
                # Download button
                st.download_button(
                    "📥 Download Results",
                    json.dumps(verification_record, indent=2),
                    f"verification_{name.replace(' ', '_')}.json",
                    "application/json"
                )
                
            except Exception as api_error:
                elapsed = time.time() - start_time
                debug_log(f"API error after {elapsed:.2f}s: {str(api_error)}")
                debug_log(f"Error type: {type(api_error).__name__}")
                debug_log(f"Traceback: {traceback.format_exc()}")
                
                status.empty()
                progress_bar.empty()
                
                st.error(f"❌ API Error: {str(api_error)}")
                
                # Specific error handling
                if "timeout" in str(api_error).lower():
                    st.warning("The request timed out. Try increasing the timeout in the sidebar.")
                elif "api_key" in str(api_error).lower():
                    st.warning("There might be an issue with your API key.")
                elif "rate" in str(api_error).lower():
                    st.warning("You might have hit a rate limit. Wait a moment and try again.")
                
        except Exception as e:
            debug_log(f"Unexpected error: {str(e)}")
            debug_log(f"Traceback: {traceback.format_exc()}")
            
            status.empty()
            progress_bar.empty()
            
            st.error(f"❌ Unexpected error: {str(e)}")
            st.text("See debug log for details")

# Footer
with st.expander("📖 Troubleshooting"):
    st.markdown("""
    ### If the app is hanging:
    
    1. **Check the Debug Log** - Shows exactly where it's getting stuck
    2. **Test API Connection** - Use the test button in sidebar
    3. **Verify API Key** - Make sure it starts with `sk-ant-api03-`
    4. **Try shorter timeout** - Sometimes fails faster with useful error
    5. **Check Anthropic Status** - The API might be down
    
    ### Common issues:
    - **Hanging on "Calling Claude API"** - Network or API issues
    - **401 Error** - Invalid API key
    - **429 Error** - Rate limit hit
    - **Timeout** - Increase timeout or simplify query
    """)
