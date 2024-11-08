
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import sqlite3


import streamlit as st
from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from langchain_community.document_loaders import WebBaseLoader
import os

# Set user agent environment variable
os.environ["LANGCHAIN_USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Set page config
st.set_page_config(layout="wide")

# Define your CSS
css = """
<style>
    body {
        font-family: 'Arial', sans-serif;
        color: #333333;
        background-color: #f5f7fa;
    }
    
    .stTitle {
        color: #1e3a8a;
        font-size: 36px;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1.5rem;
    }
    
    .stTextInput > div > div > input {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
    }
    
    .stButton > button {
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #1d4ed8;
    }
    
    .portfolio-link {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }
    
    .portfolio-link:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .job-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    pre {
        background-color: #f5f5f5;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 15px;
        color: #333333;
        font-size: 14px;
        line-height: 1.5;
        overflow-x: auto;
    }
</style>
"""

# Inject CSS
st.markdown(css, unsafe_allow_html=True)

def create_streamlit_app(llm, portfolio, clean_text):
    st.title("Cold Mail Generator")

    # Initialize session state for storing URL and results
    if 'url' not in st.session_state:
        st.session_state.url = ""
        st.session_state.results = None
        st.session_state.show_portfolio = {}

    # Sidebar for input
    with st.sidebar:
        url_input = st.text_input("Enter a URL:", key="url_input")
        submit_button = st.button("Submit")

    if submit_button and url_input:
        try:
            # Create loader with custom headers
            loader = WebBaseLoader(
                web_paths=[url_input],
                header_template={"User-Agent": os.environ["LANGCHAIN_USER_AGENT"]}
            )
            data = loader.load()
            if not data:
                st.error("Failed to load content from the URL")
                return

            page_content = data.pop().page_content
            clean_data = clean_text(page_content)
            
            portfolio.load_portfolio()
            jobs = llm.extract_jobs(clean_data)
            
            # Store results in session state
            st.session_state.results = {
                'jobs': jobs,
                'portfolio': portfolio
            }
            st.session_state.url = url_input

        except Exception as e:
            st.error("An Error Occurred")
            st.exception(e)

    # Display results if they exist
    if hasattr(st.session_state, 'results') and st.session_state.results:
        jobs = st.session_state.results['jobs']
        
        if not jobs:
            st.error("No jobs found in the page content")
        else:
            for idx, job in enumerate(jobs):
                with st.container():
                    st.markdown("---")
                    st.subheader(f"Job {idx + 1}")
                    
                    # Get job details
                    skills = job.get('skills', [])
                    links = portfolio.query_links(skills)
                    
                    # Display skills
                    st.write("**Skills Required:**")
                    st.write(", ".join(skills))
                    
                    # Portfolio toggle
                    show_portfolio = st.checkbox(f"Show Portfolio Links for Job {idx + 1}", 
                                               key=f"portfolio_toggle_{idx}")
                    
                    # Display portfolio links if toggled
                    if show_portfolio:
                        st.write("**Portfolio Links:**")
                        for link_list in links:
                            for link_item in link_list:
                                st.markdown(
                                    f"""
                                    <div class="portfolio-link">
                                        <a href="{link_item['links']}" target="_blank">
                                            {link_item['links']}
                                        </a>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                    
                    # Display generated email
                    st.write("**Generated Email:**")
                    email = llm.write_mail(job, links)
                    st.code(email, language='markdown')

if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()
    create_streamlit_app(chain, portfolio, clean_text)