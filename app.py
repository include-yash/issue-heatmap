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
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .st-emotion-cache-1v0mbdj {
        border-radius: 10px;
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
    value=[df['timestamp'].min().date(), df['timestamp'].max().date()],
    key="date_range"
)

sentiment_filter = st.sidebar.multiselect(
    "Sentiment",
    options=df['sentiment'].unique(),
    default=df['sentiment'].unique(),
    key="sentiment"
)

category_filter = st.sidebar.multiselect(
    "Category",
    options=df['category'].unique(),
    default=df['category'].unique(),
    key="category"
)

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
if 'n_clusters_used' not in st.session_state:
    st.session_state.n_clusters_used = None

# Main Dashboard
st.title("📊 Feedback Analyzer Pro")

# Metrics Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="metric-card"><h3>Total Feedback</h3><h2>{}</h2></div>'.format(len(filtered_df)), unsafe_allow_html=True)
with col2:
    st.markdown('<div class="metric-card"><h3>Positive</h3><h2 style="color:green;">{}</h2></div>'.format(len(filtered_df[filtered_df['sentiment'] == 'Positive'])), unsafe_allow_html=True)
with col3:
    st.markdown('<div class="metric-card"><h3>Negative</h3><h2 style="color:red;">{}</h2></div>'.format(len(filtered_df[filtered_df['sentiment'] == 'Negative'])), unsafe_allow_html=True)
with col4:
    st.markdown('<div class="metric-card"><h3>Locations</h3><h2>{}</h2></div>'.format(len(filtered_df['location'].unique())), unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Map View", "📈 Analytics", "🔍 Cluster Analysis", "💬 Feedback Explorer"])

with tab1:
    # Enhanced Map
    st.header("Geospatial Feedback Visualization")
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5, tiles="CartoDB Positron")
    
    # Heatmap
    heat_data = [[row['latitude'], row['longitude']] for _, row in filtered_df.iterrows()]
    folium.plugins.HeatMap(heat_data, radius=15, blur=10).add_to(m)
    
    # Clustered Markers
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
    # Analytics
    st.header("Feedback Analytics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sentiment Distribution")
        fig1 = px.pie(filtered_df, names='sentiment', hole=0.3)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Emotion Analysis")
        fig2 = px.bar(filtered_df['emotion'].value_counts(), 
                     labels={'value': 'Count', 'index': 'Emotion'})
        st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("Category Distribution Over Time")
    df_time = filtered_df.copy()
    df_time['date'] = df_time['timestamp'].dt.date
    fig3 = px.histogram(df_time, x='date', color='category', 
                       barmode='stack', nbins=30)
    st.plotly_chart(fig3, use_container_width=True)
    
    # Word Cloud
    st.subheader("Top Keywords")
    text = " ".join(filtered_df['text'])
    if text.strip():
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.warning("No text available for word cloud")

with tab3:
    # Cluster Analysis
    st.header("Issue Clustering")
    st.markdown("Group similar feedback based on location and content")
    
    n_clusters = st.slider("Number of Clusters", 3, 10, 5, key="n_clusters")
    
    if st.button("Run Clustering", key="run_clustering"):
        with st.spinner("Analyzing feedback patterns..."):
            st.session_state.clustered_df = perform_clustering(filtered_df, n_clusters=n_clusters)
            st.session_state.n_clusters_used = n_clusters
    
    if st.session_state.clustered_df is not None:
        st.info(f"Showing clustering results for {st.session_state.n_clusters_used} clusters.")
        clustered_df = st.session_state.clustered_df
        n_clusters = st.session_state.n_clusters_used
        
        # Cluster Map
        st.subheader("Cluster Map View")
        cluster_map = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

        colors = px.colors.qualitative.Plotly[:n_clusters]

        for cluster_id in range(n_clusters):
            cluster_data = clustered_df[clustered_df['cluster'] == cluster_id]
            
            # Create a FeatureGroup for each cluster
            cluster_group = folium.FeatureGroup(name=f'Cluster {cluster_id}')
            
            for _, row in cluster_data.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=5,
                    color=colors[cluster_id],
                    fill=True,
                    fill_opacity=0.7,
                    popup=f"""
                        <b>Cluster {cluster_id}</b><br>
                        <b>Category:</b> {row['category']}<br>
                        <b>Sentiment:</b> {row['sentiment']}<br>
                        {row['text'][:100]}...
                    """
                ).add_to(cluster_group)
            
            cluster_group.add_to(cluster_map)

        # Add MarkerCluster for all points (without custom icons)
        marker_cluster = folium.plugins.MarkerCluster()
        for _, row in clustered_df.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=5,
                color=colors[row['cluster']],
                fill=True,
                fill_opacity=0.7
            ).add_to(marker_cluster)
        marker_cluster.add_to(cluster_map)

        folium.LayerControl().add_to(cluster_map)
        st_folium(cluster_map, width=1200, height=600)
        
        # Cluster Insights
        st.subheader("Cluster Insights")
        cols = st.columns(2)
        
        for cluster_id in range(n_clusters):
            cluster_data = clustered_df[clustered_df['cluster'] == cluster_id]
            if len(cluster_data) > 0:
                with st.expander(f"📌 Cluster {cluster_id} ({len(cluster_data)} issues)", expanded=(cluster_id < 2)):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**📍 Center:** {cluster_data['latitude'].mean():.4f}, {cluster_data['longitude'].mean():.4f}")
                        st.markdown(f"**📅 Date Range:** {cluster_data['timestamp'].min().date()} to {cluster_data['timestamp'].max().date()}")
                    with c2:
                        st.markdown(f"**😊 Sentiment:** {len(cluster_data[cluster_data['sentiment']=='Positive'])} 👍 / {len(cluster_data[cluster_data['sentiment']=='Negative'])} 👎")
                        st.markdown(f"**🏷️ Top Category:** {cluster_data['category'].mode()[0]}")
                    
                    st.markdown("**📝 Common Keywords:**")
                    words = " ".join(cluster_data['text']).split()
                    word_freq = Counter([w.lower() for w in words if len(w) > 3]).most_common(5)
                    st.write(", ".join([f"{w[0]} ({w[1]})" for w in word_freq]))
                    
                    st.markdown("**Sample Feedback:**")
                    for i, feedback in enumerate(cluster_data['text'].head(3), 1):
                        st.write(f"{i}. {feedback[:150]}...")

with tab4:
    # Feedback Explorer
    st.header("Feedback Explorer")
    
    search_term = st.text_input("🔍 Search feedback text", "")
    if search_term:
        results = filtered_df[filtered_df['text'].str.contains(search_term, case=False)]
    else:
        results = filtered_df
    
    sentiment_select = st.multiselect(
        "Filter by sentiment",
        options=filtered_df['sentiment'].unique(),
        default=[],
        key="explorer_sentiment"
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
st.markdown("### Feedback Analyzer Pro v1.1")
st.markdown("Built with Streamlit, Folium, and Scikit-learn")