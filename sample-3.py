import streamlit as st
import re
from serpapi import GoogleSearch
from typing import List, Tuple

# Hardcode your SerpAPI key here
SERPAPI_KEY = "99032d11f4529779ed8b321c24eedeee0575114010305c719dd19fc019542c7d"

def clean_quote_text(text: str) -> str:
    """
    Clean and normalize quote text with proper punctuation.
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove any quotes at the start and end
    text = text.strip('"\'""''')
    
    # Normalize ending punctuation
    if not any(text.endswith(p) for p in '.!?'):
        if text.endswith(','):
            text = text[:-1] + '.'
        else:
            text += '.'
    
    # Capitalize first letter
    text = text[0].upper() + text[1:]
    
    return text

def extract_quote_and_author(snippet: str) -> Tuple[str, str]:
    """
    Extract quote and author with improved pattern matching and cleansing.
    """
    # Define quote patterns with various separators and formats
    patterns = [
        # Basic patterns with standard separators
        r'["""]([^"""\n]+)["""][\s]*[-–—~]\s*([A-Z][^,\n]{2,})',
        r'"([^"\n]+)"[\s]*[-–—~]\s*([A-Z][^,\n]{2,})',
        r"'([^'\n]+)'[\s]*[-–—~]\s*([A-Z][^,\n]{2,})",
        
        # Patterns with "by" attribution
        r'["""]([^"""\n]+)["""][\s]*by[\s]*([A-Z][^,\n]{2,})',
        
        # Patterns without explicit separators
        r'["""]([^"""\n]+)["""][\s]*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
        
        # Patterns with different quote marks
        r'[«»]([^«»\n]+)[«»][\s]*[-–—~]\s*([A-Z][^,\n]{2,})',
        
        # Fallback pattern for simpler format
        r'"([^"\n]{15,})"[\s]*[-–—~]\s*([A-Z][^,\n]{2,})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, snippet, re.DOTALL)
        if match:
            quote, author = match.groups()
            
            # Clean the quote
            quote = clean_quote_text(quote)
            
            # Clean the author name
            author = author.strip()
            author = re.sub(r'\s+', ' ', author)  # Normalize spaces
            author = author.strip('.,;:-')  # Remove trailing punctuation
            
            # Validate quote and author
            if len(quote) > 10 and len(author) > 2:
                if not any(x in author.lower() for x in ['http', 'www', '.com', 'click', 'search', 'more']):
                    return quote, author
    
    return None, None

def fetch_quotes_from_serpapi(prompt: str) -> List[Tuple[str, str]]:
    """
    Fetch quotes using SerpAPI with improved search strategies.
    """
    search_variations = [
        f"{prompt} quotes",
        f"famous quotes about {prompt}",
        f"{prompt} sayings and quotes",
        f"best {prompt} quotes",
        f"inspirational {prompt} quotes",
        f"meaningful {prompt} quotes",
        f"popular {prompt} quotes"
    ]
    
    quotes_and_authors = []
    seen_quotes = set()
    
    for search_query in search_variations:
        if len(quotes_and_authors) >= 5:  # Continue until we have at least 5 quotes
            break
            
        search = GoogleSearch({
            "q": search_query,
            "api_key": SERPAPI_KEY,
            "num": 15,  # Increased number of results
            "gl": "us",
        })
        
        try:
            results = search.get_dict()
            if "organic_results" in results:
                for result in results["organic_results"]:
                    snippet = result.get("snippet", "")
                    quote, author = extract_quote_and_author(snippet)
                    
                    if quote and author:
                        quote_key = quote.lower()
                        if quote_key not in seen_quotes:
                            seen_quotes.add(quote_key)
                            quotes_and_authors.append((quote, author))
                    
                    if len(quotes_and_authors) >= 5:
                        break
                        
        except Exception as e:
            continue
    
    # If we still don't have 5 quotes, try one more general search
    if len(quotes_and_authors) < 5:
        try:
            search = GoogleSearch({
                "q": f"quotes related to {prompt}",
                "api_key": SERPAPI_KEY,
                "num": 20,
                "gl": "us",
            })
            
            results = search.get_dict()
            if "organic_results" in results:
                for result in results["organic_results"]:
                    if len(quotes_and_authors) >= 5:
                        break
                    snippet = result.get("snippet", "")
                    quote, author = extract_quote_and_author(snippet)
                    if quote and author:
                        quote_key = quote.lower()
                        if quote_key not in seen_quotes:
                            seen_quotes.add(quote_key)
                            quotes_and_authors.append((quote, author))
        except Exception as e:
            pass
    
    return quotes_and_authors or [("No relevant quotes found. Please try a different topic.", "")]

# Streamlit App
st.title("Quote Generator")
st.write("Enter any topic to find relevant quotes!")

# User Input
user_prompt = st.text_input("Enter a topic (e.g., success, failure, love, friendship):")

# Generate Quotes Button
if st.button("Generate Quotes"):
    if not user_prompt:
        st.warning("Please enter a topic to generate quotes!")
    else:
        with st.spinner("Finding quotes..."):
            quotes_and_authors = fetch_quotes_from_serpapi(user_prompt)
        
        st.subheader(f"Quotes about {user_prompt.capitalize()}")
        for i, (quote, author) in enumerate(quotes_and_authors, 1):
            # Display quote with consistent formatting
            if author:
                st.markdown(f"{i}. \"{quote}\" - **{author}**")
            else:
                st.markdown(f"{i}. \"{quote}\"")
            st.write("---")