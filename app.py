"""
Minimal app that exactly matches the working console example
"""

import streamlit as st
import anthropic

st.title("🔍 Donor Verification - Console Match")

# API key
api_key = st.secrets.get("API-KEY", "")
if not api_key:
    st.error("Add API-KEY to secrets")
    st.stop()

# Inputs
name = st.text_input("Name", "Matthew Hanauer")
title = st.text_input("Title", "Senior Director Data Science")
company = st.text_input("Company", "MedeAnalytics")

if st.button("Verify"):
    # Exact parameters from working example
    client = anthropic.Anthropic(api_key=api_key)
    
    query = f"Please verify this information is correct: {name} is {title} at {company}."
    
    with st.spinner("Verifying..."):
        try:
            # Exact API call from console
            message = client.beta.messages.create(
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
            
            # Parse response
            st.success("Response received!")
            
            # Check for web search execution
            search_executed = False
            for block in message.content:
                if hasattr(block, 'type'):
                    if block.type == 'server_tool_use':
                        search_executed = True
                        st.info(f"✅ Searched for: {block.input.get('query', 'N/A')}")
                    elif block.type == 'web_search_tool_result':
                        st.write("**Search Results:**")
                        for result in block.content[:5]:
                            if hasattr(result, 'title'):
                                st.write(f"- {result.title}")
            
            if not search_executed:
                st.warning("⚠️ Web search was not executed")
            
            # Show text response
            st.write("**Analysis:**")
            for block in message.content:
                if hasattr(block, 'type') and block.type == 'text':
                    st.write(block.text)
                    
        except Exception as e:
            st.error(f"Error: {e}")
