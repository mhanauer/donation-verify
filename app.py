"""
Final Clean Donor Verification App with Summary
===============================================
Uses Claude Sonnet 4 for both web search verification and AI-generated summary
"""

import streamlit as st
import anthropic
import json
from datetime import datetime

st.set_page_config(
    page_title="Donor Verification Tool",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Campaign Donor Verification Tool")
st.markdown("Verify donor information with AI-powered web search and get actionable summaries")

# API key
api_key = st.secrets.get("API-KEY", "")
if not api_key:
    st.error("Please add API-KEY to Streamlit secrets")
    st.stop()

# Create columns for input and results
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📝 Donor Information")
    name = st.text_input("Name*", value="Matthew Hanauer")
    title = st.text_input("Job Title", value="Senior Director Data Science")
    company = st.text_input("Company", value="MedeAnalytics")
    
    verify_btn = st.button("🔍 Verify Donor", type="primary", use_container_width=True)
    
    # Info box
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        1. **Web Search**: Searches for public information about the donor
        2. **Analysis**: Compares findings with provided information
        3. **Summary**: Generates actionable summary with confidence level
        4. **Next Steps**: Provides clear recommendation
        """)

with col2:
    if verify_btn and name:
        # Initialize client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Store timestamp
        timestamp = datetime.now()
        
        # Step 1: Web Search Verification
        with st.spinner("🔍 Searching and verifying..."):
            try:
                # Verification query
                query = f"Please verify this information is correct: {name} is {title} at {company}."
                
                # Make web search API call using Claude Sonnet 4 with web search
                verification_response = client.beta.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=20000,
                    temperature=1,
                    messages=[{
                        "role": "user",
                        "content": [{
                            "type": "text",
                            "text": query
                        }]
                    }],
                    tools=[{
                        "name": "web_search",
                        "type": "web_search_20250305"
                    }],
                    betas=["web-search-2025-03-05"]
                )
                
                # Extract verification text and search results
                verification_text = ""
                search_results = []
                search_executed = False
                
                for block in verification_response.content:
                    if hasattr(block, 'type'):
                        if block.type == 'text':
                            verification_text = block.text
                        elif block.type == 'server_tool_use':
                            search_executed = True
                        elif block.type == 'web_search_tool_result':
                            for result in block.content[:5]:
                                if hasattr(result, 'title'):
                                    search_results.append(result.title)
                
                # Display search results
                if search_results:
                    st.success("✅ Web search completed successfully!")
                    with st.expander("🔍 Sources Found", expanded=False):
                        for result in search_results:
                            st.write(f"• {result}")
                else:
                    st.warning("⚠️ No web search results found")
                
                # Display verification analysis
                with st.expander("📊 Detailed Verification Analysis", expanded=True):
                    st.write(verification_text)
                
                # Step 2: Generate Summary using Claude Sonnet 4 (no web search needed)
                if verification_text:
                    with st.spinner("📝 Generating summary..."):
                        # Create structured prompt for summary
                        summary_prompt = f"""Based on this verification analysis, provide a clear summary:

VERIFICATION ANALYSIS:
{verification_text}

PERSON BEING VERIFIED:
- Name: {name}
- Title: {title}
- Company: {company}

Provide exactly these three items:
1. VERIFICATION STATUS: A 1-2 sentence summary of what was verified vs not verified
2. CONFIDENCE LEVEL: Choose HIGH/MEDIUM/LOW with a brief explanation
3. NEXT STEPS: A specific 1-2 sentence recommendation for action

Format your response EXACTLY like this:
VERIFICATION STATUS: [Your summary]
CONFIDENCE LEVEL: [HIGH/MEDIUM/LOW] - [Brief explanation]
NEXT STEPS: [Your recommendation]"""

                        # Get summary using Claude Sonnet 4 (no web search needed)
                        summary_response = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=500,
                            temperature=0,
                            messages=[{"role": "user", "content": summary_prompt}]
                        )
                        
                        summary_text = summary_response.content[0].text
                        
                        # Display formatted summary
                        st.divider()
                        st.subheader("📋 Verification Summary")
                        
                        # Parse and display summary with visual formatting
                        lines = summary_text.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith("VERIFICATION STATUS:"):
                                st.info(f"**{line}**")
                            elif line.startswith("CONFIDENCE LEVEL:"):
                                # Color-coded confidence levels
                                if "HIGH" in line:
                                    st.success(f"**🟢 {line}**")
                                elif "MEDIUM" in line:
                                    st.warning(f"**🟡 {line}**")
                                elif "LOW" in line:
                                    st.error(f"**🔴 {line}**")
                            elif line.startswith("NEXT STEPS:"):
                                st.markdown(f"### 🎯 {line}")
                        
                        # Processing time
                        elapsed = (datetime.now() - timestamp).total_seconds()
                        st.caption(f"⏱️ Verification completed in {elapsed:.1f} seconds")
                        
                        # Download report
                        st.divider()
                        # Create comprehensive report
                        report = {
                            "timestamp": timestamp.isoformat(),
                            "processing_time_seconds": elapsed,
                            "donor_info": {
                                "name": name,
                                "title": title,
                                "company": company
                            },
                            "web_search": {
                                "executed": search_executed,
                                "sources_found": search_results
                            },
                            "verification_analysis": verification_text,
                            "executive_summary": summary_text
                        }
                        
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            st.download_button(
                                "📥 Download JSON Report",
                                data=json.dumps(report, indent=2),
                                file_name=f"donor_verification_{name.replace(' ', '_')}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        
                        with col_dl2:
                            # Create text version
                            text_report = f"""DONOR VERIFICATION REPORT
{'='*50}
Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}

DONOR INFORMATION:
- Name: {name}
- Title: {title}
- Company: {company}

SOURCES FOUND:
{chr(10).join(['- ' + s for s in search_results])}

VERIFICATION ANALYSIS:
{verification_text}

EXECUTIVE SUMMARY:
{summary_text}

Processing Time: {elapsed:.1f} seconds
"""
                            st.download_button(
                                "📄 Download Text Report",
                                data=text_report,
                                file_name=f"donor_verification_{name.replace(' ', '_')}_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if "rate" in str(e).lower():
                    st.info("You may have hit a rate limit. Please wait a moment and try again.")
                elif "api" in str(e).lower():
                    st.info("Please check your API key configuration.")
    
    elif verify_btn and not name:
        st.warning("Please enter a donor name to verify")

# Footer
st.divider()
st.caption("This tool searches public information to verify donor details and provide actionable recommendations.")
