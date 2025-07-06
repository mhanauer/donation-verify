"""
Simple test script to debug Claude web search
==============================================
Run this separately to test if web search is working
"""

import anthropic
import json

# Replace with your actual API key
API_KEY = "sk-ant-api03-your-key-here"

def test_web_search():
    """Test if web search is working"""
    print("Testing Claude web search...")
    
    client = anthropic.Anthropic(api_key=API_KEY)
    
    # Test queries
    queries = [
        "Use web_search to find what company Tim Cook works for",
        "Search for information about Satya Nadella using web_search",
        "web_search: What is Apple's current stock price?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Test {i} ---")
        print(f"Query: {query}")
        
        try:
            message = client.beta.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
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
            
            result = message.content[0].text if message.content else "No response"
            print(f"Response: {result[:200]}...")
            
            # Check if search was executed
            if "I'll search" in result or "I will search" in result:
                print("❌ FAILED: Got 'I'll search' response - tool not executed")
            elif "apple" in result.lower() or "microsoft" in result.lower():
                print("✅ SUCCESS: Got actual search results")
            else:
                print("⚠️  UNCLEAR: Check full response")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")

def test_without_web_search():
    """Test regular API call without web search"""
    print("\n\n--- Testing WITHOUT web search ---")
    
    client = anthropic.Anthropic(api_key=API_KEY)
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": "What company does Tim Cook work for? (answer based on your knowledge)"
            }]
        )
        
        result = message.content[0].text
        print(f"Response: {result}")
        print("✅ Regular API call works")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    # Test both with and without web search
    test_web_search()
    test_without_web_search()
    
    print("\n\nIf web search tests show 'I'll search' responses, the beta feature may be unavailable.")
    print("Use the regular API (without web search) as a fallback.")
