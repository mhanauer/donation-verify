import streamlit as st
import requests
import json
from openai import OpenAI

# Page config
st.set_page_config(
    page_title="Donor Verification",
    page_icon="🔍",
    layout="centered"
)

st.title("🔍 Simple Donor Verification")
st.markdown("Search and verify donor information using Serper and OpenAI")

# Initialize OpenAI client using secrets
try:
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    serper_api_key = st.secrets["SERPER_API_KEY"]
except:
    st.error("Please set OPENAI_API_KEY and SERPER_API_KEY in your Streamlit secrets")
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

def compare_with_openai(provided_info: str, search_results: dict) -> str:
    """Use OpenAI to compare provided info with search results"""
    # Extract relevant information from search results
    search_summary = []
    if "organic_results" in search_results:
        for result in search_results.get("organic_results", [])[:5]:
            search_summary.append({
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "link": result.get("link", "")
            })
    
    prompt = f"""
    Compare the following provided donor information with the search results and verify what matches and what doesn't.
    
    PROVIDED DONOR INFORMATION:
    {provided_info}
    
    SEARCH RESULTS:
    {json.dumps(search_summary, indent=2)}
    
    Please analyze and provide:
    1. What information was verified (found matching in search results)
    2. What information could not be verified
    3. Any discrepancies or concerns
    4. Overall verification confidence (High/Medium/Low)
    
    Format your response clearly with these sections.
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a verification specialist analyzing donor information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing with OpenAI: {str(e)}"

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
if st.button("🔍 Search and Verify", type="primary"):
    if donor_info:
        # Show progress
        with st.spinner("Searching for information..."):
            # Create search query from the first few lines (usually name and email)
            lines = donor_info.strip().split('\n')
            search_query = ' '.join(lines[:2])  # Use name and email for search
            
            # Search with Serper
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
                
                # Analyze with OpenAI
                with st.spinner("Analyzing with OpenAI..."):
                    analysis = compare_with_openai(donor_info, search_results)
                
                # Display analysis
                st.divider()
                st.subheader("🤖 Verification Analysis")
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
                        "search_results_count": len(search_results.get("organic_results", []))
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
    3. **Review the analysis** provided by OpenAI
    4. **Download the report** if needed
    
    ### Setting up API Keys:
    Create a `.streamlit/secrets.toml` file with:
    ```toml
    OPENAI_API_KEY = "your-openai-key"
    SERPER_API_KEY = "your-serper-key"
    ```
    """)

# Footer
st.divider()
st.caption("This app uses Serper API for web search and OpenAI for intelligent analysis")
