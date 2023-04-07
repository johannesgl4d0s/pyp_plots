# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
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

from tool_box import get_grid_df, load_data, get_map_object, plot_grid, export_fig_to_json, export_fig_to_png,export_fig_to_html
logging.basicConfig( format = "%(asctime)s - %(message)s")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# =============================================================================
# mypath = r"C:\Users\johannes.misensky\OneDrive - AGGM\Dokumente\ESM_Aus\postnetworks\test_3"
# export_path = r"C:\Users\johannes.misensky\OneDrive - AGGM\Dokumente\ESM_Aus\eval_auto_test"
# 
# =============================================================================


def main(mypath,export_path):
    """plots several maps as json and pngs as well as 3 filter jsons
    Parameters
    ----------
    mypath : string - path to the postnetworks (=="\ESM_Aus\postnetworks\test_3")
    export_path : string - path where the generated json and png should be saved (=="\ESM_Aus\eval_auto_test")
        
    Returns
    -------
    json and pngs as well as 3 filter jsons
    """
    #path to shapefiles
    fp = r'C:\Users\johannes.misensky\OneDrive - AGGM\Dokumente\ESM_Aus\shapefile'
    map_df = get_map_object(fp)
    mypath1 = f"{mypath}"
    filenames = next(walk(mypath1), (None, None, []))[2]
    # get network objects
    networks = {}
    planning_horizon = []
    filenames

    networks, planning_horizon = load_data(mypath1,filenames)
    dropdown_year = ['2020','2030','2040','2050']
    carrier = ["gas pipeline", "AC", "H2 pipeline"]
    
    # Quick and dirty solution to change to carriers to the naming convention of LearnConsult
    d = {"gas pipeline":"MethaneTransmission",
         "AC":"PowerTransmission",
         "H2 pipeline":"HydrogenTransmission",
         "europe":"EU"}
    #this solution should be optimised in the futur
    radio = "europe"
    for c in carrier:
        
        for year in dropdown_year:
            n = networks[year]
            normal,retro,dc = get_grid_df(n,c)
            fig = plot_grid(normal, retro, dc, c, year, radio, map_df)
            export_fig_to_json(figure_name=d[c], year = year, region=d[radio], figure=fig,scenario_path= export_path)
            logging.info("Saving {} of region {} for year {} as json".format(c,radio,year))
            export_fig_to_html(figure_name=d[c], year = year, region=d[radio], figure=fig,scenario_path= export_path)
            logging.info("Saving {} of region {} for year {} as html".format(c,radio,year))
            export_fig_to_png(figure_name=d[c], year = year, region=d[radio], figure=fig,scenario_path= export_path)
            logging.info("Saving {} of region {} for year {} as png".format(c,radio,year))
    radio = "AT"
    for c in carrier:
        
        for year in dropdown_year:
            n = networks[year]
            normal,retro,dc = get_grid_df(n,c)
            fig = plot_grid(normal, retro, dc, c, year, radio, map_df)
            export_fig_to_json(figure_name=d[c], year = year, region=radio, figure=fig,scenario_path= export_path)
            logging.info("Saving {} of region {} for year {} as json".format(c,radio,year))
            export_fig_to_html(figure_name=d[c], year = year, region=radio, figure=fig,scenario_path= export_path)
            logging.info("Saving {} of region {} for year {} as html".format(c,radio,year))
            export_fig_to_png(figure_name=d[c], year = year, region=radio, figure=fig,scenario_path= export_path)
            logging.info("Saving {} of region {} for year {} as png".format(c,radio,year))

   
if __name__  == "__plot_map__":
    main(mypath, export_path)
#%%
# =============================================================================
# mypath = r"C:\Users\johannes.misensky\OneDrive - AGGM\Dokumente\ESM_Aus\postnetworks\test_3"
# export_path = r"C:\Users\johannes.misensky\OneDrive - AGGM\Dokumente\ESM_Aus\eval_auto_test"
# #path to shapefiles
# fp = r'C:\Users\johannes.misensky\OneDrive - AGGM\Dokumente\ESM_Aus\shapefile'
# map_df = get_map_object(fp)
# mypath1 = f"{mypath}"
# filenames = next(walk(mypath1), (None, None, []))[2]
# # get network objects
# networks = {}
# planning_horizon = []
# filenames
# 
# networks, planning_horizon = load_data(mypath1,filenames)
# dropdown_year = ['2020','2030','2040','2050']
# carrier = ["gas pipeline", "AC", "H2 pipeline"]
# 
# # Quick and dirty solution to change to carriers to the naming convention of LearnConsult
# d = {"gas pipeline":"MethaneTransmission",
#      "AC":"PowerTransmission",
#      "H2 pipeline":"HydrogenTransmission",
#      "europe":"EU"}
# #this solution should be optimised in the futur
# radio = "europe"
# for c in carrier:
#     
#     for year in dropdown_year:
#         n = networks[year]
#         normal,retro,dc = get_grid_df(n,c)
#         fig = plot_grid(normal, retro, dc, c, year, radio, map_df)
#         
#         export_fig_to_html(figure_name=d[c], year = year, region=d[radio], figure=fig,scenario_path= export_path)
#         logging.info("Saving {} of region {} for year {} as html".format(c,radio,year))
# =============================================================================
        