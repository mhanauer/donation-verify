"""
Campaign Donor Verification Tool - Minimal Version
==================================================
Simple and clean with just the essentials
"""

import streamlit as st
import anthropic
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

# Get API key from secrets
try:
    api_key = st.secrets["API-KEY"]
    api_configured = True
except:
    api_key = None
    api_configured = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    if api_configured:
        st.success("✅ API Key configured")
    else:
        st.error("❌ Add API-KEY to secrets")
    
    model = st.selectbox(
        "Model",
        ["claude-sonnet-4-20250514", "claude-opus-4-20250514"]
    )
    
    if st.session_state.history:
        st.divider()
        st.header("📜 Recent")
        for item in st.session_state.history[-3:]:
            st.text(f"• {item['name']} ({item['time']})")

# Main columns
col1, col2 = st.columns(2)

with col1:
    st.header("📝 Donor Information")
    
    name = st.text_input("Name*", placeholder="John Doe")
    company = st.text_input("Company", placeholder="Acme Corp")
    job_title = st.text_input("Job Title", placeholder="CEO")
    email = st.text_input("Email", placeholder="john@example.com")
    location = st.text_input("Location", placeholder="New York, NY")
    
    verify_btn = st.button("🔍 Verify", type="primary", use_container_width=True)

with col2:
    st.header("✅ Results")
    
    if verify_btn and name and api_configured:
        with st.spinner("Verifying..."):
            try:
                # Create client
                client = anthropic.Anthropic(api_key=api_key)
                
                # Simple query
                query = f"""Please verify this information about {name}:
                - Company: {company or 'Unknown'}
                - Title: {job_title or 'Unknown'}
                - Email: {email or 'Unknown'}
                - Location: {location or 'Unknown'}
                
                Use web search to check if this information is accurate.
                Provide a brief summary of what you found."""
                
                # API call with web search
                message = client.beta.messages.create(
                    model=model,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": query}],
                    tools=[{"name": "web_search", "type": "web_search_20250305"}],
                    betas=["web-search-2025-03-05"]
                )
                
                # Get response
                result = message.content[0].text if message.content else "No response"
                
                # Show results
                st.success("✅ Verification complete!")
                st.markdown(result)
                
                # Save to history
                st.session_state.history.append({
                    'name': name,
                    'time': datetime.now().strftime("%H:%M"),
                    'result': result
                })
                
                # Download button
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'donor': {
                        'name': name,
                        'company': company,
                        'job_title': job_title,
                        'email': email,
                        'location': location
                    },
                    'verification': result
                }
                
                st.download_button(
                    "📥 Download",
                    json.dumps(data, indent=2),
                    f"{name.replace(' ', '_')}_verification.json",
                    "application/json"
                )
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif verify_btn and not name:
        st.warning("Please enter a name")
    elif verify_btn and not api_configured:
        st.error("API key not configured")

# Footer
st.divider()
st.markdown("""
**Setup:** Add `API-KEY = "sk-ant-api03-..."` to Streamlit secrets  
**Usage:** Enter donor info → Click Verify → Download results
""")
