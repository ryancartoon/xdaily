import streamlit as st
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.service import get_articles, get_sources, get_article

# Constants
ITEMS_PER_PAGE = 10


def get_filtered_articles(
    sources: List[str],
    keywords: str,
    from_date: Optional[datetime],
    to_date: Optional[datetime],
    page: int
) -> List[Dict]:
    """Get filtered articles from DataStore with pagination"""
    
    return get_articles(
        sources=sources,
        keywords=keywords,
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
        page=page,
        page_size=ITEMS_PER_PAGE
    )

def show_article_detail(article_id: int):
    """Show detailed view of a single article"""
    article = get_article(article_id)
    if not article:
        st.error("Article not found")
        return
    
    st.title(article['title'])
    st.caption(f"Published on {article['published_at']} | Source: {article['source']}")
    
    st.markdown("---")
    st.subheader("Content")
    st.markdown(article['content'])
    
    if article.get('summary'):
        st.markdown("---")
        st.subheader("Summary")
        st.markdown(article['summary'])
    
    if article.get('analysis_result'):
        st.markdown("---")
        st.subheader("Analysis")
        st.markdown(article['analysis_result'])
    
    if article.get('keywords'):
        st.markdown("---")
        st.subheader("Keywords")
        st.write(", ".join(article['keywords']))
    
    st.markdown("---")
    if st.button("Back to News List"):
        st.session_state['view'] = 'list'

def main():
    st.set_page_config(page_title="News Explorer", layout="wide")
    
    # Initialize session state
    if 'view' not in st.session_state:
        st.session_state['view'] = 'list'
    if 'article_id' not in st.session_state:
        st.session_state['article_id'] = None
    
    # Show appropriate view based on state
    if st.session_state['view'] == 'detail' and st.session_state['article_id']:
        show_article_detail(st.session_state['article_id'])
        return
    
    # List view
    st.title("News Explorer")

    # Main content area
    st.header("Filters")
    
    # Create columns for filters and pagination
    filter_col, page_col = st.columns([4, 1]) # Adjust ratio for filters vs page number

    with filter_col:
        # Create columns for individual filters
        source_col, keyword_col, date_col = st.columns(3) # Three columns for the three filters

        with source_col:
            all_sources = get_sources()
            selected_sources = st.multiselect(
                "Select Sources",
                options=[s['id'] for s in all_sources],
                format_func=lambda x: next((s['name'] for s in all_sources if s['id'] == x), x),
                default=[]
            )
            
        with keyword_col:
            keywords = st.text_input("Keywords")
            
        with date_col:
            today = datetime.now()
            week_ago = today - timedelta(days=7)
            date_range = st.date_input(
                "Date Range",
                value=(week_ago, today),
                min_value=today - timedelta(days=365),
                max_value=today
            )
            
            from_date, to_date = date_range if len(date_range) == 2 else (None, None)

    with page_col:
        page = st.number_input("Page", min_value=1, value=1, step=1)

    st.markdown("---") # Add padding

    # Convert source names to IDs for filtering
    articles = get_filtered_articles(
        sources=selected_sources,
        keywords=keywords,
        from_date=from_date,
        to_date=to_date,
        page=page
    )

    if not articles:
        st.warning("No articles found matching your criteria")
    else:
        # Create DataFrame with required columns
        # Display articles in a more reliable way
        for article in articles:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(article['title'])
                    st.caption(f"Source: {article['source']['name']} | Published: {article['published_at']}")
                with col2:
                    if st.button("View Details", key=f"view_{article['id']}"):
                        st.session_state['view'] = 'detail'
                        st.session_state['article_id'] = article['id']
                        st.rerun()
                st.markdown("---")

if __name__ == "__main__":
    main()