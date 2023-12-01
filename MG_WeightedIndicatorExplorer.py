import streamlit as st
import pandas as pd
import base64
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from datetime import datetime
from scipy.stats import zscore
import json
from folium.plugins import Fullscreen

st.set_page_config(
    page_title='Madagascar - Weighted Vulnerability Index Explorer (Streamlit App Demo)',
    page_icon="🗺️",
    layout="wide",
)
st.title('Madagascar - Weighted Vulnerability Index Explorer (Streamlit App Demo)')

st.markdown(
    """ This tool gives you the ability to see how altering the weighted importance of each vulnerability indicaor affects the Vulnerability Index Score and Percentile of each Commune. To adjust the indicators, use the sliders to your left, scroll down, and hit the submit button. 
    The tool will take about 30 seconds to re-load depending on your internet connection. Also, the maps and data tables are interactive!

---
*Once weights are submitted, you can download html versions of the Weighted map. Please note, you must open these files using a browser (e.g., Chrome. Edge, or FireFox).* 
"""
)
   
# Define Processing Column Groups
def define_processing_col_groups():
    ''' These column lists are used throughout the .py script. The core columns are returned with each dataframe output. 
    The columns to normalize are all fed into the create z score index function. The reverse columns are an exception within
    that z score function. For those columns, the resulting z score will be mulitplied by -1 to indicate a negative relationship
    with the other indicators. 
    '''
    core_columns = [
        'OBJECTID',
        'ADM1_PCODE','ADM1_EN','ADM1_TYPE','ADM2_PCODE','ADM2_EN','ADM2_TYPE','ADM3_PCODE','ADM3_EN','ADM3_TYPE',
        'StudyRegio','StudyReg',
        'Pop2023','Pop2024',
        'geometry'
        ]
    
    columns_to_normalize = [
        'CON_DFA1C','CON_DFA2C','CON_NDFAC1','CON_NDFAC2',
        'ST_SUM',
        'RD_DENSUNREV',
        'IPC_AVC',
        'MK_DIST','MK_VOLA','MK_ANOM',
        'DIS_AFF','DIS_CROPDMG',
        'USAID_VAC', 'USAID_SD', 'USAID_IPC','USAID_STUNTING','USAIDWEALTH','USAID_PIF','USAID_PRECIP','USAID_WALKING',
      ]
    
    reverse = ['RD_DENSUNREV']
    return(core_columns, columns_to_normalize, reverse)

@st.cache_data  # 👈 Add the caching decorator
def load_geopandas_df(geojson_path):
    ''' This function loads a geopandas datframe based on a geojson URL.'''
    # Load Dataframe with Initial Vulnerability Index (Default Weights = 0.1)
    df = gpd.read_file(geojson_path)
    df.dropna(inplace=True)
    return(df)
    
def create_zscore_index(sdf, weights_dict):
    ''' First, this function loops through the columns to normalize list, calculates a new column based on the z-score, 
    and then multiplies it by the weight. The weight is either the default (0.1) or provided via a weights_dict. If a column
    is also in the reverse list, then the z score is multiplied by -1. After the normalized and weighted columns are created,
    they are summed to create the vulnerability index. Lastly, we calculate the percentile of this index to more readily compare
    the results of different weighting schemes.'''
    core_columns, columns_to_normalize, reverse = define_processing_col_groups()
    normalized_df = pd.DataFrame()
    # Loop through columns to normalize
    for column in columns_to_normalize:
        normalized_df[column] = sdf[column]
        is_reverse = column in reverse
        normalized_col_suffix = '_normalized' 
        normalized_df[column + normalized_col_suffix] = -zscore(sdf[column]) if is_reverse else zscore(sdf[column])
        weight_col_suffix = '_weight'
        weight_value = 0.1 if weights_dict is None else weights_dict[column]
        normalized_df[column + weight_col_suffix] = weight_value
        final_suffix = "_weighted_zscore"
        normalized_df[column + final_suffix] = normalized_df[column + normalized_col_suffix]  * normalized_df[column + weight_col_suffix]
    normalized_df['Vulnerability_Index'] = round(normalized_df.filter(like=final_suffix, axis=1).sum(axis=1),4)
    normalized_df['Vulnerability_Index_Percentile'] = round(normalized_df['Vulnerability_Index'].rank(pct=True) * 100)
    result_df = pd.concat([sdf[core_columns], normalized_df], axis=1)
    return result_df

def create_vulnerability_index(df, weights_dict):
    '''This function creates a new dataframe with the vulnerability index and percentile that has columns sorted for easier viewing.'''
    # Create Weighted Vulnerablity Index
    df = create_zscore_index(df , weights_dict=weights_dict)
    df.set_index(['OBJECTID','ADM3_EN','Vulnerability_Index','Vulnerability_Index_Percentile'], inplace=True)
    df = df.reindex(sorted(df.columns), axis=1)
    df.reset_index(inplace=True)
    df = gpd.GeoDataFrame(df, geometry = 'geometry')
    return(df)


def render_map(df, choropleth_name):
    '''This function renders a choropleth map with custom html based on the geometry and vulerability index percentile columns'''
    normalized_cols = [col for col in df.columns if col.endswith('_normalized')]
    # Get the bounding box of the GeoDataFrame
    bbox = df.total_bounds
    # Calculate the center of the bounding box
    map_center = [(bbox[1] + bbox[3]) / 2, (bbox[0] + bbox[2]) / 2]
    # Create Map Object
    m1= folium.Map(location=map_center, zoom_start=7,
                   tiles=None)
    tile = folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Satellite',
        overlay = False,
        control = True
       ).add_to(m1)
    # Create a choropleth map based on the specified column
    choropleth_layer = folium.Choropleth(
        geo_data= df,
        name = choropleth_name,
        data = df,
        columns=['ADM3_EN','Vulnerability_Index_Percentile'],
        # key_on='feature.id',
        key_on='feature.properties.ADM3_EN',
        fill_color='RdYlBu_r',
        fill_opacity=0.7,
        line_opacity=0.5,
        legend_name='Vulnerability Index (Percentile)',
        # legend_name = 'Custom Legend',
        highlight = True,
        style_function=lambda x: {'weight': 1, 'color': 'white', 'fillOpacity': 1.0},
    ).add_to(m1)
    
    # Create a custom CSS style for the legend control
    legend_style = """
    <style>
        .leaflet-control.legend {
            background-color: rgba(0,0,0,0.6);  /* Background color */
            color: white; /* Text color */
            border: 1px solid #333;
            border-radius: 2px;
            padding: 2px;
        }
    
        .leaflet-control.legend .key {
          fill: white; /* Text color within the key class*/
        }
    
    </style>
    """
    # Add the custom CSS style to the choropleth layer's HTML content
    m1.get_root().html.add_child(folium.Element(legend_style))
    
    # Add GeoJson layer with pop-ups
    folium.GeoJson(
        df,
        name='pup',
        style_function=lambda x: {'fillOpacity': 0, 'color': 'transparent', 'weight': 0},
        highlight_function=lambda x: {'weight': 3, 'color': 'white'},
        tooltip=folium.GeoJsonTooltip(fields=
          ['ADM3_EN','Vulnerability_Index','Vulnerability_Index_Percentile'], aliases=['Commune', "VI", "VI Percentile"]
                                      ),
        # popup=folium.GeoJsonPopup(
        #     fields = ['ADM3_EN','Vulnerability_Index','Vulnerability_Index_Percentile'] + normalized_cols,
        #     aliases=['Commune', "VI", "VI Percentile"] + normalized_cols,
        #     max_width=600, max_height=200, sticky=False
        #     ),
        control= False
    ).add_to(m1)
    
    # Add Esri Map Labels
    map_labels = folium.TileLayer(
        tiles = 'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri World Boundaries and Places',
        overlay = True,
        show = True,
        control = True
    )
    map_labels.add_to(m1)
    
    # Add to Layer Control
    folium.LayerControl().add_to(m1)
    # Add Fullscreen plugin
    Fullscreen().add_to(m1)
    # st.subheader(choropleth_name)
    # folium_static(m1._repr_html_(), width=725, returned_objects=[])
    return(m1)

def get_key_by_value(dictionary, search_value):
  """
  Returns the key in the dictionary corresponding to the provided search_value.
  """
  for key, value in dictionary.items():
      if value == search_value:
          return key
  return None  # Return None if the value is not found
  
def download_map(map_to_download, map_title, timestamp):
    '''Creates and displays a download link for map as HTML File.'''
    html_name = f'{map_title} ({timestamp}).html'
    map_html = map_to_download._repr_html_()
    # Convert the HTML to bytes and encode as base64
    html_bytes = map_html.encode('utf-8')
    b64 = base64.b64encode(html_bytes)
    payload = b64.decode()

    # Create a data URL
    data_url = f'data:text/html;base64,{payload}'
    # Create a download link using Streamlit
    st.markdown(f'<a href="{data_url}" download="{html_name}" target="_blank">Click to Download Map</a>', unsafe_allow_html=True)

def download_dataframe(df, csv_name, timestamp):
    '''Creates and displays a download link for the dataframe as a CSV File.'''
    filename = f'{csv_name} ({timestamp}).csv'
    dynamic_vars = {}
    # Setting the DataFrame as the value for 'dynamic_var' key
    dynamic_vars[f'df_{timestamp}'] = df.copy()
    dynamic_vars[f'df_{timestamp}'].set_index('OBJECTID',inplace=True)
    csv_str = dynamic_vars[f'df_{timestamp}'].loc[:, ~dynamic_vars[f'df_{timestamp}'].columns.isin(['geometry'])].to_csv(index=False)
    csv_bytes = csv_str.encode('utf-8')
    b64 = base64.b64encode(csv_bytes)
    payload = b64.decode()
    st.markdown(f'<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">Download CSV with updated indicator weights and weighted vulnerability index {timestamp}</a>', unsafe_allow_html=True)

# Setup Streatmlit Tabs
tab1,tab2,tab3 = st.tabs(["🗺️ Unweighted VI","🗺️ Weighted VI", "🗺️ Indicator Explorer (ArcGIS)"])

# Define core columns and columns to rank with reverse exception
core_columns, columns_to_normalize, reverse = define_processing_col_groups()

# Load geopandas dataframe 
gdf = load_geopandas_df(r'https://github.com/GSinger-Abt/streamlit_abt/raw/main/MadagascarCommunes_VI_Analysis_v3.geojson')
# Create unweighted vulnerability index dataframe
root_df = create_vulnerability_index(gdf, weights_dict=None)
# Load Map and Map HTML
map_title = 'Unweighted Vulnerability Index'
m1 = render_map(root_df, map_title)
# Display the Folium map using st.components.html
map_html = m1._repr_html_()

# Display Unweighted Map and DataFrame
with tab1:
    st.subheader("Unweighted VI")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with st.container():
        components.html(map_html, width=800, height=500,scrolling = True)
        # download_map(m1, map_title, timestamp)
        st.subheader(f"{map_title} Dataframe:")
        st.dataframe(root_df.set_index('OBJECTID').drop(columns=['geometry']), width=800)
        # download_dataframe(root_df, map_title, timestamp)

# Create a dictionary to store the input widgets
weights_dict = {}
# Set Alias Dict
widget_alias_dict = {
    'Dahalo Flag Actor 1 (Count)': 'CON_DFA1C',
    'Dahalo Flag Actor 2 (Count)': 'CON_DFA2C',
    'Non-Dahalo Flag Actor 1 (Sum)': 'CON_NDFAC1',
    'Non-Dahalo Flag Actor 2 (Sum)':'CON_NDFAC2',
    'Stunting (Sum)':'ST_SUM',
    "Road Density":"RD_DENSUNREV",
    'Distance To Market': 'MK_DIST',
    'Market Price Volatility':'MK_VOLA',
    'Anomaly Rate': 'MK_ANOM',
    'IPC Average': 'IPC_AVC',
    'Distance - Affected': 'DIS_AFF',
    'Crop Damage HA':'DIS_CROPDMG',
    'USAID VAC':'USAID_VAC',
    'USAID SD':'USAID_SD',
    'USAID IPC':'USAID_IPC',
    'USAID STUNTING':'USAID_STUNTING',
    'USAID WEALTH':'USAIDWEALTH',
    'USAID PIF':'USAID_PIF',
    'USAID PRECIP':'USAID_PRECIP',
    'USAID WALKING':'USAID_WALKING',
    }

# Create input widgets for each column with the column name as the description
with st.sidebar:
    with st.form("Weight Sliders"):
        st.title("Indicator Weight Slider")

        for column in columns_to_normalize:
            weights_dict[f'{column}'] = st.slider(
            # weights_dict[f'{column}_weight'] = st.slider(
                # Use a dictionary to remap description
                label = get_key_by_value(widget_alias_dict, column),
                min_value=0.0,
                max_value=1.0,
                value= 0.1,
                step=0.1
            )
        # st.write(weights_dict)
        # Every form must have a submit button.
        submitted = st.form_submit_button('Update!')        

# Display Weighted Map and DataFrame
with tab2:
    # Re-run .py if submitted and add map to tab2
    if submitted:       
        # Render Weighted Tab
        weighted_df = create_vulnerability_index(gdf, weights_dict)
        # Load Map and Map HTML
        map_title2 = 'Weighted Vulnerability Index'
        m2 = render_map(weighted_df, map_title2)
        # Display the Folium map using st.components.html
        map_html2 = m2._repr_html_()
        # Display Sample Dataframe
        with tab2:
            st.subheader(map_title2)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with st.container():
                components.html(map_html2, width=800, height=500, scrolling = True)
                download_map(m2, map_title2, timestamp)
                st.subheader(f"{map_title2} Dataframe:")
                st.dataframe(weighted_df.set_index('OBJECTID').drop(columns=['geometry']), width=800)
                download_dataframe(weighted_df, map_title2, timestamp)
        st.toast('Hooray! Your map is ready!!', icon="🗺️")

# Display Indicator Explorer
with tab3:
    st.title("Indicator Explorer (ArcGIS)")
    experience_builder_url = r'https://experience.arcgis.com/experience/342ca27b75774a02a318f6eb9bb47951'
    components.iframe(experience_builder_url, width = 1600, height = 800, scrolling = True)
    st.link_button('Click here to open the Indicator Explorer in another window.', experience_builder_url)
    # # Use st.markdown with HTML to embed the website using an iframe
    # st.markdown(f'<iframe src="{experience_builder_url}" width="800" height="600"></iframe>', unsafe_allow_html=True)
