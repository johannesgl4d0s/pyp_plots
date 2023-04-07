# -*- coding: utf-8 -*-
"""
Created on Wed Apr  5 11:03:42 2023

@author: johannes.misensky
"""
import pandas as pd
import pypsa
#%matplotlib inline
import matplotlib.pyplot as plt
import geopandas as gpd
import numpy as np
import cartopy.crs as ccrs
# import ipynb
import os
from os import walk
import plotly.express as px
import json
import plotly.graph_objs as gobj
import plotly.graph_objects as go
import pyproj
import logging
from dash import Dash, dcc, Output, Input  # pip install dash
import dash_bootstrap_components as dbc    # pip install dash-bootstrap-components


#%%
logging.basicConfig( format = "%(asctime)s - %(message)s")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def load_data(mypath1,filenames):
    networks = {}
    planning_horizon = []
    for file in filenames:
        year = file[-7:-3]
        logging.info("Loading year {} ".format(year))
        networks[year] = pypsa.Network(os.path.join(mypath1,file))
        planning_horizon.append(year)
    logging.info("Done!")
    return(networks, planning_horizon)

def get_grid_df(n,carrier):
    """Gets all capacity dataframes for the grid
    Parameters
    ----------
    n : Networks
    carrier : string (== "gas pipeline", "AC", "H2 pipeline")
        carrier (e.g. "gas pipeline", "DC") used in lines and links for transporting a specific energy
    
    Returns
    -------
    two dataframes:
    normal = classic grid, including newly build H2 grid
    retro only used for H2 retrofitted piplines.
    """
    # CODEREVIEW: Is there a leaner way to implement this? Once networks get to a higher time-resolution, this can become really slow and make the 
    # dashboard hard to navigate. Maybe we can discuss options to optimize performance in a seperate Task -> Backlog Item
    normal = n.copy()
    retro = n.copy()
    dc = n.copy()
    if carrier == 'AC':
        # CODEREVIEW: Why is this filter for line-types necessary? All AC-lines and only AC-lines are here: n.lines
        normal.lines = n.lines[n.lines.type =="Al/St 240/40 4-bundle 380.0"]
        dc.links = n.links[n.links.carrier == "DC"]
        # CODEREVIEW: Why is this necessary? normal.buses and dc.buses are the same objects at this point (because of copy())
        # Comment for optimizing code: It is faster to use i.e. pd.Series than loops
        for bus in normal.buses[n.buses.carrier=="AC"].index:
            dc.buses.loc[f"{bus}", ["x","y"]] = normal.buses.loc[bus, ["x","y"]]
    else: 
        normal.links = n.links[(n.links.carrier == carrier)]
        carrier_retro = carrier + " retrofit"
        retro.links = n.links[(n.links.carrier == carrier_retro)]
        for bus in normal.buses[n.buses.carrier=="AC"].index:
            normal.buses.loc[f"{bus}"+ " "  + carrier[:3].strip(), ["x","y"]] = normal.buses.loc[bus, ["x","y"]]
            retro.buses.loc[f"{bus}"+ " " + carrier[:3].strip(), ["x","y"]] = retro.buses.loc[bus, ["x","y"]]
    return(normal,retro,dc)


def get_map_object(fp):
    """loads a shapefile, simplifies it and transforms it into a, for plotly, usable format
    Parameters
    ----------
    # CODEREVIEW: filepath may be different in deployed version
    fp : string (i.e. ".\shape_nuts2.shx")
        fp defines a shapefile location in unicode
    
    Returns
    -------
    geopandas.geodataframe.GeoDataFrame
    """
    #read in file
    map_df = gpd.read_file(fp)
    #Returns a GeoSeries containing a simplified representation of each geometry
    map_df["geometry"] = (
        map_df.to_crs(map_df.estimate_utm_crs()).simplify(1000).to_crs(map_df.crs)
    )
    #transform to readable geo-df
    map_df.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
    # Change CountryID for AT (and DE if need) 
    for country in range(len(map_df.COUNTRY_ID)):
        if map_df.COUNTRY_ID[country] in ['AT', 'DE']:
            map_df.COUNTRY_ID[country]= map_df.COUNTRY_ID[country] + '_' + str(map_df.id[country])
    return(map_df)


def plot_grid(normal, retro, dc, carrier, year, button, map_df):
    """Plots a Geo. Figure in Plotly containing all clusters and a given grid
    Parameters
    ----------
    normal : Dataframe containing Links and Buses for AC and H2/gas grid, should be provided by get_grid_df function
    retro : Dataframe containing Links and Buses for retrofitted H2 grid, should be provided by get_grid_df function
    carrier : string (== "gas pipeline", "AC", "H2 pipeline")
        carrier (e.g. "gas pipeline", "AC") used to differenciate what grid to plot
    
    Returns
    -------
    Grid plot of a given carrier
    """
    # Variable to divde Capacity and therefore line thickness. 
    divisor = 1e3
    
    #plot a choropleth map
    fig = px.choropleth(map_df, geojson=map_df.geometry, 
                    locations=map_df.index, color =map_df.index ,  
                    height=500, 
                    # Colorscale atm set to one color
                    color_continuous_scale=[[0, 'rgb(229,236,246)'],
                      [0.05, 'rgb(229,236,246)'],
                      [0.1, 'rgb(229,236,246)'],
                      [0.20, 'rgb(229,236,246)'],
                      [1, 'rgb(229,236,246)']],
                    hover_name =  list(map_df.COUNTRY_ID) )

    # Formate hover_name to only show the Country ID = Cluster name
    fig.update_traces(customdata= np.stack(map_df.COUNTRY_ID, axis=0),
        hovertemplate = '<b>%{customdata}</b>' )

    #Plot grid lines and set width, AC has to be treated specially 
    if carrier == 'AC':

        for i in range(len(normal.lines.s_nom_opt)):
            fig.add_trace(
                go.Scattergeo(
                    lon = [normal.buses.loc[normal.lines.bus0[i]]['x'].round(3), normal.buses.loc[normal.lines.bus1[i]]['x'].round(3)],
                    lat = [normal.buses.loc[normal.lines.bus0[i]]['y'].round(3), normal.buses.loc[normal.lines.bus1[i]]['y'].round(3)],
                    mode = 'lines',
                    line = dict(width = (normal.lines.s_nom_opt[i] * normal.lines.s_max_pu[i])/divisor,color = 'green'), #s_nom_opt nur Termische Kap = s_nom_opt * s_max_pu für net
                    hoverinfo = 'none',
                    name="{} GW AC-Grid".format(int(round((normal.lines.s_nom_opt[i] * normal.lines.s_max_pu[i])/divisor))) 
                )
            )
            fig.add_trace(go.Scattergeo(
                lon =[0.5*(normal.buses.loc[normal.lines.bus0[i]]['x'].round(3)+normal.buses.loc[normal.lines.bus1[i]]['x'].round(3))+0.1], 
                lat = [0.5*(normal.buses.loc[normal.lines.bus0[i]]['y'].round(3)+normal.buses.loc[normal.lines.bus1[i]]['y'].round(3))+0.1], 
                mode='text', 
                hoverinfo = 'none',
                text=(normal.lines.s_nom_opt[i] * normal.lines.s_max_pu[i]/divisor).round(2)))
        for i in range(len(dc.links.p_nom_opt)):
            fig.add_trace(
                go.Scattergeo(
                    lon = [normal.buses.loc[normal.links.bus0[i]]['x'].round(3), normal.buses.loc[normal.links.bus1[i]]['x'].round(3)],
                    lat = [normal.buses.loc[normal.links.bus0[i]]['y'].round(3), normal.buses.loc[normal.links.bus1[i]]['y'].round(3)],
                    mode = 'lines',
                    line = dict(width = (dc.links.p_nom_opt[i])/divisor,color = 'red'),
                    hoverinfo = 'none',
                    opacity = 0.5,
                    name="{} GW DC-Grid".format(int(round(dc.links.p_nom_opt[i]/divisor)))
                )
            )
            if (dc.links.p_nom_opt[i]/divisor) >=0.1:
                fig.add_trace(go.Scattergeo(
                        lon =[0.5*(normal.buses.loc[normal.links.bus0[i]]['x'].round(3)+normal.buses.loc[normal.links.bus1[i]]['x'].round(3))], 
                        lat = [0.5*(normal.buses.loc[normal.links.bus0[i]]['y'].round(3)+normal.buses.loc[normal.links.bus1[i]]['y'].round(3))], 
                        mode='text',
                        hoverinfo = 'none',
                        text=(dc.links.p_nom_opt[i]/divisor).round(2), 
                        textfont=dict(color = 'red')),
                      )
    

    else:

        for i in range(len(normal.links.p_nom_opt)):
            fig.add_trace(
                go.Scattergeo(
                    lon = [normal.buses.loc[normal.links.bus0[i]]['x'].round(3), normal.buses.loc[normal.links.bus1[i]]['x'].round(3)],
                    lat = [normal.buses.loc[normal.links.bus0[i]]['y'].round(3), normal.buses.loc[normal.links.bus1[i]]['y'].round(3)],
                    mode = 'lines',
                    line = dict(width = (normal.links.p_nom_opt[i])/divisor,color = 'red'),
                    hoverinfo = 'none',
                    name="{} GW Pipeline".format(int(round(normal.links.p_nom_opt[i]/divisor)))

                )
            )
            if (normal.links.p_nom_opt[i]/divisor) >=0.01:
                fig.add_trace(go.Scattergeo(
                        lon =[0.5*(normal.buses.loc[normal.links.bus0[i]]['x'].round(3)+normal.buses.loc[normal.links.bus1[i]]['x'].round(3))+0.1],
                        lat = [0.5*(normal.buses.loc[normal.links.bus0[i]]['y'].round(3)+normal.buses.loc[normal.links.bus1[i]]['y'].round(3))+0.1],
                        mode='text',
                        hoverinfo = 'none',
                        text=(normal.links.p_nom_opt[i]/divisor).round(2), 
                        textfont=dict(color = 'black')),
                      )
        for i in range(len(retro.links.p_nom_opt)):
            fig.add_trace(
                go.Scattergeo(
                    lon = [normal.buses.loc[retro.links.bus0[i]]['x'].round(3), normal.buses.loc[retro.links.bus1[i]]['x'].round(3)],
                    lat = [normal.buses.loc[retro.links.bus0[i]]['y'].round(3), normal.buses.loc[retro.links.bus1[i]]['y'].round(3)],
                    mode = 'lines',
                    line = dict(width = (retro.links.p_nom_opt[i])/divisor,color = 'blue'),
                    hoverinfo = 'none',
                    name="{} GW retrofitted Pipeline".format(int(round(retro.links.p_nom_opt[i]/divisor)))
                )
            )
            if (retro.links.p_nom_opt[i]/divisor) >=0.01:
                fig.add_trace(go.Scattergeo(
                lon =[0.5*(normal.buses.loc[retro.links.bus0[i]]['x'].round(3)+normal.buses.loc[retro.links.bus1[i]]['x'].round(3))], 
                lat = [0.5*(normal.buses.loc[retro.links.bus0[i]]['y'].round(3)+normal.buses.loc[retro.links.bus1[i]]['y'].round(3))], 
                mode='text',
                hoverinfo = 'none',
                text=(retro.links.p_nom_opt[i]/divisor).round(2), 
                textfont=dict(color = 'lightblue'))
              )

    #centralize on europe

    if button == 'europe':
        fig.update_geos(
            visible=False, resolution=50, 
            scope="europe",
            showcountries=True, countrycolor="Black",
        )
    else:
        #zoom to AT
        fig.update_geos(
            visible=False, resolution=50, 
            scope="europe",
            #center around AT
            center=dict(lon=11, lat=40), 
            projection_rotation=dict(lon=30.5, lat=30.5, roll=30.5),  
            lataxis_range=[10,11], lonaxis_range=[33,41],
            showcountries=True, countrycolor="Black"
        )
    d = {"gas pipeline":"Methane Transmission",
         "AC":"Power Transmission",
         "H2 pipeline":"Hydrogen Transmission",
         "europe":"EU"}

    #Scale Figure 
    fig.update_layout(
        title=f"{d[carrier]} Grid Capacity in {year}",
        autosize=False,
        width=1000,
        height=1000,
        coloraxis_showscale=False,

    )

    #the following part is only for legend customizing

    #create empty list to store legend labels
    labels_to_show_in_legend = []

    #as far as i understand plotly needs a geoobject to exist in the plot to be filtered in legend 
    #therefor find the closest existing Capacity to 3 and 10 GW and store them in List
    for s in (10,3):
        if carrier == 'AC':
            a = int(round(min(dc.links.p_nom_opt/divisor, key=lambda x:abs(x-s))))
            labels_to_show_in_legend.append("{} GW DC-Grid".format(a))
            b = int(round(min((normal.lines.s_nom_opt * normal.lines.s_max_pu)/divisor, key=lambda x:abs(x-s))))
            labels_to_show_in_legend.append("{} GW AC-Grid".format(b))
        elif carrier == 'gas pipeline':
            c = int(round(min(normal.links.p_nom_opt/divisor, key=lambda x:abs(x-s))))
            labels_to_show_in_legend.append("{} GW Pipeline".format(c))
        else:
            c = int(round(min(normal.links.p_nom_opt/divisor, key=lambda x:abs(x-s))))
            labels_to_show_in_legend.append("{} GW Pipeline".format(c))
            d = int(round(min(retro.links.p_nom_opt/divisor, key=lambda x:abs(x-s))))
            labels_to_show_in_legend.append("{} GW retrofitted Pipeline".format(d))

    #create empty set
    labels = set()

    #check if trace name is not in set and in list, if true enable showlegend and store in set
    for trace in fig['data']: 
        if ( not trace['name'] in labels) and (trace['name'] in labels_to_show_in_legend):
            labels.add(trace['name'])
            trace['showlegend'] = True
            #print(trace['name'])   #enable print for troubleshooting
        else:
            trace['showlegend'] = False


    return(fig)


def export_fig_to_json(figure_name, year, region, figure, scenario_path):
    
    jsonstr = figure.to_json(True, True, True, None)
    
    if not os.path.exists(f"{scenario_path}\JSONs_LC"):
        os.makedirs(f"{scenario_path}\JSONs_LC")
        
    f = open(f"{scenario_path}\JSONs_LC\{figure_name}_{year}_{region}.json", "w")
    f.write(jsonstr)
    f.close 
    
def export_fig_to_png(figure_name, year, region, figure, scenario_path):
    
    if not os.path.exists(f"{scenario_path}\Graphs"):
        os.makedirs(f"{scenario_path}\Graphs")

    figure.write_image(f"{scenario_path}\Graphs\{figure_name}_{year}_{region}.png")
    
def export_fig_to_html(figure_name, year, region, figure, scenario_path):
    
    if not os.path.exists(f"{scenario_path}\Graphs"):
        os.makedirs(f"{scenario_path}\Graphs")

    # Ordneraddresse festlegen
    figure.write_html(f"{scenario_path}\Graphs\{figure_name}_{year}_{region}.html")
    
    #%%

# =============================================================================
# def export_filters_to_json(figure_name, available_years, available_regions, scenario_path):
# 
#     help_string = "{year}_{region}"
#     name_dict = {"naming_convention": f"{figure_name}_{help_string}.json"}
#     
#     filter_dict = {"Years": available_years, "Regions": available_regions}
#     
#     rename_local_regions_dict, rename_all_regions_dict = get_rename_region_dict()
#     nice_region_names_dict = rename_all_regions_dict
#     
#     list_of_dicts = [name_dict, filter_dict, nice_region_names_dict]
#     
#     if not os.path.exists(f"{scenario_path}\JSONs_LC"):
#         os.makedirs(f"{scenario_path}\JSONs_LC")
#         
#     with open(f"{scenario_path}\JSONs_LC\{figure_name}_FILTERS.json", "w") as outfile:
#         json.dump(list_of_dicts, outfile, indent = 3)
# =============================================================================