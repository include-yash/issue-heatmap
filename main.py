import json
from modules.sentiment_analysis import analyze_sentiment_and_categorize
from geopy.geocoders import Nominatim
import time

# Initialize geocoder
geolocator = Nominatim(user_agent="feedback-analyzer")

# Helper function to get lat/lon from a location name
def get_lat_lon(location_name):
    try:
        location = geolocator.geocode(location_name, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        print(f"Error geocoding {location_name}: {e}")
        return None, None

# Step 1: Load feedback data
with open('data/feedback_data.json', 'r') as file:
    feedback_data = json.load(file)

# Step 2: Analyze sentiment, emotion, category, and geocode location for each feedback entry
results = []

for feedback in feedback_data:
    text = feedback["text"]
    
    # Analyze sentiment, emotion, and category
    sentiment, emotion, category = analyze_sentiment_and_categorize(text)
    
    # Geocode location
    location_name = feedback["location"]
    latitude, longitude = get_lat_lon(location_name)
    
    # Append the result with sentiment, emotion, category, and geolocation
    results.append({
        "text": text,
        "user": feedback["user"],
        "location": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": feedback["timestamp"],
        "sentiment": sentiment,
        "emotion": emotion,
        "category": category
    })

# Step 3: Save the results to a new JSON file
with open('data/feedback_results_with_location.json', 'w') as file:
    json.dump(results, file, indent=4)

print("Sentiment, Emotion, Categorization, and Geolocation Analysis Completed. Results saved in 'feedback_results_with_location.json'")
