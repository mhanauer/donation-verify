"""
Campaign Donor Verification Tool - Minimal Version
==================================================
Simple and clean with just the essentials
"""

import streamlit as st
import anthropic
import os
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Campaign Donor Verification Tool",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 Campaign Donor Verification Tool")
st.markdown("Verify donor information using Claude's web search")

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'prefill_data' not in st.session_state:
    st.session_state.prefill_data = {
        'name': "Matthew Hanauer",
        'company': "MedeAnalytics",
        'job_title': "Senior Director Data Science",
        'email': "matthewhanauer99@gmail.com",
        'phone': "260-409-5700",
        'address': "730 Crestview Drive, Durham, NC 27712"
    }

# Get API key from secrets
try:
    api_key = st.secrets["API-KEY"]
    api_configured = True
    # Debug: Check API key format
    if api_key:
        # Remove any accidental spaces or quotes
        api_key = api_key.strip().strip('"').strip("'")
        # Also set as environment variable as backup
        os.environ["ANTHROPIC_API_KEY"] = api_key
        # Validate format
        if not api_key.startswith("sk-ant-"):
            st.sidebar.error("❌ API key should start with 'sk-ant-'")
            api_configured = False
except:
    api_key = None
    api_configured = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    if api_configured:
        st.success("✅ API Key configured")
        # Show partial key for debugging
        if api_key:
            st.text(f"Key preview: {api_key[:20]}...")
            st.text(f"Key length: {len(api_key)} chars")
    else:
        st.error("❌ Add API-KEY to secrets")
        with st.expander("Setup Help"):
            st.markdown("""
            In Streamlit secrets, add:
            ```
            API-KEY = "sk-ant-api03-xxxxx"
            ```
            Make sure:
            - No extra quotes
            - No spaces before/after
            - Starts with sk-ant-api03-
            """)
    
    model = st.selectbox(
        "Model",
        ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]
    )
    
    # Test button
    if st.button("🧪 Test API Key") and api_key:
        try:
            test_client = anthropic.Anthropic(api_key=api_key)
            # Use a basic model to test
            test_msg = test_client.messages.create(
                model="claude-3-haiku-3-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            st.success("✅ API key is valid!")
        except Exception as e:
            st.error(f"❌ API test failed: {str(e)}")
            if "401" in str(e):
                st.warning("Check your API key in secrets")
    
    if st.session_state.history:
        st.divider()
        st.header("📜 Recent")
        for item in st.session_state.history[-3:]:
            st.text(f"• {item['name']} ({item['time']})")

# Main columns
col1, col2 = st.columns(2)

with col1:
    st.header("📝 Donor Information")
    
    name = st.text_input("Name*", value=st.session_state.prefill_data['name'])
    company = st.text_input("Company", value=st.session_state.prefill_data['company'])
    job_title = st.text_input("Job Title", value=st.session_state.prefill_data['job_title'])
    email = st.text_input("Email", value=st.session_state.prefill_data['email'])
    phone = st.text_input("Phone", value=st.session_state.prefill_data['phone'])
    address = st.text_input("Address", value=st.session_state.prefill_data['address'])
    
    verify_btn = st.button("🔍 Verify", type="primary", use_container_width=True)

with col2:
    st.header("✅ Results")
    
    if verify_btn and name and api_configured:
        start_time = datetime.now()
        with st.spinner("Verifying..."):
            try:
                # Create client
                client = anthropic.Anthropic(api_key=api_key)
                
                # Simple query
                query = f"""You have web search capabilities. Please search for information about {name} and verify the following details:

PROVIDED INFORMATION TO VERIFY:
- Company: {company or 'Not provided'}
- Job Title: {job_title or 'Not provided'}
- Email: {email or 'Not provided'}
- Phone: {phone or 'Not provided'}
- Address: {address or 'Not provided'}

INSTRUCTIONS:
1. Use web search to find current information about this person
2. Compare what you find with the provided information
3. For each piece of information, indicate:
   - VERIFIED ✓ if it matches what you found
   - UNVERIFIED ✗ if you couldn't find information to confirm it
   - INCORRECT ⚠️ if it contradicts what you found

Please provide a clear verification report with your findings."""
                
                # API call with web search
                message = client.beta.messages.create(
                    model=model,
                    max_tokens=3000,
                    temperature=0,
                    messages=[{"role": "user", "content": query}],
                    tools=[{"name": "web_search", "type": "web_search_20250305"}],
                    betas=["web-search-2025-03-05"]
                )
                
                # Get response
                result = message.content[0].text if message.content else "No response"
                
                # Calculate elapsed time
                elapsed_time = (datetime.now() - start_time).total_seconds()
                
                # Show results
                st.success(f"✅ Verification complete! (took {elapsed_time:.1f} seconds)")
                
                # Display results in an organized way
                with st.container():
                    st.subheader("📊 Verification Report")
                    
                    # Show the full response
                    with st.expander("Detailed Findings", expanded=True):
                        st.markdown(result)
                    
                    # Quick summary based on keywords in result
                    verified_count = result.lower().count('verified')
                    unverified_count = result.lower().count('unverified')
                    incorrect_count = result.lower().count('incorrect')
                    
                    # Status summary
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Verified", f"{verified_count} items")
                    with col_stat2:
                        st.metric("Unverified", f"{unverified_count} items")
                    with col_stat3:
                        st.metric("Incorrect", f"{incorrect_count} items")
                
                # Save to history
                st.session_state.history.append({
                    'name': name,
                    'time': datetime.now().strftime("%H:%M"),
                    'result': result
                })
                
                # Download button with enhanced data
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'donor': {
                        'name': name,
                        'company': company,
                        'job_title': job_title,
                        'email': email,
                        'phone': phone,
                        'address': address
                    },
                    'verification': {
                        'full_report': result,
                        'summary': {
                            'verified_items': verified_count,
                            'unverified_items': unverified_count,
                            'incorrect_items': incorrect_count
                        }
                    }
                }
                
                st.download_button(
                    "📥 Download",
                    json.dumps(data, indent=2),
                    f"{name.replace(' ', '_')}_verification.json",
                    "application/json"
                )
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
                
                # Provide helpful guidance based on error type
                if "web_search" in str(e).lower():
                    st.info("💡 The web search feature might be temporarily unavailable. Try again in a moment.")
                elif "401" in str(e):
                    st.warning("🔑 Authentication issue. Check your API key in Streamlit secrets.")
                elif "rate" in str(e).lower():
                    st.warning("⏱️ Rate limit reached. Please wait a moment before trying again.")
                else:
                    st.info("💡 If this persists, try using a different model or check your internet connection.")
                
                # Debug help for common errors
                if "401" in str(e) or "authentication" in str(e).lower():
                    st.warning("🔑 API Key Issue Detected")
                    st.info("""
                    Please check:
                    1. Your API key in Streamlit secrets is correct
                    2. No extra spaces or quotes around the key
                    3. Key starts with 'sk-ant-api03-'
                    4. Key hasn't expired
                    
                    Current key preview: {}...
                    """.format(api_key[:20] if api_key else "Not set"))
                elif "404" in str(e):
                    st.warning("Model might not be available. Try the Test API button.")
                elif "rate" in str(e).lower():
                    st.warning("Rate limit hit. Wait a moment and try again.")
    
    elif verify_btn and not name:
        st.warning("Please enter a name")
    elif verify_btn and not api_configured:
        st.error("API key not configured")

# Footer
st.divider()
with st.expander("🔧 Troubleshooting 401 Error"):
    st.markdown("""
    **If you're getting a 401 authentication error:**
    
    1. **Check your Streamlit secrets format:**
       ```toml
       API-KEY = "sk-ant-api03-your-actual-key-here"
       ```
       
    2. **Common mistakes to avoid:**
       - ❌ `API-KEY = sk-ant-api03-xxx` (missing quotes)
       - ❌ `API-KEY = "sk-ant-api03-xxx"` (if xxx is not your real key)
       - ❌ `API-KEY = "'sk-ant-api03-xxx'"` (extra quotes)
       - ❌ `API-KEY = " sk-ant-api03-xxx "` (extra spaces)
       - ✅ `API-KEY = "sk-ant-api03-your-actual-key"`
    
    3. **Get your API key from:**
       - Console: https://console.anthropic.com/
       - Look for API keys section
       - Create new key if needed
    
    4. **Use the Test API Key button** in the sidebar to verify
    """)

st.markdown("""
**Quick Start:** Add `API-KEY = "sk-ant-api03-..."` to Streamlit secrets  
**Usage:** Enter donor info → Click Verify → Download results
""")
