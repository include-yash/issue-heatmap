from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd

def perform_clustering(df, n_clusters=5):
    """Perform spatio-textual clustering on feedback data"""
    
    # Filter out entries without location data
    df = df.dropna(subset=['latitude', 'longitude'])
    
    # 1. Text Embedding (using Sentence-BERT)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    text_embeddings = model.encode(df['text'].tolist())
    
    # 2. Normalize Location Data
    locations = df[['latitude', 'longitude']].values
    locations = (locations - np.mean(locations, axis=0)) / np.std(locations, axis=0)
    
    # 3. Combine Features (weight location 30%, text 70%)
    combined_features = np.hstack([
        text_embeddings * 0.7, 
        locations * 0.3
    ])
    
    # 4. Perform K-Means Clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(combined_features)
    
    # 5. Add Cluster Info to DataFrame
    df['cluster'] = clusters
    return df