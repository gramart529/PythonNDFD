#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 18:44:37 2020

@author: gray
"""

#%% Imports
import os
import re
from urllib.request import urlopen, urlretrieve, urlcleanup

import xarray as xr
import cfgrib
import pandas as pd
import numpy as np

#%% Setup
#%%% Server Access
# These variables allow us to assemble a URL to access specific variables from
# the NDFD database. 
NDFD_SERVER = "http://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/"
NDFD_AREA = "AR.{}/"       # NDFD Area of Data
NDFD_TRNG = "VP.{}/"       # NDFD Valid Period (Forecast Time Range)
NDFD_VAR = "ds.{}.bin"     # NDFD Variable

#%%% Local Directories
DATA = "data/"

#%% Data Loading
def getNDFDlist(listof, area=None, timerange=None, ndfd_server=NDFD_SERVER):
    """
    Description: Returns a list of available NDFD parameters
    Parameters:
        listof (str): Either "areas", "timeranges", or "vars"
        area (str): Needed if listof="timeranges" or "vars"
        timerange (str): Needed if listof="vars"
        ndfd_server (str): URL to NDFD server with files 
    Returns:
        lines (list): List of extracted parameters
    """
    if listof == "areas":
        regex = r"(?<=a href=\"AR\.).*(?=\/\">)"
    elif listof == "timeranges":
        ndfd_server += NDFD_AREA.format(area)
        regex = r"(?<=a href=\"VP\.)\d\d\d\-\d\d\d(?=\/)"
    elif listof == "vars":
        ndfd_server += NDFD_AREA.format(area) + NDFD_TRNG.format(timerange)
        regex = r"(?<=a href=\"ds\.).*(?=\.bin\")"
    with urlopen(ndfd_server) as file:
        lines = file.readlines()
    lines = [line.decode("utf-8") for line in lines]
    lines = "\n".join(lines)
    lines = re.findall(regex, lines)
    urlcleanup()
    return lines

def getVariablePath(area, timerange, var):
    """
    Description: Assembles a directory and path for a specific NDFD variable 
    Parameters:
        area (str): Data area
        timerange (str): Forecast range (001-003, 004-007, or 008-450)
        var (str): Variable to access
    Returns:
        filepath (str): Path to local file with variable
    """
    area_url = NDFD_AREA.format(area)
    timerange_url = NDFD_TRNG.format(timerange)
    filedir = DATA + area_url + timerange_url
    filepath = filedir + var + ".bin"
    return filedir, filepath

def getVariable(area, timerange, var):
    """
    Description: Saves an NDFD variable to a local file
    Parameters:
        area (str): Data area
        timerange (str): Forecast range (001-003, 004-007, or 008-450)
        var (str): Variable to access
    Returns:
        filepath (str): Path to local file with variable
    """
    area_url = NDFD_AREA.format(area)
    timerange_url = NDFD_TRNG.format(timerange)
    var_url = NDFD_VAR.format(var)
    remote_url = NDFD_SERVER + area_url + timerange_url + var_url
    
    filedir, filepath = getVariablePath(area, timerange, var)
    os.makedirs(filedir, exist_ok=True)
    
    filename, _ = urlretrieve(remote_url, filename=filepath)
    urlcleanup()
    return filename

def getVariables(area_list, timerange_list, var_list):
    """
    Description: Saves a list of NDFD variables 
    Parameters:
        area (str list): Data area
        timerange (str list): Forecast range (001-003, 004-007, or 008-450)
        var (str list): Variable to access
    Returns:
        filepaths (list): Path to local file with variable
    """
    filepaths = []
    for area in area_list:
        for timerange in timerange_list:
            for var in var_list:
                filepath = getVariable(area, timerange, var)
                filepaths.append(filepath)
    return filepaths

def loadVariable(area, timerange, var):
    """
    Description: Loads an NDFD variable into the workspace as an xarray 
    Parameters:
        area (str): Data area
        timerange (str): Forecast range (001-003, 004-007, or 008-450)
        var (str): Variable to access
    Returns:
        ndfd_variable_xr (xarray): An xarray dataset
        ndfd_variable_pd (pandas): A pandas dataframe
    """
    filedir, filepath = getVariablePath(area, timerange, var)
    if not os.path.exists(filepath):
        getVariable(area, timerange, var)
    ndfd_variable_xr = xr.open_dataset(filepath, engine="cfgrib")
    ndfd_variable_pd = ndfd_variable_xr.to_dataframe()
    return ndfd_variable_xr, ndfd_variable_pd

ndfd_areas = getNDFDlist("areas")
ndfd_seast_sky_xr, ndfd_seast_sky_pd = loadVariable("seast", "001-003", "sky")
