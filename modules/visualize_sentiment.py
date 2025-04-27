import json
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import pandas as pd


# Load the feedback results
with open('data/feedback_results.json', 'r') as file:
    feedback_results = json.load(file)

# Extract sentiments
sentiments = [entry['sentiment'] for entry in feedback_results]

# Count sentiment occurrences
sentiment_count = Counter(sentiments)

# Plot the sentiment distribution
plt.figure(figsize=(8, 5))
sns.barplot(x=list(sentiment_count.keys()), y=list(sentiment_count.values()), palette='coolwarm')
plt.title("Sentiment Distribution")
plt.xlabel("Sentiment")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

# Extract emotions
emotions = [entry['emotion'] for entry in feedback_results]

# Count emotion occurrences
emotion_count = Counter(emotions)

# Plot the emotion distribution
plt.figure(figsize=(10, 6))
sns.barplot(x=list(emotion_count.keys()), y=list(emotion_count.values()), palette='Set2')
plt.title("Emotion Distribution")
plt.xlabel("Emotion")
plt.ylabel("Count")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Extract categories
categories = [entry['category'] for entry in feedback_results]

# Count category occurrences
category_count = Counter(categories)

# Plot the category distribution
plt.figure(figsize=(10, 6))
sns.barplot(x=list(category_count.keys()), y=list(category_count.values()), palette='Set3')
plt.title("Feedback Category Distribution")
plt.xlabel("Category")
plt.ylabel("Count")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Count feedbacks per location
location_count = Counter(entry['location'] for entry in feedback_results)

# Create heatmap data
locations = list(location_count.keys())
counts = list(location_count.values())

# Create a DataFrame for seaborn heatmap
heatmap_data = pd.DataFrame({'Location': locations, 'Count': counts})
heatmap_data = heatmap_data.pivot_table(index='Location', values='Count', aggfunc='sum')

# Plot the heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(heatmap_data, annot=True, cmap='YlOrRd', linewidths=1, fmt='g')
plt.title("Feedback Density by Location")
plt.xlabel("Feedback Count")
plt.ylabel("Location")
plt.tight_layout()
plt.show()


def show_top_issues(data, top_n=3):
    from collections import Counter

    issue_counter = Counter()
    for item in data:
        issue_words = item['text'].lower().split()
        issue_counter.update(issue_words)

    # Exclude common stopwords
    stopwords = {'in', 'the', 'is', 'are', 'on', 'for', 'a', 'of', 'to', 'and', 'its', 'it'}
    filtered_issues = {word: count for word, count in issue_counter.items() if word not in stopwords and len(word) > 3}

    # Get top N issues
    top_issues = sorted(filtered_issues.items(), key=lambda x: x[1], reverse=True)[:top_n]

    print(f"\n🔍 Top {top_n} Most Reported Issues:")
    for issue, count in top_issues:
        print(f"- {issue}: {count} reports")

# Show the top 3 most reported issues
show_top_issues(feedback_results)

