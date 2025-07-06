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
st.markdown("Verify job titles and company affiliations using Claude's web search")

# What this tool does
with st.expander("ℹ️ What this tool does", expanded=False):
    st.markdown("""
    This tool helps you verify donor information by:
    1. **Searching the web** for information about the person
    2. **Showing you what was found** in the search results
    3. **Comparing** the provided information with search findings
    4. **Assessing confidence** in the job title and company verification
    
    The tool provides nuanced assessments (not just yes/no) with confidence levels ranging from HIGH to CANNOT CONFIRM.
    """)

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
    
    st.markdown("**Key Information to Verify:**")
    name = st.text_input("Name*", value=st.session_state.prefill_data['name'])
    company = st.text_input("Company", value=st.session_state.prefill_data['company'])
    job_title = st.text_input("Job Title", value=st.session_state.prefill_data['job_title'])
    
    # Initialize these variables even if in expander
    email = ""
    phone = ""  
    address = ""
    
    with st.expander("Additional Information (Optional)"):
        email = st.text_input("Email", value=st.session_state.prefill_data['email'])
        phone = st.text_input("Phone", value=st.session_state.prefill_data['phone'])
        address = st.text_input("Address", value=st.session_state.prefill_data['address'])
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        verify_btn = st.button("🔍 Verify", type="primary", use_container_width=True)
    with col_btn2:
        if st.button("🧹 Clear", use_container_width=True):
            st.session_state.prefill_data = {
                'name': "",
                'company': "",
                'job_title': "",
                'email': "",
                'phone': "",
                'address': ""
            }
            st.rerun()

with col2:
    st.header("✅ Results")
    
    if verify_btn and name and api_configured:
        start_time = datetime.now()
        with st.spinner("Verifying..."):
            try:
                # Create client
                client = anthropic.Anthropic(api_key=api_key)
                
                # Simple query
                query = f"""Search for information about {name} and provide a detailed verification report.

INFORMATION TO VERIFY:
- Name: {name}
- Company: {company or 'Not provided'}
- Job Title: {job_title or 'Not provided'}

YOUR TASK:
1. SEARCH: Use web search to find information about this person
2. SHOW FINDINGS: List exactly what you found in your search results (URLs, snippets, sources)
3. COMPARE: Compare the provided information with what you found
4. ASSESS CONFIDENCE: For the job title and company, provide a confidence assessment:
   - HIGH CONFIDENCE: Multiple reliable sources confirm this information
   - MODERATE CONFIDENCE: Some evidence supports this, but limited sources
   - LOW CONFIDENCE: Little or conflicting information found
   - CANNOT CONFIRM: No relevant information found

FORMAT YOUR RESPONSE AS:

**SEARCH FINDINGS:**
- List each relevant search result you found
- Include source names and what information each provided

**JOB TITLE VERIFICATION:**
Provided: {job_title or 'Not provided'}
Found: [What you actually found]
Confidence: [HIGH/MODERATE/LOW/CANNOT CONFIRM]
Explanation: [Why you have this confidence level]

**COMPANY VERIFICATION:**
Provided: {company or 'Not provided'}
Found: [What you actually found]
Confidence: [HIGH/MODERATE/LOW/CANNOT CONFIRM]
Explanation: [Why you have this confidence level]

**ADDITIONAL NOTES:**
Any other relevant information about this person"""
                
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
                
                # Check if web search was actually performed by looking for key indicators
                search_performed = any([
                    "SEARCH FINDINGS:" in result,
                    "Found:" in result,
                    "Confidence:" in result,
                    "sources" in result.lower(),
                    "search results" in result.lower()
                ])
                
                if not search_performed and ("I'll search" in result or "I will search" in result or "Let me search" in result):
                    st.warning("⚠️ The web search may not have completed properly.")
                    st.info("Try clicking Verify again. If this persists, try testing with a well-known person like 'Tim Cook' to ensure the search is working.")
                else:
                    # Show results
                    st.success(f"✅ Verification complete! (took {elapsed_time:.1f} seconds)")
                
                # Display results in an organized way
                with st.container():
                    st.subheader("📊 Verification Report")
                    
                    # Full report
                    st.markdown(result)
                    
                    # Extract confidence levels if present in the response
                    if "HIGH CONFIDENCE" in result:
                        st.success("🟢 High confidence in verification")
                    elif "MODERATE CONFIDENCE" in result:
                        st.warning("🟡 Moderate confidence in verification")
                    elif "LOW CONFIDENCE" in result:
                        st.error("🔴 Low confidence in verification")
                    elif "CANNOT CONFIRM" in result:
                        st.error("⚫ Cannot confirm information")
                
                # Save to history
                st.session_state.history.append({
                    'name': name,
                    'time': datetime.now().strftime("%H:%M"),
                    'result': result
                })
                
                # Download button with focused data
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'verification_duration_seconds': elapsed_time,
                    'donor_info': {
                        'name': name,
                        'company': company,
                        'job_title': job_title,
                        'email': email,
                        'phone': phone,
                        'address': address
                    },
                    'verification_report': result,
                    'confidence_indicators': {
                        'high_confidence': "HIGH CONFIDENCE" in result,
                        'moderate_confidence': "MODERATE CONFIDENCE" in result,
                        'low_confidence': "LOW CONFIDENCE" in result,
                        'cannot_confirm': "CANNOT CONFIRM" in result
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
