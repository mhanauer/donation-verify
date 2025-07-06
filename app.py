import streamlit as st
import requests
import json
from langchain_anthropic import ChatAnthropicMessages
from langchain.schema import SystemMessage, HumanMessage

# Page config
st.set_page_config(
    page_title="Donor Verification",
    page_icon="🔍",
    layout="centered"
)

st.title("🔍 Simple Donor Verification")
st.markdown("Search and verify donor information using Serper and Claude")

# Initialize Claude using secrets
try:
    anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
    serper_api_key = st.secrets["SERPER_API_KEY"]
    
    # Initialize Claude
    llm = ChatAnthropicMessages(
        model_name="claude-3-sonnet-20241022",  # Using current Claude 3 Sonnet model
        anthropic_api_key=anthropic_api_key,
        temperature=0.3,  # Lower temperature for more consistent verification
    )
except Exception as e:
    st.error("Please set ANTHROPIC_API_KEY and SERPER_API_KEY in your Streamlit secrets")
    st.error(f"Error: {str(e)}")
    st.stop()

# Helper functions
def search_with_serper(query: str) -> dict:
    """Search using Serper API"""
    url = "https://serpapi.com/search.json"
    params = {
        "q": query,
        "api_key": serper_api_key,
        "num": 5
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def compare_with_claude(provided_info: str, search_results: dict) -> str:
    """Use Claude to compare provided info with search results"""
    # Extract relevant information from search results
    search_summary = []
    if "organic_results" in search_results:
        for result in search_results.get("organic_results", [])[:5]:
            search_summary.append({
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "link": result.get("link", "")
            })
    
    # Create messages for Claude
    system_message = SystemMessage(
        content="You are a verification specialist analyzing donor information. Compare the provided information with search results and identify what matches, what doesn't match, and any discrepancies."
    )
    
    human_message = HumanMessage(
        content=f"""
Compare the following provided donor information with the search results and verify what matches and what doesn't.

PROVIDED DONOR INFORMATION:
{provided_info}

SEARCH RESULTS:
{json.dumps(search_summary, indent=2)}

Please analyze and provide:
1. **Verified Information** - What information was found matching in search results
2. **Unverified Information** - What information could not be verified
3. **Discrepancies** - Any conflicting information or concerns
4. **Verification Confidence** - Overall confidence level (High/Medium/Low) with explanation

Format your response clearly with these sections using markdown headers.
"""
    )
    
    try:
        messages = [system_message, human_message]
        response = llm(messages)
        return response.content
    except Exception as e:
        return f"Error analyzing with Claude: {str(e)}"

# Main app
st.subheader("📝 Enter Donor Information")

# Default donor information
default_info = """Matthew Hanauer
matthewhanauer99@gmail.com
260-409-5700
730 Crestview Drive, Durham, NC 27712
Senior Director Data Science, MedeAnalytics"""

# Input area
donor_info = st.text_area(
    "Donor Information",
    value=default_info,
    height=150,
    help="Enter donor information including name, email, phone, address, and title/company"
)

# Search button
if st.button("🔍 Search and Verify", type="primary", use_container_width=True):
    if donor_info:
        # Show progress
        with st.spinner("Searching for information..."):
            # Create search query from the first few lines (usually name and email)
            lines = donor_info.strip().split('\n')
            # Get name and any identifiable info for search
            search_parts = []
            if len(lines) > 0:
                search_parts.append(lines[0])  # Name
            if len(lines) > 1 and '@' in lines[1]:
                search_parts.append(lines[1])  # Email
            if len(lines) > 4:
                # Try to get company name from last line
                company_line = lines[4]
                if ',' in company_line:
                    company = company_line.split(',')[1].strip()
                    search_parts.append(company)
            
            search_query = ' '.join(search_parts)
            
            # Search with Serper
            st.write(f"🔎 Searching for: *{search_query}*")
            search_results = search_with_serper(search_query)
            
            if "error" in search_results:
                st.error(f"Search error: {search_results['error']}")
            else:
                st.success("✅ Search completed!")
                
                # Show search results in expander
                with st.expander("📄 View Raw Search Results"):
                    for i, result in enumerate(search_results.get("organic_results", [])[:5], 1):
                        st.markdown(f"**{i}. {result.get('title', 'No title')}**")
                        st.markdown(f"*{result.get('snippet', 'No snippet')}*")
                        st.markdown(f"[Link]({result.get('link', '#')})")
                        st.divider()
                
                # Analyze with Claude
                with st.spinner("Analyzing with Claude..."):
                    analysis = compare_with_claude(donor_info, search_results)
                
                # Display analysis
                st.divider()
                st.subheader("🤖 Claude's Verification Analysis")
                st.markdown(analysis)
                
                # Save results
                st.divider()
                col1, col2 = st.columns(2)
                
                with col1:
                    # Create report
                    report = {
                        "donor_info": donor_info,
                        "search_query": search_query,
                        "analysis": analysis,
                        "search_results_count": len(search_results.get("organic_results", [])),
                        "timestamp": str(st.session_state.get('timestamp', ''))
                    }
                    
                    st.download_button(
                        label="📥 Download Report (JSON)",
                        data=json.dumps(report, indent=2),
                        file_name="donor_verification_report.json",
                        mime="application/json"
                    )
                
                with col2:
                    if st.button("🔄 Search Another Donor"):
                        st.rerun()
    else:
        st.warning("Please enter donor information")

# Instructions
with st.expander("ℹ️ How to use this app"):
    st.markdown("""
    1. **Enter donor information** in the text area (or use the default)
    2. **Click Search and Verify** to search the web
    3. **Review the analysis** provided by Claude
    4. **Download the report** if needed
    
    ### Setting up API Keys:
    Create a `.streamlit/secrets.toml` file with:
    ```toml
    ANTHROPIC_API_KEY = "your-anthropic-key"
    SERPER_API_KEY = "your-serper-key"
    ```
    
    ### About the Analysis:
    Claude will analyze the search results and provide:
    - ✅ Verified information (found in search results)
    - ❌ Unverified information (not found)
    - ⚠️ Any discrepancies or concerns
    - 📊 Overall confidence level
    """)

# Footer
st.divider()
st.caption("This app uses Serper API for web search and Claude (Anthropic) for intelligent analysis")
