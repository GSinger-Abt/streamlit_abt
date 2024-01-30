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

# This Experience Builder App is hosted on ArcGIS Online (https://usaid.maps.arcgis.com/). 
experience_builder_url = r'https://experience.arcgis.com/experience/7a2860e06a54437091b1cfa05ed389a9'

# The following variables are URL references that will need to be updated if this python script is cloned in another GitHub Repo. 
geojson_path = r'https://github.com/GSinger-Abt/streamlit_abt/raw/main/MadagascarCommunes_VI_Analysis_v3.geojson'
codebook_url = "https://github.com/GSinger-Abt/streamlit_abt/raw/main/20240124_Vulnerability%20Index%20Data%20Dictionary_Revised.xlsx"
instructions_url = "https://raw.githubusercontent.com/GSinger-Abt/streamlit_abt/main/20240124_Readme%201_Final.pdf"
readme_url = "https://raw.githubusercontent.com/GSinger-Abt/streamlit_abt/main/20240124_README%202%20_Final.pdf"
logo_url = r'https://github.com/GSinger-Abt/streamlit_abt/raw/main/StreamlitApp_Logos.jpg'

st.set_page_config(
    page_title='Madagascar - Weighted Index of Need (IoN) Explorer',
    page_icon="🗺️",
    layout="wide",
)
st.title('Madagascar - Weighted Index of Need (IoN) Explorer')
st.subheader("Introduction:")
st.markdown(
    """
The USAID Bureau for Humanitarian Assistance (BHA) seeks to reduce the need for ongoing and future food and nutrition security humanitarian assistance in Madagascar and build resilience among households and communities affected by recurrent shocks. 
This tool allows users to calculate a custom Index of Need using indicators from nine themes relevant as drivers of ongoing humanitarian need, and then use this information to identify and strategically target assistance toward the communes within the country with the highest degree of need.
    
--- 
    """
)
st.subheader("How to use this tool:")
    
st.markdown(
    """
    Below these brief instructions, you will find three tabs: Index Maker, Illustrative Example, and Indicator Explorer. This text provides an overview of how and when to use each tab's functionality.
    
    **Index Maker:**
    
    - Click the “Index Maker” tab below to develop your custom weighted index. First, use the sliders on the left to assign each indicator a weight between 0 and 1. Weights should be tied to the importance of each indicator. Indicators that you have concluded (based on evidence) are the most important contributors to humanitarian need should be weighted closer to 1, and indicators that you have concluded are less important contributors to ongoing humanitarian needs should be weighted closer to 0. Note that this index is designed to be highly flexible. Therefore, there are no restrictions or requirements on the total weight that must be assigned across indicators. For further background on index calculation and weighting methodology, refer to the Full Instructions linked below.
    - For example, if you believe that road density and drought are by far the most important drivers of need, you might choose to weight these indicators as 1.0 or 0.9 and assign relatively lower weights to other indicators. 
    - Once you have assigned weights, click "Update!" on the bottom left under the sliders. In a few moments, your customized map will appear below. Communes with the highest level of need will appear as red and communes with the lowest level of need will appear as blue.
    - If you scroll downward, you can view and download the underlying data including the weights that you have assigned. Using the pie chart, you can also compare the weights that you have assigned by theme to ensure that the relative weights of each topic are aligned with your perception of their importance. 
        
    *Note: The indicators are organized by themes: Conflict, Disaster, Food Security/Crisis, Health Facility Access, Market, Precipitation, Road Density, Stunting, Wealth. For further details on data sources and how the indicators are defined, please see the Data Dictionary linked below.*
    

    **Illustrative Example (Equal Weights):**
    
    - Click the second tab called "Illustrative Example (equal weights)" to view an unweighted version of the index which assigns equal weights to all sixteen indicators. 
    - This can provide a useful comparison for the custom weighted versions you might create.
    

    **Indicator Explorer:**
    - Click the third tab called "Indicator Explorer" if you would like to browse the underlying data used to create the indicators for this index. 
    - To view a data layer, you can click the arrow to the left of the relevant theme to reveal a dropdown menu and then click the checkbox next to the dataset you are interested in. 
    - To understand how to interpret each map layer, see the legend by clicking on the first red button in the top right of the tab with the bulleted list icon.
    
    *Note: The first dataset in the list with a checked box will always appear as the top layer in the map. To view a different layer, uncheck any boxes for other datasets that come earlier in the list.*

    ---
    BHA strongly suggests that applicants read the full instructions provided first in order to fully understand and make use of the geospatial mapping tool.

    ---

    """
    # *Once weights are submitted, you can download html versions of the Weighted map. Please note, you must open these files using a browser (e.g., Chrome. Edge, or FireFox).* 
)

st.link_button("Download Full Instructions (.pdf)", instructions_url, help=None, type='primary')
st.link_button("Download Data Dictionary (.xlsx)", codebook_url, help=None, type='secondary')
st.link_button("Download Read Me for Advanced Users (.pdf)", readme_url, help=None, type='secondary')

@st.cache_data  # 👈 Add the caching decorator
def load_geopandas_df(geojson_path):
    ''' This function loads a geopandas datframe based on a geojson URL.'''
    # Load Dataframe with Initial Index of Need (Default Weights = 0.1)
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
    Stunting_cols = ['ST_SUM',
                     #'USAID_STUNTING'
                    ]
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
    reverse = ['RD_DENSUNREV', 'USAID_PRECIP']
    return(core_columns, columns_to_normalize, reverse, thematic_lists)
    
def create_zscore_index(sdf, weights_dict):
    ''' First, this function loops through the columns to normalize list, calculates a new column based on the z-score, 
    and then multiplies it by the weight. The weight is either the default (0.1) or provided via a weights_dict. If a column
    is also in the reverse list, then the z score is multiplied by -1. After the normalized and weighted columns are created,
    they are summed to create the index of need. Lastly, we calculate the percentile of this index to more readily compare
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
    normalized_df['INDEX_OF_NEED'] = round(normalized_df.filter(like=final_suffix, axis=1).sum(axis=1),4)
    normalized_df['INDEX_OF_NEED_percentile'] = round(normalized_df['INDEX_OF_NEED'].rank(pct=True) * 100)
    result_df = pd.concat([sdf[core_columns], normalized_df], axis=1)
    return result_df

def create_INDEX_OF_NEED(df, weights_dict):
    '''This function creates a new dataframe with the index of need and percentile that has columns sorted for easier viewing.'''
    # Create Weighted Vulnerablity Index
    df = create_zscore_index(df , weights_dict=weights_dict)
    df.set_index(['OBJECTID','ADM3_EN','INDEX_OF_NEED','INDEX_OF_NEED_percentile'], inplace=True)
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
        columns=['ADM3_EN','INDEX_OF_NEED_percentile'],
        # key_on='feature.id',
        key_on='feature.properties.ADM3_EN',
        fill_color='RdYlBu_r',
        fill_opacity=0.7,
        line_opacity=0.5,
        legend_name='Index of Need (Percentile)',
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
          ['ADM3_EN','INDEX_OF_NEED','INDEX_OF_NEED_percentile'], aliases=['Commune', "VI", "VI Percentile"]
                                      ),
        # popup=folium.GeoJsonPopup(
        #     fields = ['ADM3_EN','INDEX_OF_NEED','INDEX_OF_NEED_percentile'] + normalized_cols,
        #     aliases=['Commune', "ION", "ION Percentile"] + normalized_cols,
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
    st.markdown(f'<a href="{data_url}" download="{html_name}" target="_blank">Click to Download Map as an HTML File</a>', unsafe_allow_html=True)

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
#     st.markdown(f'<a download="{filename}" href="data:text/csv;base64,{payload}" target="_blank">Download CSV with updated indicator weights and weighted index of need {timestamp}</a>', unsafe_allow_html=True)  
    
# Setup Streatmlit Tabs
tab2, tab1, tab3 = st.tabs(["Index Maker", "Illustrative Example (equal weights)", "Indicator Explorer"])

# Define core columns and columns to rank with reverse exception
core_columns, columns_to_normalize, reverse, thematic_lists = define_processing_col_groups()

# Load geopandas dataframe 
gdf = load_geopandas_df(geojson_path)
# Create unweighted index of need dataframe
root_df = create_INDEX_OF_NEED(gdf, weights_dict=None)
# Load Map and Map HTML
map_title = 'Unweighted Index of Need'
m1 = render_map(root_df, map_title)
# Display the Folium map using st.components.html
map_html = m1._repr_html_()

# Create a dictionary to store the input widgets
weights_dict = {}
# Set Alias Dict (This Dict is inverted later on)
widget_alias_dict = {
    'USAID_PRECIP': 'Average Cumulative Precipitation per Square Kilometer during 2016 - 2023 Growing Season (Reversed)',
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
    # 'USAID_STUNTING': 'Prevalence of Stunting',
    'RD_DENSUNREV': "Road Density (Reversed)",
    'USAIDWEALTH': 'Relative Wealth Index (Reversed)',
    'CON_DFA1C': 'Violence Against Civilians from Dahalo Attacks',
    'USAID_VAC': 'Violence Against Civilians (Total)',
    # 'IPC_AVC': 'Average IPC Score',
    # 'CON_DFA2C': 'Dahalo Flag Actor 2 (Count); Placeholder',
    # 'CON_NDFAC1': 'Non-Dahalo Flag Actor 1 (Sum)',
    # 'CON_NDFAC2': 'Non-Dahalo Flag Actor 2 (Sum)',
}

# Set Alias Dict (This Dict is inverted later on)
hover_source_dict = {
    'USAID_PRECIP': 'Climate Hazards Group InfraRed Precipitation with Station Data (CHIRPS) Daily via Google Earth Engine (GEE) 2016-2023',
    'USAID_IPC': 'Famine Early Warning Systems Network (FEWS-NET) 2020-2023',
    'USAID_PIF': 'World Food Programme 2022',
    'USAID_WALKING': 'USAID GeoCenter Analysis using data from the Malaria Atlas Project 2019',
    'DIS_CROPDMG': 'Disaster Information Management System (DesInventar) 2004-2023',
    'MK_DIST': 'World Food Programme 2023',
    'MK_VOLA': 'World Food Programme 2018-2023',
    'MK_ANOM': 'World Food Programme 2018-2023',
    'DIS_AFF': 'Disaster Information Management System (DesInventar) 2004-2023',
    'USAID_SD': 'Armed Conflict Location & Event Data (ACLED) Project 2018-2023',
    'ST_SUM': 'Demographic and Health Surveys (DHS) 2021',
    # 'USAID_STUNTING': '',
    'RD_DENSUNREV': 'OpenStreetMap 2023',
    'USAIDWEALTH': 'UC Berkeley Data Intensive Development Lab 2022',
    'CON_DFA1C': 'Armed Conflict Location & Event Data (ACLED) Project 2018-2023',
    'USAID_VAC': 'Armed Conflict Location & Event Data (ACLED) Project 2018-2023',
    # 'IPC_AVC': 'Average IPC Score',
    # 'CON_DFA2C': '',
    # 'CON_NDFAC1': '',
    # 'CON_NDFAC2': '',
}

# Create input widgets for each column with the column name as the description
with st.sidebar:
    with st.form("Weight Sliders"):
        st.title("Indicator Weight Slider")
        # Iterate over Thematic Lists Dictionary
        for key, value in thematic_lists.items():
            st.subheader(key)
            # Sort columns by Alias Name
            for column in sorted(value, key=lambda x: widget_alias_dict [x]):
                weights_dict[f'{column}'] = st.slider(
                    # Use the widget_alias_dict to remap the column names. 
                    label = widget_alias_dict[column],
                    help = f'Variable Name: {column} | Source: {hover_source_dict[column]}',
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
    st.subheader("Illustrative Example (equal weights)")
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
        
    st.markdown("""
    ---
    
    Note: This is not an endorsement of using equal weights for the indicators but is an illustrative example of what a map with equally weighted indicators looks like. To manually adjust the weights for each indicator, please navigate to the Index Maker tab and use the sliders to your left.
    
    --- 
    """
               )

# # Initialize session state
# if 'tab2_data' not in st.session_state:
#     st.session_state.tab2_data = {'result2': None, 'map_html2': None, 'timestamp2': None}       
# Display Weighted Map and DataFrame
with tab2:
    # Re-run .py if submitted and add map to tab2
    if submitted:       
        # Render Weighted Tab
        weighted_df = create_INDEX_OF_NEED(gdf, weights_dict)
        # Load Map and Map HTML
        map_title2 = 'Index Maker'
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
                components.html(map_html2, width=800, height=500, scrolling = True)
                # components.html(st.session_state.tab2_data['map_html2'], width=800, height=500, scrolling = True)
                # download_map(m2, map_title2, timestamp2)
                st.subheader(f"{map_title2} Dataframe:")
                st.dataframe(weighted_df.set_index('OBJECTID').drop(columns=['geometry']), width=800)
                # st.dataframe(st.session_state.tab2_data['result2'].set_index('OBJECTID').drop(columns=['geometry']), width=800)
                # download_dataframe(weighted_df, map_title2, timestamp2)
                st.subheader('Thematic Influence on Weighted Index of Need Pie Chart')
                render_piechart(weighted_df, thematic_lists)
        
        st.toast('The Index Maker Tab has been updated!', icon="🗺️")

# Initialize session state
if 'tab3_data' not in st.session_state:
    st.session_state.tab3_data = {'experience_builder_url': None}
    
# Display Indicator Explorer Tab
with tab3:
    st.title("Indicator Explorer")

    # Check if the data for Tab 3 is already calculated
    if st.session_state.tab3_data['experience_builder_url'] is None:        
        # Store the data in session state
        st.session_state.tab3_data["experience_builder_url"] = experience_builder_url
        
    st.link_button('Click here to open the Indicator Explorer in another window.', experience_builder_url, type="primary")
    components.iframe(st.session_state.tab3_data['experience_builder_url'], width = 1400, height = 800, scrolling = True)
st.markdown(
    """
    *This application was produced as part of a buy-in from USAID/BHA/TPQ/SPADe into the Long-Term Assistance and Services for Research (LASER) project currently in place between USAID/DDI/ITR/R and Purdue University under a cooperative agreement. This project has been executed by Abt Global LLC under a subcontract with Purdue University.*
    """
)
st.image(logo_url, width = 640)
