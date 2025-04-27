import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import StandardScaler
from geopy.distance import geodesic

def calculate_spatial_radius(coords, max_radius_km=5):
    """Calculate appropriate epsilon for DBSCAN based on desired max radius"""
    # Convert km to radians (approx. for Earth's radius)
    return max_radius_km / 6371.0

def perform_clustering(df, max_radius_km=5, min_samples=3):
    """Perform spatio-textual clustering with predefined categories"""
    
    # Filter out entries without location data
    df = df.dropna(subset=['latitude', 'longitude'])
    
    # Predefined categories
    VALID_CATEGORIES = ['Health', 'Education', 'Infrastructure', 'Environment', 'Public Safety']
    df = df[df['category'].isin(VALID_CATEGORIES)]
    
    if len(df) < min_samples:
        return df.assign(cluster=-1)
    
    # 1. Text Embedding
    model = SentenceTransformer('all-MiniLM-L6-v2')
    text_embeddings = model.encode(df['text'].tolist(), batch_size=32, show_progress_bar=False)
    
    # 2. Category Encoding
    category_encoded = pd.get_dummies(df['category']).values
    
    # 3. Location Data (in radians for DBSCAN)
    coords = np.radians(df[['latitude', 'longitude']].values)
    
    # 4. Combine Features
    scaler = StandardScaler()
    text_scaled = scaler.fit_transform(text_embeddings)
    
    # Weight features: 50% text, 30% location, 20% category
    combined_features = np.hstack([
        text_scaled * 0.5,
        coords * 0.3,
        category_encoded * 0.2
    ])
    
    # 5. DBSCAN Clustering
    eps = calculate_spatial_radius(coords, max_radius_km)
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='haversine', n_jobs=-1)
    clusters = dbscan.fit_predict(coords)  # Cluster primarily on location
    
    # Refine clusters based on text and category similarity
    final_clusters = np.full(len(df), -1, dtype=int)
    current_cluster = 0
    
    for cluster_id in np.unique(clusters):
        if cluster_id == -1:
            continue
            
        cluster_idx = np.where(clusters == cluster_id)[0]
        cluster_features = combined_features[cluster_idx]
        
        # Sub-cluster within spatial cluster based on content
        kmeans = KMeans(n_clusters=min(len(cluster_idx), 3), random_state=42)
        sub_clusters = kmeans.fit_predict(cluster_features)
        
        for sub_id in np.unique(sub_clusters):
            sub_idx = cluster_idx[sub_clusters == sub_id]
            final_clusters[sub_idx] = current_cluster
            current_cluster += 1
    
    df = df.assign(cluster=final_clusters)
    
    # Add cluster summaries
    cluster_summaries = []
    for cluster_id in np.unique(final_clusters):
        if cluster_id == -1:
            continue
        cluster_data = df[df['cluster'] == cluster_id]
        center = (
            cluster_data['latitude'].mean(),
            cluster_data['longitude'].mean()
        )
        cluster_summaries.append({
            'cluster_id': cluster_id,
            'center_lat': center[0],
            'center_lon': center[1],
            'category': cluster_data['category'].mode()[0],
            'count': len(cluster_data),
            'main_issue': cluster_data['text'].iloc[0][:100] + "..."
        })
    
    df.attrs['cluster_summaries'] = pd.DataFrame(cluster_summaries)
    return df