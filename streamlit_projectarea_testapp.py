import streamlit as st
import streamlit.components.v1 as components

# HTML and JS for the Leaflet map
leaflet_map_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <style>
        #map { height: 400px; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([51.505, -0.09], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(map);
    </script>
</body>
</html>
"""

def main():
    st.title("Streamlit Leaflet Map Integration")

    # Use the `components.html` function to render the custom HTML/JS for the Leaflet map
    components.html(leaflet_map_html, height=450)

if __name__ == "__main__":
    main()


# import streamlit as st
# import geopandas as gpd
# import requests
# from shapely.geometry import shape

# def fetch_data():
#     url = "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/epa_ira/FeatureServer/0/query"
#     params = {
#         'where': '1=1',  # Modify this as needed to filter the data
#         'outFields': '*',  # Adjust the fields you need
#         'outSR': '4326',  # EPSG code for WGS84
#         'f': 'geojson'  # Fetches the data in GeoJSON format
#     }
#     response = requests.get(url, params=params)
#     data = response.json()
#     gdf = gpd.GeoDataFrame.from_features(data["features"])
#     return gdf

# def main():
#     st.title('Census Tracts Selection and Drawing')

#     # Load the data
#     gdf = fetch_data()

#     st.dataframe(gdf)

#     # # Display the map to show the data and allow drawing
#     # st.map(gdf)

#     # Add functionality for user interaction (selection/drawing and exporting)
#     # This part would need more specific details on how you want the user to interact with the map

#     # Placeholder for user interactions
#     st.write("Select tracts or draw on the map.")

#     # Export functionality
#     # You need to add actual logic to capture user selections or drawings and then export that data

# if __name__ == "__main__":
#     main()
