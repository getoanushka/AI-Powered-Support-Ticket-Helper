import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_URL = f"{BACKEND_URL}/api"

# Page config
st.set_page_config(
    page_title="AI Support Ticket Helper",
    page_icon="🎫",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .success-box {
        background: #d1fae5;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #10b981;
    }
    .warning-box {
        background: #fef3c7;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🎫 AI Ticket Helper")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Analyze Ticket", "KB Gap Analysis", "Data Explorer"]
)

# Helper functions
def fetch_gap_analysis():
    try:
        response = requests.get(f"{API_URL}/gap-analysis")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def analyze_ticket(ticket_text):
    try:
        response = requests.post(
            f"{API_URL}/analyze-ticket",
            json={"ticket_text": ticket_text}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def fetch_tickets():
    try:
        response = requests.get(f"{API_URL}/tickets")
        if response.status_code == 200:
            return response.json()['tickets']
        return []
    except:
        return []

def fetch_kb_articles():
    try:
        response = requests.get(f"{API_URL}/kb-articles")
        if response.status_code == 200:
            return response.json()['articles']
        return []
    except:
        return []

def build_index():
    try:
        response = requests.post(f"{API_URL}/build-index")
        return response.status_code == 200
    except:
        return False

# Main content
if page == "Dashboard":
    st.markdown('<div class="main-header">📊 Dashboard Overview</div>', unsafe_allow_html=True)
    st.markdown("A single view of ticket activity, category trends, and knowledge gaps")

    # Load data
    tickets = fetch_tickets()
    kb_articles = fetch_kb_articles()
    gap_data = fetch_gap_analysis()

    # Compute derived values
    df_tickets = pd.DataFrame(tickets)
    if not df_tickets.empty:
        df_tickets['created_at'] = pd.to_datetime(df_tickets['created_at'], errors='coerce')
        df_tickets.dropna(subset=['created_at'], inplace=True)

        # Tickets over time
        tickets_over_time = (
            df_tickets
            .set_index('created_at')
            .resample('D')
            .size()
            .rename('count')
            .reset_index()
        )

        # Category breakdown
        category_counts = df_tickets['category'].value_counts().reset_index()
        category_counts.columns = ['category', 'count']

        # Priority (derived)
        def derive_priority(category):
            high = {'Payment', 'Authentication', 'API', 'Security'}
            medium = {'Performance', 'Integration'}
            if category in high:
                return 'High'
            if category in medium:
                return 'Medium'
            return 'Low'

        df_tickets['priority'] = df_tickets['category'].apply(derive_priority)
        priority_counts = df_tickets['priority'].value_counts().reset_index()
        priority_counts.columns = ['priority', 'count']

        recent_tickets = df_tickets.sort_values('created_at', ascending=False).head(7)
    else:
        tickets_over_time = pd.DataFrame(columns=['created_at', 'count'])
        category_counts = pd.DataFrame(columns=['category', 'count'])
        priority_counts = pd.DataFrame(columns=['priority', 'count'])
        recent_tickets = pd.DataFrame()

    # Top stats cards
    total_tickets = len(df_tickets)
    total_kb = len(kb_articles)
    index_status = "Ready" if gap_data else "Not Built"

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", total_tickets)
    col2.metric("KB Articles", total_kb)
    col3.metric("Index Status", index_status)

    st.divider()

    # Tickets over time
    st.subheader("📈 Tickets Over Time")
    if not tickets_over_time.empty:
        tickets_over_time = tickets_over_time.set_index('created_at')
        st.line_chart(tickets_over_time)
    else:
        st.info("No ticket data available to render the timeline.")

    st.divider()

    # Category + Priority breakdown
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🗂 Category Breakdown")
        if not category_counts.empty:
            st.bar_chart(category_counts.set_index('category'))
        else:
            st.info("No category data available.")

    with col2:
        st.subheader("⏳ Priority Breakdown")
        if not priority_counts.empty:
            st.bar_chart(priority_counts.set_index('priority'))
        else:
            st.info("No priority data available.")

    st.divider()

    # Recent tickets
    st.subheader("📝 Recent Tickets")
    if not recent_tickets.empty:
        st.dataframe(
            recent_tickets[['ticket_id', 'created_at', 'category', 'priority', 'ticket_text']].head(7),
            use_container_width=True
        )
    else:
        st.info("No recent tickets available.")

    st.divider()

    # AI insights / gap analysis
    st.subheader("🤖 AI Insights & Knowledge Gap Analysis")
    if gap_data:
        summary = gap_data['summary']

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total KB Articles", summary.get('total_articles', 0))
        col2.metric("Avg CTR", f"{summary.get('avg_ctr', 0):.1%}")
        col3.metric("Avg Views", f"{summary.get('avg_views', 0):.0f}")
        col4.metric("Avg Clicks", f"{summary.get('avg_clicks', 0):.0f}")

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**⚠️ Low Performing Articles**")
            if gap_data['low_performers']:
                df_low = pd.DataFrame(gap_data['low_performers'])
                st.dataframe(
                    df_low[['title', 'ctr', 'views', 'clicks']].head(5),
                    use_container_width=True
                )
            else:
                st.info("No low performing articles detected.")

        with col2:
            st.markdown("**📉 Low Coverage Articles**")
            if gap_data['low_coverage']:
                df_cov = pd.DataFrame(gap_data['low_coverage'])
                st.dataframe(
                    df_cov[['title', 'views', 'clicks']].head(5),
                    use_container_width=True
                )
            else:
                st.info("No low coverage articles detected.")
    else:
        st.warning("Gap analysis data not available; run the index build and retry.")

elif page == "Analyze Ticket":
    st.markdown('<div class="main-header">🎫 Analyze Support Ticket</div>', unsafe_allow_html=True)
    st.markdown("Get AI-powered classification and KB article recommendations")
    
    st.divider()
    
    # Input
    ticket_text = st.text_area(
        "Enter ticket text:",
        height=150,
        placeholder="Example: I can't reset my password. The link in my email isn't working..."
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        analyze_btn = st.button("🔍 Analyze Ticket", type="primary", use_container_width=True)
    
    if analyze_btn and ticket_text:
        with st.spinner("Analyzing ticket..."):
            result = analyze_ticket(ticket_text)
        
        if result:
            st.success("Analysis complete!")
            
            # Preprocessing
            st.subheader("🛡️ Preprocessing")
            preproc = result['preprocessed']
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original Text:**")
                st.text_area("", value=preproc['original'], height=100, disabled=True, key="orig")
            
            with col2:
                st.markdown("**Anonymized Text:**")
                st.text_area("", value=preproc['anonymized'], height=100, disabled=True, key="anon")
            
            if preproc['has_sensitive_data']:
                st.warning("⚠️ Sensitive data detected and anonymized")
            
            st.divider()
            
            # Classification
            st.subheader("🏷️ Classification")
            classif = result['classification']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Category", classif['category'])
            with col2:
                st.metric("Confidence", f"{classif['confidence']:.0%}")
            with col3:
                st.metric("Status", classif['status'].upper())
            
            st.markdown(f"**Tags:** {', '.join(classif['tags'])}")
            st.caption(f"Reasoning: {classif['reasoning']}")
            
            st.divider()
            
            # Recommendations
            st.subheader("📚 Recommended KB Articles")
            recommendations = result['recommendations']
            
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"#{i} - {rec['title']} (Similarity: {rec['similarity_score']:.2%})"):
                        st.markdown(f"**Category:** {rec['category']}")
                        st.markdown(f"**Article ID:** {rec['article_id']}")
                        st.markdown(f"**Content:**")
                        st.write(rec['content'])
            else:
                st.info("No recommendations available. Build the index first.")
        else:
            st.error("Failed to analyze ticket. Check backend connection.")

elif page == "KB Gap Analysis":
    st.markdown('<div class="main-header">🔍 KB Gap Analysis</div>', unsafe_allow_html=True)
    st.markdown("Identify weak KB articles and coverage gaps")
    
    st.divider()
    
    gap_data = fetch_gap_analysis()
    
    if gap_data:
        summary = gap_data['summary']
        
        # Summary boxes
        st.markdown("### 📊 Performance Summary")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="success-box">
                <h3>📊 Overall Stats</h3>
                <p>• Total Articles: {summary['total_articles']}</p>
                <p>• Average CTR: {summary['avg_ctr']:.2%}</p>
                <p>• Average Views: {summary['avg_views']:.0f}</p>
                <p>• Average Clicks: {summary['avg_clicks']:.0f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="warning-box">
                <h3>⚠️ Issues Found</h3>
                <p>• Low Performers: {summary['low_performers_count']} articles</p>
                <p>• Low Coverage: {summary['low_coverage_count']} articles</p>
                <p>• Action Required: {summary['low_performers_count'] + summary['low_coverage_count']} articles</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Detailed tables
        st.markdown("### 📝 Detailed Analysis")
        
        tab1, tab2 = st.tabs(["Low Performing Articles", "Low Coverage Articles"])
        
        with tab1:
            if gap_data['low_performers']:
                df = pd.DataFrame(gap_data['low_performers'])
                st.dataframe(
                    df[['article_id', 'title', 'category', 'views', 'clicks', 'ctr']],
                    use_container_width=True
                )
            else:
                st.success("No low-performing articles found!")
        
        with tab2:
            if gap_data['low_coverage']:
                df = pd.DataFrame(gap_data['low_coverage'])
                st.dataframe(
                    df[['article_id', 'title', 'category', 'views', 'clicks']],
                    use_container_width=True
                )
            else:
                st.success("No low-coverage articles found!")
    else:
        st.error("Unable to load gap analysis data")

elif page == "Data Explorer":
    st.markdown('<div class="main-header">📂 Data Explorer</div>', unsafe_allow_html=True)
    st.markdown("Browse tickets and KB articles")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Tickets", "KB Articles"])
    
    with tab1:
        st.subheader("🎫 Support Tickets")
        tickets = fetch_tickets()
        
        if tickets:
            df = pd.DataFrame(tickets)
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total tickets: {len(tickets)}")
        else:
            st.warning("No tickets found")
    
    with tab2:
        st.subheader("📚 KB Articles")
        articles = fetch_kb_articles()
        
        if articles:
            df = pd.DataFrame(articles)
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total articles: {len(articles)}")
        else:
            st.warning("No articles found")

# Footer
st.divider()
st.caption("🤖 AI Support Ticket Helper | Powered by LLaMA, FAISS, and Sentence Transformers")