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
import plotly.express as px


# The following variables are URL references that will need to be updated if this python script is cloned in another GitHub Repo. 
geojson_path = r'https://github.com/GSinger-Abt/streamlit_abt/raw/main/MadagascarCommunes_VI_Analysis_v3.geojson'
experience_builder_url = r'https://experience.arcgis.com/experience/342ca27b75774a02a318f6eb9bb47951'
codebook_url = "https://github.com/GSinger-Abt/streamlit_abt/blob/main/README.md"
read_me_url = "https://github.com/GSinger-Abt/streamlit_abt/blob/main/README.md"

st.set_page_config(
    page_title='Madagascar - Weighted Vulnerability Index (VI) Explorer',
    page_icon="🗺️",
    layout="wide",
)
st.title('Madagascar - Weighted Vulnerability Index (VI) Explorer')
st.header("StreamLit App Draft")

st.markdown(
    """ Use this tool to create a custom Weighted Vulnerability Index for Communes in Madagascar by experimenting with the weights assigned to each vulnerability indicaor. To adjust the indicators, use the sliders to your left, scroll down, and hit the "Update!" button. 
    The tool will take about 30 seconds to re-load depending on your internet connection. Choose a tab below and explore the interactive maps and data tables!

---
"""
    # *Once weights are submitted, you can download html versions of the Weighted map. Please note, you must open these files using a browser (e.g., Chrome. Edge, or FireFox).* 
)

st.link_button("Click here to open Codebook *PLACEHOLDER*", codebook_url, help=None, type='secondary')
st.link_button("Click here to open additional instructions *PLACEHOLDER*", read_me_url, help=None, type='secondary')

@st.cache_data  # 👈 Add the caching decorator
def load_geopandas_df(geojson_path):
    ''' This function loads a geopandas datframe based on a geojson URL.'''
    # Load Dataframe with Initial Vulnerability Index (Default Weights = 0.1)
    df = gpd.read_file(geojson_path)
    df.dropna(inplace=True)
    return(df)
    
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
    
    # Create Thematic Lists of Indicators  
    Conflict_cols = ['CON_DFA1C','USAID_VAC','USAID_SD'] #,'CON_DFA2C','CON_NDFAC1','CON_NDFAC2']
    Disaster_cols = ['DIS_CROPDMG', 'DIS_AFF']
    Food_cols =  ['USAID_IPC','USAID_PIF']
    Health_cols = [ 'USAID_WALKING']
    Market_cols = ['MK_DIST','MK_VOLA','MK_ANOM']
    Precip_cols =  ['USAID_PRECIP']
    Road_cols = ['RD_DENSUNREV']
    Stunting_cols = ['ST_SUM','USAID_STUNTING']
    Wealth_cols = ['USAIDWEALTH']
    # Create Dictionary of Thematic Lists
    thematic_lists = {
        "Conflict": Conflict_cols,
        "Disaster": Disaster_cols,
        "Food Security/Crisis": Food_cols,
        "Health Facility Access": Health_cols,
        "Market": Market_cols,
        "Precipitation": Precip_cols,
        "Road Density": Road_cols,
        "Stunting": Stunting_cols,
        "Wealth" : Wealth_cols
    }
    columns_to_normalize = [item for sublist in thematic_lists.values() for item in sublist]
    reverse = ['RD_DENSUNREV']
    return(core_columns, columns_to_normalize, reverse, thematic_lists)
    
def create_zscore_index(sdf, weights_dict):
    ''' First, this function loops through the columns to normalize list, calculates a new column based on the z-score, 
    and then multiplies it by the weight. The weight is either the default (0.1) or provided via a weights_dict. If a column
    is also in the reverse list, then the z score is multiplied by -1. After the normalized and weighted columns are created,
    they are summed to create the vulnerability index. Lastly, we calculate the percentile of this index to more readily compare
    the results of different weighting schemes.'''
    core_columns, columns_to_normalize, reverse, thematic_lists = define_processing_col_groups()
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

def render_piechart(df, column_list):
    # Create Pie Chart
    thematic_weights_dict = {}
    for key, value in thematic_lists.items():
        weight_cols = [item + "_weight" for item in value]
        thematic_sum = weighted_df[weight_cols].iloc[0].sum()
        thematic_weights_dict[key] = thematic_sum
    data = pd.DataFrame(list(thematic_weights_dict.items()), columns=['Themes', 'Weights'])
    fig = px.pie(data, names='Themes', values='Weights')
    st.plotly_chart(fig)
  
# def download_map(map_to_download, map_title, timestamp):
#     '''Creates and displays a download link for map as HTML File.'''
#     html_name = f'{map_title} ({timestamp}).html'
#     map_html = map_to_download._repr_html_()
#     # Convert the HTML to bytes and encode as base64
#     html_bytes = map_html.encode('utf-8')
#     b64 = base64.b64encode(html_bytes)
#     payload = b64.decode()
#     # Create a data URL
#     data_url = f'data:text/html;base64,{payload}'
#     # Create a download link using Streamlit
#     st.markdown(f'<a href="{data_url}" download="{html_name}" target="_blank">Click to Download Map</a>', unsafe_allow_html=True)

# def download_dataframe(df, csv_name, timestamp):
#     '''Creates and displays a download link for the dataframe as a CSV File.'''
#     filename = f'{csv_name} ({timestamp}).csv'
#     dynamic_vars = {}
#     # Setting the DataFrame as the value for 'dynamic_var' key
#     dynamic_vars[f'df_{timestamp}'] = df.copy()
#     dynamic_vars[f'df_{timestamp}'].set_index('OBJECTID',inplace=True)
#     csv_str = dynamic_vars[f'df_{timestamp}'].loc[:, ~dynamic_vars[f'df_{timestamp}'].columns.isin(['geometry'])].to_csv(index=False)
#     csv_bytes = csv_str.encode('utf-8')
#     b64 = base64.b64encode(csv_bytes)
#     payload = b64.decode()
#     st.markdown(f'<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">Download CSV with updated indicator weights and weighted vulnerability index {timestamp}</a>', unsafe_allow_html=True)  
    
# Setup Streatmlit Tabs
tab2,tab1,tab3 = st.tabs(["🗺️ Weighted VI", "🗺️ Unweighted VI", "🗺️ Indicator Explorer (ArcGIS)"])

# Define core columns and columns to rank with reverse exception
core_columns, columns_to_normalize, reverse, thematic_lists = define_processing_col_groups()

# Load geopandas dataframe 
gdf = load_geopandas_df(geojson_path)
# Create unweighted vulnerability index dataframe
root_df = create_vulnerability_index(gdf, weights_dict=None)
# Load Map and Map HTML
map_title = 'Unweighted Vulnerability Index'
m1 = render_map(root_df, map_title)
# Display the Folium map using st.components.html
map_html = m1._repr_html_()

# Create a dictionary to store the input widgets
weights_dict = {}
# Set Alias Dict (This Dict is inverted later on)
widget_alias_dict = {
    'USAID_PRECIP': 'Average Cumulative Precipitation per Square Kilometer during 2016 - 2023 Growing Season',
    'USAID_IPC': 'Average IPC Scores from 2020-2023',
    'USAID_PIF': 'Average Prevalence of Insufficient Food Consumption',
    'USAID_WALKING': 'Average Walking Travel Time to Nearest Healthcare Facility',
    'DIS_CROPDMG': 'Crop Damage HA',
    'MK_DIST': 'Distance to Nearest Market (KM)',
    'MK_VOLA': 'Market Price Volatility Score',
    'MK_ANOM': 'Market Pricing Anomaly Score',
    'DIS_AFF': 'Number of People Affected by Natural Disasters',
    'USAID_SD': 'Number of Strategic Development Events',
    'ST_SUM': 'Percent Children Stunted (Total)',
    'USAID_STUNTING': 'Prevalence of Stunting',
    'RD_DENSUNREV': "Road Density (Reversed)",
    'USAIDWEALTH': 'Relative Wealth Index (Reversed)',
    'CON_DFA1C': 'Violence Against Civilians from Dahalo Attacks',
    'USAID_VAC': 'Violence Against Civilians (Total)',
    # 'IPC_AVC': 'Average IPC Score',
    # 'CON_DFA2C': 'Dahalo Flag Actor 2 (Count); Placeholder',
    # 'CON_NDFAC1': 'Non-Dahalo Flag Actor 1 (Sum)',
    # 'CON_NDFAC2': 'Non-Dahalo Flag Actor 2 (Sum)',
}


# Create input widgets for each column with the column name as the description
with st.sidebar:
    with st.form("Weight Sliders"):
        st.title("Indicator Weight Slider")
        # Iterate over Thematic Lists Dictionary
        for key, value in thematic_lists.items():
            st.subheader(key)
            # Sort columns by Alias Name
            for column in sorted(value):
                weights_dict[f'{column}'] = st.slider(
                    # Use the widget_alias_dict to remap the column names. 
                    # label = {v: k for k, v in widget_alias_dict.items()}[column],
                    label = widget_alias_dict[column],
                    help = f'{column}',
                    min_value=0.0,
                    max_value=1.0,
                    value= 0.1,
                    step=0.1
                )                
        # Every form must have a submit button.
        submitted = st.form_submit_button('Update!')        

# Initialize session state
if 'tab1_data' not in st.session_state:
    st.session_state.tab1_data = {'result': None, 'map_html': None, 'timestamp': None}

# Display Unweighted Map and DataFrame
with tab1:
    st.subheader("Unweighted VI")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if the data for Tab 1 is already calculated
    if st.session_state.tab1_data['result'] is None:        
        # Store the data in session state
        st.session_state.tab1_data['result'] = root_df
        st.session_state.tab1_data['map_html'] = map_html
        st.session_state.tab1_data['timestamp'] = timestamp

    with st.container():
        # Display the HTML components
        components.html(st.session_state.tab1_data['map_html'], width=800, height=500, scrolling=True)
        # Display the dataframe
        st.subheader(f"{map_title} Dataframe:")
        st.dataframe(st.session_state.tab1_data['result'].set_index('OBJECTID').drop(columns=['geometry']), width=800)

# # Initialize session state
# if 'tab2_data' not in st.session_state:
#     st.session_state.tab2_data = {'result2': None, 'map_html2': None, 'timestamp2': None}       
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
        # Render the map, dataframe, and piechart on Weighted VI Tab
        with tab2:
            st.subheader(map_title2)
            timestamp2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # # Check if the data for Tab 1 is already calculated
            # if st.session_state.tab2_data['result2'] is None:        
            #     # Store the data in session state
            #     st.sessieon_state.tab2_data['result2'] = weighted_df
            #     st.session_state.tab2_data['map_html2'] = map_html2
            #     st.session_state.tab2_data['timestamp2'] = timestamp2
                
            with st.container():
                components.html(map_html, width=800, height=500, scrolling = True)
                # components.html(st.session_state.tab2_data['map_html2'], width=800, height=500, scrolling = True)
                # download_map(m2, map_title2, timestamp2)
                st.subheader(f"{map_title2} Dataframe:")
                st.dataframe(weighted_df.set_index('OBJECTID').drop(columns=['geometry']), width=800)
                # st.dataframe(st.session_state.tab2_data['result2'].set_index('OBJECTID').drop(columns=['geometry']), width=800)
                # download_dataframe(weighted_df, map_title2, timestamp2)
                st.subheader('Thematic Influence on Weighted Vulnerability Index Pie Chart')
                render_piechart(weighted_df, thematic_lists)
        
        st.toast('The Weighted Vulnerability Index Tab has been updated!', icon="🗺️")

# Initialize session state
if 'tab3_data' not in st.session_state:
    st.session_state.tab3_data = {'experience_builder_url': None}
    
# Display Indicator Explorer Tab
with tab3:
    st.title("Indicator Explorer (ArcGIS)")

    # Check if the data for Tab 3 is already calculated
    if st.session_state.tab3_data['experience_builder_url'] is None:        
        # Store the data in session state
        st.session_state.tab3_data["experience_builder_url"] = experience_builder_url
        
    st.link_button('Click here to open the Indicator Explorer in another window.', experience_builder_url, type="primary")
    components.iframe(st.session_state.tab3_data['experience_builder_url'], width = 1400, height = 800, scrolling = True)
