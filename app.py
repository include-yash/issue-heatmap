import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from modules.clustering import perform_clustering
from collections import Counter
import numpy as np

# Page Config
st.set_page_config(
    page_title="Feedback Analyzer Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background: #9370db;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .cluster-card {
        background: #9370db;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Load Data
@st.cache_data
def load_data():
    df = pd.read_json('data/feedback_results_with_location.json')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("🔍 Filters")
date_range = st.sidebar.date_input(
    "Date Range",
    value=[df['timestamp'].min().date(), df['timestamp'].max().date()]
)

sentiment_filter = st.sidebar.multiselect(
    "Sentiment",
    options=df['sentiment'].unique(),
    default=df['sentiment'].unique()
)

category_filter = st.sidebar.multiselect(
    "Category",
    options=['Health', 'Education', 'Infrastructure', 'Environment', 'Public Safety'],
    default=['Health', 'Education', 'Infrastructure', 'Environment', 'Public Safety']
)

radius_km = st.sidebar.slider("Clustering Radius (km)", 1, 20, 5)
min_samples = st.sidebar.slider("Minimum Cluster Size", 2, 10, 3)

# Apply Filters
filtered_df = df[
    (df['sentiment'].isin(sentiment_filter)) &
    (df['category'].isin(category_filter)) &
    (df['timestamp'].dt.date >= date_range[0]) &
    (df['timestamp'].dt.date <= date_range[1])
]

# Initialize Session State
if 'clustered_df' not in st.session_state:
    st.session_state.clustered_df = None

# Main Dashboard
st.title("📊 Feedback Analyzer Pro")

# Metrics Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><h3>Total Feedback</h3><h2>{len(filtered_df)}</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><h3>Positive</h3><h2 style="color:green;">{len(filtered_df[filtered_df["sentiment"] == "Positive"])}</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><h3>Negative</h3><h2 style="color:red;">{len(filtered_df[filtered_df["sentiment"] == "Negative"])}</h2></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><h3>Clusters</h3><h2>{len(st.session_state.clustered_df["cluster"].unique()) if st.session_state.clustered_df is not None else 0}</h2></div>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Map View", "📈 Analytics", "🔍 Cluster Analysis", "💬 Feedback Explorer"])

with tab1:
    st.header("Geospatial Feedback Visualization")
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB Positron")
    
    category_colors = {
        "Health": "green",
        "Education": "blue",
        "Infrastructure": "orange",
        "Environment": "purple",
        "Public Safety": "red"
    }
    
    marker_cluster = folium.plugins.MarkerCluster().add_to(m)
    for _, row in filtered_df.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=f"""
                <b>Category:</b> {row['category']}<br>
                <b>Sentiment:</b> {row['sentiment']}<br>
                <b>Feedback:</b> {row['text'][:100]}...
            """,
            icon=folium.Icon(
                color=category_colors.get(row['category'], 'gray'),
                icon='info-sign',
                prefix='fa'
            )
        ).add_to(marker_cluster)
    
    st_folium(m, width=1200, height=600)

with tab2:
    st.header("Feedback Analytics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sentiment Distribution")
        fig1 = px.pie(filtered_df, names='sentiment', hole=0.3)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Category Distribution")
        fig2 = px.bar(filtered_df['category'].value_counts(), 
                     labels={'value': 'Count', 'index': 'Category'})
        st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("Category Trends Over Time")
    df_time = filtered_df.copy()
    df_time['date'] = df_time['timestamp'].dt.date
    fig3 = px.histogram(df_time, x='date', color='category', 
                       barmode='stack', nbins=30)
    st.plotly_chart(fig3, use_container_width=True)
    
    st.subheader("Top Keywords")
    text = " ".join(filtered_df['text'])
    if text.strip():
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

with tab3:
    st.header("Issue Clustering")
    st.markdown("Group similar issues reported within a specified radius")
    
    if st.button("Run Clustering"):
        with st.spinner("Analyzing feedback patterns..."):
            st.session_state.clustered_df = perform_clustering(
                filtered_df,
                max_radius_km=radius_km,
                min_samples=min_samples
            )
    
    if st.session_state.clustered_df is not None:
        clustered_df = st.session_state.clustered_df
        cluster_summaries = clustered_df.attrs.get('cluster_summaries', pd.DataFrame())
        
        st.subheader("Cluster Map View")
        cluster_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5)
        colors = px.colors.qualitative.Plotly
        
        for _, cluster in cluster_summaries.iterrows():
            cluster_data = clustered_df[clustered_df['cluster'] == cluster['cluster_id']]
            color = colors[cluster['cluster_id'] % len(colors)]
            
            folium.CircleMarker(
                location=[cluster['center_lat'], cluster['center_lon']],
                radius=10,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=f"""
                    <b>Cluster {cluster['cluster_id']}</b><br>
                    <b>Main Issue:</b> {cluster['main_issue']}<br>
                    <b>Category:</b> {cluster['category']}<br>
                    <b>Reports:</b> {cluster['count']}
                """
            ).add_to(cluster_map)
            
            for _, row in cluster_data.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=5,
                    color=color,
                    fill=True,
                    fill_opacity=0.5
                ).add_to(cluster_map)
        
        folium.LayerControl().add_to(cluster_map)
        st_folium(cluster_map, width=1200, height=600)
        
        st.subheader("Cluster Summaries")
        for _, cluster in cluster_summaries.iterrows():
            cluster_data = clustered_df[clustered_df['cluster'] == cluster['cluster_id']]
            with st.expander(f"📍 Cluster {cluster['cluster_id']} ({cluster['count']} reports)", expanded=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**📍 Center:** {cluster['center_lat']:.4f}, {cluster['center_lon']:.4f}")
                    st.markdown(f"**🏷️ Main Category:** {cluster['category']}")
                with c2:
                    st.markdown(f"**📊 Sentiment:** {len(cluster_data[cluster_data['sentiment']=='Positive'])} 👍 / {len(cluster_data[cluster_data['sentiment']=='Negative'])} 👎")
                    st.markdown(f"**📝 Main Issue:** {cluster['main_issue']}")
                
                st.markdown("**🔑 Keywords:**")
                words = " ".join(cluster_data['text']).split()
                word_freq = Counter([w.lower() for w in words if len(w) > 3]).most_common(5)
                st.write(", ".join([f"{w[0]} ({w[1]})" for w in word_freq]))
                
                st.markdown("**📜 Sample Reports:**")
                for i, feedback in enumerate(cluster_data['text'].head(3), 1):
                    st.write(f"{i}. {feedback[:150]}...")

with tab4:
    st.header("Feedback Explorer")
    
    search_term = st.text_input("🔍 Search feedback text", "")
    if search_term:
        results = filtered_df[filtered_df['text'].str.contains(search_term, case=False)]
    else:
        results = filtered_df
    
    sentiment_select = st.multiselect(
        "Filter by sentiment",
        options=filtered_df['sentiment'].unique(),
        default=[]
    )
    if sentiment_select:
        results = results[results['sentiment'].isin(sentiment_select)]
    
    st.dataframe(
        results[['text', 'sentiment', 'category', 'location', 'timestamp']],
        column_config={
            "text": "Feedback",
            "sentiment": "Sentiment",
            "category": "Category",
            "location": "Location",
            "timestamp": "Date"
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )

# Footer
st.markdown("---")
st.markdown("### Feedback Analyzer")