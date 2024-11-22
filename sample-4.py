import streamlit as st
import re
from serpapi import GoogleSearch
from typing import List, Tuple

# Your SerpAPI Key
SERPAPI_KEY = "99032d11f4529779ed8b321c24eedeee0575114010305c719dd19fc019542c7d"

def clean_quote_text(text: str) -> str:
    """
    Clean and normalize quote text with proper punctuation.
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Truncate at the first full stop to remove excess text
    text = text.split('.')[0] + '.' if '.' in text else text
    
    # Capitalize first letter
    text = text[0].upper() + text[1:] if text else text
    
    return text.strip()

def extract_quote_and_author(snippet: str) -> Tuple[str, str]:
    """
    Extract quote and author using pattern matching.
    """
    # Define regex patterns to identify quotes and their authors
    patterns = [
        r'["“”](.+?)["”][\s]*[-–—~]\s*([A-Z][^,\n]+)',
        r'"(.+?)"[\s]*[-–—~]\s*([A-Z][^,\n]+)',
        r'(.+?)[\s]*[-–—~]\s*([A-Z][^,\n]+)',
        r'["“](.+?)["”][\s]*by\s*([A-Z][^,\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, snippet, re.DOTALL)
        if match:
            quote, author = match.groups()
            
            # Clean quote
            quote = clean_quote_text(quote)
            
            # Clean author
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
    Fetch quotes using SerpAPI with refined search queries.
    """
    search_queries = [
        f"famous quotes about {prompt}",
        f"{prompt} quotes by authors",
        f"inspirational {prompt} quotes",
        f"best {prompt} sayings",
    ]
    
    quotes_and_authors = []
    seen_quotes = set()
    
    for query in search_queries:
        if len(quotes_and_authors) >= 5:  # Stop when we have enough quotes
            break
        
        search = GoogleSearch({
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 15,  # Fetch multiple results
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
                        
        except Exception:
            continue
    
    # Fallback if fewer than 5 quotes are found
    if len(quotes_and_authors) < 5:
        general_fallbacks = [
            ("Failure is the stepping stone to success.", "Ariana Huffington"),
            ("Happiness depends upon ourselves.", "Aristotle"),
            ("Success is not final; failure is not fatal: It is the courage to continue that counts.", "Winston Churchill"),
            ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
            ("The only limit to our realization of tomorrow is our doubts of today.", "Franklin D. Roosevelt"),
        ]
        quotes_and_authors.extend(general_fallbacks[:5 - len(quotes_and_authors)])
    
    return quotes_and_authors

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
            st.markdown(f"{i}. \"{quote}\" - **{author}**")
            st.write("---")
