import json
import folium
from folium.plugins import HeatMap, MarkerCluster
from folium import Marker
from folium.map import Icon
from folium import MacroElement
from jinja2 import Template

# Load feedback results with explicit UTF-8 encoding
try:
    with open('../data/feedback_results_with_location.json', 'r', encoding='utf-8') as file:
        feedback_data = json.load(file)
    print(f"Loaded {len(feedback_data)} feedback entries")
except UnicodeDecodeError as e:
    print(f"Error: Failed to decode JSON file. Ensure the file is encoded in UTF-8. Details: {e}")
    exit(1)
except FileNotFoundError:
    print("Error: JSON file not found at '../data/feedback_results_with_location.json'.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON format. Details: {e}")
    exit(1)

# Define a basic map centered on India with a cleaner tileset
map_center = [20.5937, 78.9629]  # India Center
mymap = folium.Map(
    location=map_center,
    zoom_start=5,
    tiles='CartoDB Positron',
    attr='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>'
)

# Create feature groups for heatmap and markers (for layer control)
heatmap_layer = folium.FeatureGroup(name='Heatmap', show=True)
marker_layer = folium.FeatureGroup(name='Markers', show=True)

# Prepare data for the initial heatmap and markers
heat_data = []
filtered_feedback = []

# Filter feedback (initially no filters, will be controlled via JS)
for entry in feedback_data:
    lat = entry.get('latitude')
    lon = entry.get('longitude')
    
    if lat and lon:
        # Add to heatmap data
        heat_data.append([lat, lon])
        # Prepare feedback for markers
        filtered_feedback.append(entry)

# Add HeatMap layer with refined parameters, ensuring gradient keys are strings
HeatMap(
    heat_data,
    radius=12,
    blur=8,
    max_zoom=13,
    gradient={
        "0.2": "blue",
        "0.4": "lime",
        "0.6": "yellow",
        "0.8": "orange",
        "1.0": "red"
    }
).add_to(heatmap_layer)

# Add heatmap layer to map
heatmap_layer.add_to(mymap)

# Create a MarkerCluster for better visualization of dense marker areas
marker_cluster = MarkerCluster().add_to(marker_layer)

# Add custom markers for different categories with color-coding
category_colors = {
    'Health': 'green',
    'Education': 'blue',
    'Infrastructure': 'orange',
    'Environment': 'purple',
    'Public Safety': 'red'
}

# Add custom markers for each entry in filtered feedback
for entry in filtered_feedback:
    lat = entry.get('latitude')
    lon = entry.get('longitude')
    
    if lat and lon:
        # Set a color based on category
        category = entry['category']
        marker_color = category_colors.get(category, 'gray')
        
        # Prepare the popup message with styled HTML
        popup_message = f"""
        <div style="font-family: Arial; font-size: 12px; padding: 10px; max-width: 300px;">
            <b style="color: #333;">User:</b> {entry['user']}<br>
            <b style="color: #333;">Sentiment:</b> {entry['sentiment']}<br>
            <b style="color: #333;">Emotion:</b> {entry['emotion']}<br>
            <b style="color: #333;">Category:</b> {entry['category']}<br>
            <b style="color: #333;">Feedback:</b> {entry['text']}<br>
            <b style="color: #333;">Timestamp:</b> {entry['timestamp']}
        </div>
        """
        
        # Add custom marker with an icon and styled popup
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_message, max_width=300),
            icon=Icon(color=marker_color, icon='info-sign', prefix='fa')
        ).add_to(marker_cluster)

# Add marker layer to map
marker_layer.add_to(mymap)

# Convert feedback data to JSON for client-side filtering
feedback_json = json.dumps(feedback_data)

# Add Leaflet.AwesomeMarkers resources to the map's header
mymap.get_root().header.add_child(folium.Element('''
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css" />
<script src="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.min.js"></script>
'''))

# Add a polished, collapsible legend
legend_html = '''
<div style="position: fixed; bottom: 50px; left: 50px; width: 220px; background-color: rgba(255, 255, 255, 0.9);
            z-index:9999; font-size: 12px; border: 2px solid #ccc; border-radius: 5px; padding: 10px;
            font-family: Arial;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <b>Category Legend</b>
        <button onclick="toggleLegend()" style="background: none; border: none; cursor: pointer; font-size: 14px;">▲</button>
    </div>
    <div id="legend-content">
        <i class="fa fa-circle" style="color: green"></i> Health<br>
        <i class="fa fa-circle" style="color: blue"></i> Education<br>
        <i class="fa fa-circle" style="color: orange"></i> Infrastructure<br>
        <i class="fa fa-circle" style="color: purple"></i> Environment<br>
        <i class="fa fa-circle" style="color: red"></i> Public Safety<br>
    </div>
</div>
<script>
function toggleLegend() {
    var content = document.getElementById('legend-content');
    var button = event.target;
    if (content.style.display === 'none') {
        content.style.display = 'block';
        button.innerHTML = '▲';
    } else {
        content.style.display = 'none';
        button.innerHTML = '▼';
    }
}
</script>
'''

mymap.get_root().html.add_child(folium.Element(legend_html))

# Add layer control to toggle heatmap and markers
folium.LayerControl().add_to(mymap)

# Add a control panel for dynamic filtering with client-side JavaScript
control_panel_html = f'''
<div style="position: fixed; top: 10px; right: 10px; width: 250px; background-color: rgba(255, 255, 255, 0.9);
            z-index:9999; font-size: 12px; border: 2px solid #ccc; border-radius: 5px; padding: 10px;
            font-family: Arial;">
    <b>Filter Feedback</b><br><br>
    <label for="sentiment-filter">Sentiment:</label><br>
    <select id="sentiment-filter" style="width: 100%; padding: 5px;">
        <option value="">All</option>
        <option value="Positive">Positive</option>
        <option value="Neutral">Neutral</option>
        <option value="Negative">Negative</option>
    </select><br><br>
    <label for="emotion-filter">Emotion:</label><br>
    <select id="emotion-filter" style="width: 100%; padding: 5px;">
        <option value="">All</option>
        <option value="happiness">Happiness</option>
        <option value="sadness">Sadness</option>
        <option value="fear">Fear</option>
        <option value="disgust">Disgust</option>
        <option value="surprise">Surprise</option>
        <option value="anger">Anger</option>
    </select><br><br>
    <label for="category-filter">Category:</label><br>
    <select id="category-filter" style="width: 100%; padding: 5px;">
        <option value="">All</option>
        <option value="Health">Health</option>
        <option value="Education">Education</option>
        <option value="Infrastructure">Infrastructure</option>
        <option value="Environment">Environment</option>
        <option value="Public Safety">Public Safety</option>
    </select><br><br>
    <button onclick="applyFilters()" style="width: 100%; padding: 5px; background-color: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer;">Apply Filters</button>
</div>
<script>
// Feedback data embedded in the HTML
var feedbackData = {feedback_json};

// Map and layer references
var map = null;
var heatmapFeatureGroup = null;
var markerFeatureGroup = null;
var currentHeatLayer = null;
var currentMarkerCluster = null;

// Initialize the map and layers after the map is loaded
document.addEventListener('DOMContentLoaded', function() {{
    try {{
        map = window.map_1; // Folium's default map ID
        
        // Find existing layers by name
        map.eachLayer(function(layer) {{
            if (layer.options && layer.options.name === 'Heatmap') {{
                heatmapFeatureGroup = layer;
            }} else if (layer.options && layer.options.name === 'Markers') {{
                markerFeatureGroup = layer;
            }}
        }});

        if (!heatmapFeatureGroup || !markerFeatureGroup) {{
            console.error('Could not find Heatmap or Markers layers');
            return;
        }}

        console.log('Map initialized with ' + feedbackData.length + ' feedback entries');
        applyFilters(); // Initial render
    }} catch (e) {{
        console.error('Error initializing map: ', e);
    }}
}});

function applyFilters() {{
    try {{
        // Get filter values
        var sentiment = document.getElementById('sentiment-filter').value.toLowerCase();
        var emotion = document.getElementById('emotion-filter').value.toLowerCase();
        var category = document.getElementById('category-filter').value.toLowerCase();

        // Filter feedback data
        var filteredData = feedbackData.filter(function(entry) {{
            var entrySentiment = entry.sentiment ? entry.sentiment.toLowerCase() : '';
            var entryEmotion = entry.emotion ? entry.emotion.toLowerCase() : '';
            var entryCategory = entry.category ? entry.category.toLowerCase() : '';

            return (
                (sentiment === '' || entrySentiment === sentiment) &&
                (emotion === '' || entryEmotion === emotion) &&
                (category === '' || entryCategory === category)
            );
        }});

        console.log('Filtered ' + filteredData.length + ' entries');

        // Update Heatmap Layer
        if (currentHeatLayer) {{
            heatmapFeatureGroup.removeLayer(currentHeatLayer);
        }}
        
        if (filteredData.length > 0) {{
            var heatData = filteredData.map(function(entry) {{
                return [entry.latitude, entry.longitude];
            }});
            currentHeatLayer = L.heatLayer(heatData, {{
                radius: 12,
                blur: 8,
                maxZoom: 13,
                gradient: {{ '0.2': 'blue', '0.4': 'lime', '0.6': 'yellow', '0.8': 'orange', '1.0': 'red' }}
            }});
            heatmapFeatureGroup.addLayer(currentHeatLayer);
        }}

        // Update Marker Layer
        if (currentMarkerCluster) {{
            markerFeatureGroup.removeLayer(currentMarkerCluster);
        }}
        
        var markerCluster = L.markerClusterGroup();
        var categoryColors = {{
            'health': 'green',
            'education': 'blue',
            'infrastructure': 'orange',
            'environment': 'purple',
            'public safety': 'red'
        }};

        filteredData.forEach(function(entry) {{
            if (!entry.latitude || !entry.longitude) return;

            var popupMessage = `<div style="font-family: Arial; font-size: 12px; padding: 10px; max-width: 300px;">
                <b>User:</b> ${{entry.user}}<br>
                <b>Sentiment:</b> ${{entry.sentiment}}<br>
                <b>Emotion:</b> ${{entry.emotion}}<br>
                <b>Category:</b> ${{entry.category}}<br>
                <b>Feedback:</b> ${{entry.text}}<br>
                <b>Timestamp:</b> ${{entry.timestamp}}
            </div>`;

            var markerColor = categoryColors[entry.category.toLowerCase()] || 'gray';
            var marker = L.marker([entry.latitude, entry.longitude], {{
                icon: L.AwesomeMarkers.icon({{
                    icon: 'info-sign',
                    prefix: 'fa',
                    markerColor: markerColor
                }})
            }}).bindPopup(popupMessage, {{ maxWidth: 300 }});
            
            markerCluster.addLayer(marker);
        }});

        currentMarkerCluster = markerCluster;
        markerFeatureGroup.addLayer(currentMarkerCluster);

    }} catch (e) {{
        console.error('Error applying filters: ', e);
    }}
}}
</script>
'''

mymap.get_root().html.add_child(folium.Element(control_panel_html))

# Save the map to an HTML file with error handling
try:
    mymap.save('../outputs/interactive_heatmap_with_filters.html')
    print("✅ Enhanced interactive map with functional filters, clustering, and improved styling saved to 'outputs/interactive_heatmap_with_filters.html'")
except Exception as e:
    print(f"Error: Failed to save the map. Details: {e}")
    exit(1)