import streamlit as st
import geopandas as gpd
import requests
from shapely.geometry import shape

def fetch_data():
    url = "https://services.arcgis.com/cJ9YHowT8TU7DUyn/arcgis/rest/services/epa_ira/FeatureServer/0/query"
    params = {
        'where': '1=1',  # Modify this as needed to filter the data
        'outFields': '*',  # Adjust the fields you need
        'outSR': '4326',  # EPSG code for WGS84
        'f': 'geojson'  # Fetches the data in GeoJSON format
    }
    response = requests.get(url, params=params)
    data = response.json()
    gdf = gpd.GeoDataFrame.from_features(data["features"])
    return gdf

def main():
    st.title('Census Tracts Selection and Drawing')

    # Load the data
    gdf = fetch_data()

    st.dataframe(gdf)

    # # Display the map to show the data and allow drawing
    # st.map(gdf)

    # Add functionality for user interaction (selection/drawing and exporting)
    # This part would need more specific details on how you want the user to interact with the map

    # Placeholder for user interactions
    st.write("Select tracts or draw on the map.")

    # Export functionality
    # You need to add actual logic to capture user selections or drawings and then export that data

if __name__ == "__main__":
    main()
