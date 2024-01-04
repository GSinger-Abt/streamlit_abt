# Vulnerability Index Application: README
This publication was produced as part of the LASER PULSE program, led by Purdue University and funded by the United States Agency for International Development (USAID). The views expressed in this publication do not necessarily reflect the views of USAID or the United States Government.

The USAID Bureau for Humanitarian Assistance (BHA) seeks to reduce the need for ongoing and future food and nutrition security humanitarian assistance in Madagascar and build resilience among households and communities vulnerable to recurrent shocks. The Vulnerability Index Application allows users to calculate a Vulnerability Index using indicators from nine domains: Conflict, Disaster, Food Security/Crisis, Stunting, Market, Precipitation, Wealth, Road Density, Health Facility Access.

#### Vulnerability Index
Vulnerability can be assessed by relying on data about the potential sources of shocks. However not all areas face the same risks. For instance, in a more rural area, access to roads may play a larger role in vulnerability than in a more urban area. As such, a vulnerability index should permit flexibility in weighting the inputs to the index. 

This application provides users the ability to calculate a vulnerability index for communes in four regions of Madagascar (Androy, Anosy, Atsimo Andrefana, and Atsimo Atsinanana) by calculating the z-score of the variables and using the following formula: 

Vulnerability Index = z(Conflict Variables) + z(Food Security Variables) + z(Market Variables) + z(Wealth Index) + z(Health Facility Access) + z(Disaster Variables) + z(Stunting Variables) + z(Precipitation Variable) + z(Road Density)

#### Indicators used in Vulnerability Index Calculation
| Theme                  | Indicator                                                  |
| ---------------------- | ---------------------------------------------------------- |
| Conflict               | Violence Against Civilians from Dahalo Attacks               |
|                        | Violence Against Civilians Total                            |
| Disaster               | Number of People Affected by Natural Disaster
|                        | Hectares of Crops Damaged by Natural Disaster              |            
| Food Security/Crisis   | Average IPC Scores from 2020 – 2023                          |
|                        | Average Prevalence of Insufficient Food Consumption         |
| Market                 | Distance to Nearest Market                                  |
|                        | Market Price Volatility Score                               |
|                        | Market Pricing Anomaly Score                                |
| Stunting               | Percent Children Stunted                                    |
|                        | Prevalence of Stunting                                       |
| Health Facility Access | Average Walking Travel Time to Nearest Healthcare Facility  |
| Precipitation          | Average Cumulative Precipitation per Sq. KM during 2016-2023 growing season |
| Road Density           | KM of Road per Commune Sq Km area (Reversed)                |
| Wealth                 | Relative Wealth Index (Reversed)                            |

This application provides users the ability to calculate a vulnerability index for communes in four regions of Madagascar (Androy, Anosy, Atsimo Andrefana, and Atsimo Atsinanana). The resulting index is a weighted index that is derived by summing together the weighted z-scores of each indicator.

'Vulnerability Index = 
    (wconflict var 1 * z(Conflict Variable 1)) + … + (wconflict var n * z(Conflict Variable n))
    + (wfood security var 1 * z(Food Security Variable 1)) + … + (wfood security var n * z(Food Security Variable n))
    + (wmarket var 1 * z(Market Variable 1)) + … + (wmarket var n * z(Market Variable n))
    + (wstunting var 1 * z(Stunting Variable 1)) + … + (wstunting var n * z(Stunting Variable n))
    + (wdisaster var 1 * z(Disaster Variable 1)) + … + (wdisaster var n * z(Disaster Variable n))
    + (wwealth var * z(Wealth Index))
    + (wprecipitation var * z(Precipitation Variable))
    + (whealth facility access var * z(Health Facility Access))
    + (wroad density var * z(Road Density))
'

#### Application Interface

The application has three tabs: **Weighted VI, Unweighted VI, Indicator Explorer (ArcGIS)**

- **Weighted VI Calculates**: Calculates the vulnerability index using custom weights. To populate this tab, the user must submit the form on the left.
- **Unweighted VI Calculates**: Calculates the vulnerability index using equal weights across all variables.
- **Indicator Explorer (ArcGIS)**: Displays a map of the indicators without a vulnerability index calculation.

![Figure 1.png](https://raw.githubusercontent.com/GSinger-Abt/streamlit_abt/main/Figure%201.png)
Figure 1: Screenshot of application when first opened.

#### Weighted VI
_Calculating a Weighted Vulnerability Index_
1)	For each indicator listed in the left pane, move the slider to assign the desired weight and click the **UPDATE** button at the bottom of the list of indicators to generate a map using the weights.
2) The app will calculate the vulnerability index (it may take up to 30 seconds) and return a map and a table showing a map, a table and a pie chart.

![Figure 2.png](https://raw.githubusercontent.com/GSinger-Abt/streamlit_abt/main/Figure%202.png)
Figure 2 - Resulting map and table after assigning weights

3)	The map and table can be downloaded using the links underneath each one. (Note: the application will refresh the screen after a period of time which will erase the map and table)
4)	The pie chart shows the influence of each domain on the vulnerability index. 

#### Unweighted VI
The Unweighted VI tab calculates the vulnerability index using equal weights for all indicators
1)	Clicking on the Unweighted VI tab displays a map and a table of vulnerability index calculated by assigning a weight of one to all indicators.
NOTE: The Indicator Weight Slider will still appear on the left of the screen but it will not affect the calculation of the unweighted index.

![Figure 3.png](https://raw.githubusercontent.com/GSinger-Abt/streamlit_abt/main/Figure%203.png)
Figure 3 – Screenshot of Un-Weighted Vulnerability Index map and table
 
#### Indicator Explorer (ArcGIS)
The indicator explorer provides the ability to produce maps of each individual indicator. It also allows users to add additional data to the map.

##### Displaying layers
Clicking on the check box next to the layer will display it on the map.

![Figure 4.png](https://raw.githubusercontent.com/GSinger-Abt/streamlit_abt/main/Figure%204.png)
Figure 4 – Screenshot of Indicator Explorer
 
Note: If turning on multiple layers, only the topmost layer is visible.


##### Adding data 
It is possible to add additional data to the indicator map using the Add Data button ![image](https://github.com/GSinger-Abt/streamlit_abt/assets/151070704/6999fcc0-8beb-4505-853a-f2d04814da03) in the upper right of the window.

![image](https://github.com/GSinger-Abt/streamlit_abt/assets/151070704/dba0cbed-919d-494e-8b8a-a72be8993768)

Figure 5 – Add data pane on Indicator Explorer page


In the resulting window click on the button labeled “Click to add data” to display a pop-up window to search for available data on ArcGIS online, a url or a file on the local machine. Any data added will be only available during the current session.

Once a layer has been selected, it appears in the list of layers on the left of the ArcGIS map screen.
 

