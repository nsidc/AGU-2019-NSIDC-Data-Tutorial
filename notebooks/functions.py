#----------------------------------------------------------------------
# Functions for AGU tutorial notebooks
#
# In Python a module is just a collection of functions in a file with
# a .py extension.
#
# Functions are defined using:
#
# def function_name(argument1, arguments2,... keyword_arg1=some_variable) 
#     '''A docstring explaining what the function does and what
#        arguments it expectes.
#     '''
#     <commands>
#     return some_value  # Not required unless you need to return a value
#
#----------------------------------------------------------------------

import h5py
from pathlib import Path
import pandas as pd
import numpy as np
import geopandas as gpd
from datetime import datetime, timedelta
import pyproj

def print_cmr_metadata(entry, fields=['dataset_id', 'version_id']):
    '''This is a docstring.

    Prints metadata from query to CMR collections.json

    entry - Metadata entry for a dataset
    fields - list of metdata fields to print
    '''
    print(', '.join([f"{field}: {entry[field]}" for field in fields]))


    
def load_icesat2_as_dataframe(filepath, VARIABLES):
    '''
    Load points from an ICESat-2 granule 'gt<beam>' groups as DataFrame of points. Uses VARIABLES mapping
    to select subset of '/gt<beam>/...' variables  (Assumes these variables share dimensions)
    Arguments:
        filepath to ATL0# granule
    '''
    
    ds = h5py.File(filepath, 'r')

    # Get dataproduct name
    dataproduct = ds.attrs['identifier_product_type'].decode()
    # Convert variable paths to 'Path' objects for easy manipulation
    variables = [Path(v) for v in VARIABLES[dataproduct]]
    # Get set of beams to extract individially as dataframes combining in the end
    beams = {list(v.parents)[-2].name for v in variables}
    
    dfs = []
    for beam in beams:
        data_dict = {}
        beam_variables = [v for v in variables if beam in str(v)]
        for variable in beam_variables:
            # Use variable 'name' as column name. Beam will be specified in 'beam' column
            column = variable.name
            variable = str(variable)
            try:
                values = ds[variable][:]
                # Convert invalid data to np.nan (only for float columns)
                if 'float' in str(values.dtype):
                    if 'valid_min' in ds[variable].attrs:
                        values[values < ds[variable].attrs['valid_min']] = np.nan
                    if 'valid_max' in ds[variable].attrs:
                        values[values > ds[variable].attrs['valid_max']] = np.nan
                    if '_FillValue' in ds[variable].attrs:
                        values[values == ds[variable].attrs['_FillValue']] = np.nan
                    
                data_dict[column] = values
            except KeyError:
                print(f'Variable {variable} not found in {filepath}. Likely an empty granule.')
                raise
                
        df = pd.DataFrame.from_dict(data_dict)
        df['beam'] = beam
        dfs.append(df)
        
    df = pd.concat(dfs, sort=True)
    # Add filename column for book-keeping and reset index
    df['filename'] = Path(filepath).name
    df = df.reset_index(drop=True)
    
    return df



def convert_to_gdf(df):
    '''
    Converts a DataFrame of points with 'longitude' and 'latitude' columns to a
    GeoDataFrame
    '''
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs={'init': 'epsg:4326'},
    )

    return gdf


def convert_delta_time(delta_time):
    '''
    Convert ICESat-2 'delta_time' parameter to UTC datetime
    '''
    EPOCH = datetime(2018, 1, 1, 0, 0, 0)
    
    utc_datetime = EPOCH + timedelta(seconds=delta_time)

    return utc_datetime

def compute_along_track_distance(df, ref_point=None):
    '''
    Calculate along track distance for each point, using 'ref_point' as reference.
    Assumes single homogeneous beam profile.

    Arguments:
        df: DataFrame with icesat-2 data
        ref_point: point to use as reference for distance (defaults to first point in dataframe)

    Returuns:
        distance: series of calculated distances along track
    '''
    geod = pyproj.Geod(ellps='WGS84')
    if ref_point is None:
        ref_point = df.iloc[0][['longitude', 'latitude']]

    def calc_distance(row):
        return geod.line_length(*zip(ref_point, row[['longitude', 'latitude']]))

    distance = df.apply(calc_distance, axis=1)

    return distance