from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

# Initialize sentiment analyzer (VADER)
analyzer = SentimentIntensityAnalyzer()

# Emotion detection model from HuggingFace
emotion_analyzer = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")

# Categorization function
def categorize_feedback(feedback):
    categories = {
        "Infrastructure": ["potholes", "roads", "street lights", "construction", "sewerage"],
        "Health": ["water supply", "health", "hospital", "medicines", "doctors", "sanitation"],
        "Environment": ["garbage", "pollution", "waste", "cleanliness", "recycling"],
        "Education": ["school", "education", "learning", "teachers", "students", "classroom"],
        "Public Safety": ["traffic", "safety", "accident", "crime", "emergency", "security", "killing","kidnapping"]
    }
    
    feedback_lower = feedback.lower()
    
    for category, keywords in categories.items():
        if any(keyword in feedback_lower for keyword in keywords):
            return category
    return "Uncategorized"  # If no match, return Uncategorized

def analyze_sentiment_and_categorize(feedback):
    """
    Analyzes sentiment using VADER, emotion using a pre-trained transformer,
    and categorizes the feedback.
    """
    # VADER Sentiment Analysis
    sentiment_score = analyzer.polarity_scores(feedback)
    sentiment = "Neutral"
    if sentiment_score["compound"] >= 0.05:
        sentiment = "Positive"
    elif sentiment_score["compound"] <= -0.05:
        sentiment = "Negative"
    
    # Emotion Detection
    emotion_result = emotion_analyzer(feedback)
    emotion = emotion_result[0]['label']
    
    # Categorize Feedback
    category = categorize_feedback(feedback)
    
    return sentiment, emotion, category

# Test with an example feedback
feedback_example = "There are huge potholes in Sector 16, it's really dangerous!"
sentiment, emotion, category = analyze_sentiment_and_categorize(feedback_example)
print(f"Sentiment: {sentiment}, Emotion: {emotion}, Category: {category}")
