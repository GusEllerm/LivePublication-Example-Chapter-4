import rasterio
import numpy as np
import pickle
import logging
import pathlib
logging.getLogger().setLevel(logging.INFO)

logging.info("File handling module loaded")
logging.info(f"Current working directory: {pathlib.Path.cwd()}")

def write_band_to_file(band_name, band_array, band_link):    
    # extract the band profile
    profile = rasterio.open(band_link).profile
    # Write the profile and array to disk
    with open(band_name + '.pickle', 'wb') as dst:
        pickle.dump([band_name, band_array, profile], dst, protocol=pickle.HIGHEST_PROTOCOL)

def write_index_to_file(index_name, index_array, profile):
    # Write index name, array and profile to disk
    logging.info(f'Writing index {index_name} to file')
    with open(index_name + '.pickle', 'wb') as dst:
        pickle.dump([index_name, index_array, profile], dst, protocol=pickle.HIGHEST_PROTOCOL)

def read_band_from_file(band):
    # Read the pickle file
    with open(band, 'rb') as inp:
        band_info = pickle.load(inp)
    return band_info