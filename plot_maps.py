import pandas as pd
import pypsa
#matplotlib inline
import matplotlib.pyplot as plt
import geopandas as gpd
#import numpy as np
import cartopy.crs as ccrs
#import ipynb
import os
from os import walk
import plotly.express as px
import json
import plotly.graph_objs as gobj
import plotly.graph_objects as go





def load_data(mypath1,filenames):
    networks = {}
    planning_horizon = []
    for file in filenames:
        year = file[-7:-3]
        print("Loading year {} ".format(year))
        networks[year] = pypsa.Network(os.path.join(mypath1,file))
        planning_horizon.append(year)
    print("I have done my deed now set me Free, mortal!")
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
    normal = n.copy()
    retro = n.copy()
    if carrier == 'AC':
        normal.lines = n.lines[n.lines.type =="Al/St 240/40 4-bundle 380.0"]
    else: 
        normal.links = n.links[(n.links.carrier == carrier)]
        carrier_retro = carrier + " retrofit"
        retro.links = n.links[(n.links.carrier == carrier_retro)]
        for bus in normal.buses[n.buses.carrier=="AC"].index:
            normal.buses.loc[f"{bus}"+ " "  + carrier[:3].strip(), ["x","y"]] = normal.buses.loc[bus, ["x","y"]]
            retro.buses.loc[f"{bus}"+ " " + carrier[:3].strip(), ["x","y"]] = retro.buses.loc[bus, ["x","y"]]
    return(normal,retro)

countries = gpd.read_file(r'C:Shapefile\shape_nuts2.shp')


mypath = r"C:pyp\2022-05-11_13-30-56\esm_run"
mypath1 = f"{mypath}\postnetworks"
filenames = next(walk(mypath1), (None, None, []))[2]

networks = {}
planning_horizon = []


networks, planning_horizon = load_data(mypath1,filenames)



with open("path_to_GeoJSON _file") as geofile:
    j_file = json.load(geofile)




def plot_grid(normal, retro, carrier):
    """Plots a Geo. Figure in Plotly containing all clusters and a given grid
    Parameters
    ----------
    normal : Dataframe containing Links and Buses for AC and H2/gas grid, should be provided by get_grid_df funktion
    retro : Dataframe containing Links and Buses for retrofitted H2 grid, should be provided by get_grid_df funktion
    carrier : string (== "gas pipeline", "AC", "H2 pipeline")
        carrier (e.g. "gas pipeline", "AC") used to differenciate what grid to plot
    
    Returns
    -------
    Grid plot of a given carrier
    """
    carrier= carrier[:3].strip()          #this part is unnecessary here should be deleted as soon as get_grid_df is modified 
    df = normal.buses[normal.buses.carrier == carrier].copy()
    df['ct'] = df.index.str[:2]
    
    fig = go.Figure(data=go.Choropleth(
        #geojson=j_file,
        featureidkey= 'properties.COUNTRY_ID',
        locationmode='geojson-id', # honestly no idea what this does
        locations=df['ct'],
        z=df['v_nom'], # Placeholder Variable for a later use could be colorcode for powerussage?  
        autocolorscale=False,
        showscale=False,
        hoverinfo = 'text',
        text = df['ct']

    ))

    #Plot grid lines and set width, AC has to be treated specially 
    if carrier == 'AC':

        for i in range(len(normal.lines.s_nom_opt)):
            fig.add_trace(
                go.Scattergeo(
                    locationmode = 'geojson-id',# honestly no idea what this does
                    lon = [df.loc[normal.lines.bus0[i]]['x'].round(3), df.loc[normal.lines.bus1[i]]['x'].round(3)],
                    lat = [df.loc[normal.lines.bus0[i]]['y'].round(3), df.loc[normal.lines.bus1[i]]['y'].round(3)],
                    mode = 'lines',
                    line = dict(width = (normal.lines.s_nom_opt[i])/1e4,color = 'green'),
                    # opacity = float(df_flight_paths['cnt'][i]) / float(df_flight_paths['cnt'].max()),  => Could be used later
                )
            )
    else:

        for i in range(len(normal.links.p_nom_opt)):
            fig.add_trace(
                go.Scattergeo(
                    locationmode = 'geojson-id',# honestly no idea what this does
                    lon = [df.loc[normal.links.bus0[i]]['x'].round(3), df.loc[normal.links.bus1[i]]['x'].round(3)],
                    lat = [df.loc[normal.links.bus0[i]]['y'].round(3), df.loc[normal.links.bus1[i]]['y'].round(3)],
                    mode = 'lines',
                    line = dict(width = (normal.links.p_nom_opt[i])/1e4,color = 'red'),
                    # opacity = float(df_flight_paths['cnt'][i]) / float(df_flight_paths['cnt'].max()),    
                )
            )
        for i in range(len(retro.links.p_nom_opt)):
            fig.add_trace(
                go.Scattergeo(
                    locationmode = 'geojson-id',# honestly no idea what this does
                    lon = [df.loc[retro.links.bus0[i]]['x'].round(3), df.loc[retro.links.bus1[i]]['x'].round(3)],
                    lat = [df.loc[retro.links.bus0[i]]['y'].round(3), df.loc[retro.links.bus1[i]]['y'].round(3)],
                    mode = 'lines',
                    line = dict(width = (retro.links.p_nom_opt[i])/1e4,color = 'blue'),
                    hoverinfo = 'text',
                    text = retro.links.p_nom_opt[i].round(0),
                    # opacity = float(df_flight_paths['cnt'][i]) / float(df_flight_paths['cnt'].max()),
                )
            )

    #centralize on europe
    fig.update_geos(
        visible=False, resolution=50, scope="europe",
        showcountries=True, countrycolor="Black",
        #showsubunits=True, subunitcolor="Blue"
    )


    #Scale Figure 
    fig.update_layout(
        autosize=False,
        width=1000,
        height=1000,
        showlegend = False,
    )

    return(fig)




from dash import Dash, dcc, Output, Input  # pip install dash
import dash_bootstrap_components as dbc    # pip install dash-bootstrap-components
import plotly.express as px

# incorporate data into app
#df = px.data.medals_long()

# Build your components
app = Dash(__name__, external_stylesheets=[dbc.themes.SOLAR])
mytitle = dcc.Markdown(children='# App that plots a Map')
mygraph = dcc.Graph(figure={})
dropdown = dcc.Dropdown(options=['H2 pipeline', 'gas pipeline', "AC"],
                        value='H2 pipeline',  # initial value displayed when page first loads
                        clearable=False)

# Customize your own Layout
app.layout = dbc.Container([mytitle, dropdown, mygraph])

# Callback allows components to interact
@app.callback(
    Output(mygraph, component_property='figure'),
    Input(dropdown, component_property='value')
)
def update_graph(user_input):  # function arguments come from the component property of the Input
    carrier = user_input
    n = networks['2050']
    normal,retro = get_grid_df(n,carrier)
    fig = plot_grid(normal, retro, carrier)
    return fig  # returned objects are assigned to the component property of the Output



# Run app
if __name__=='__main__':
    app.run_server(port=8043)
