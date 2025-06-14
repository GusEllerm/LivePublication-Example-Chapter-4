import argparse
import logging
import numpy as np
import pathlib
import rasterio
from cmath import sqrt
from file_handling import *

# Turn on logging 
logging.getLogger().setLevel(logging.INFO)

# Suppress divide by zero warning
np.seterr(invalid='ignore')

logging.info("index_def module loaded")
logging.info(f"Current working directory: {pathlib.Path.cwd()}")

# Define CLI hooks
def main():

    index = {
        "NDVI": ndvi,
        "RECI": reci,
        "NDRE": ndre,
        "GNDVI": gndvi
    }

    parser = argparse.ArgumentParser(description="Calculates matrix for selected index")
    parser.add_argument('-i',
                        '--index',
                        type=str,
                        required=True,
                        help="The index to caclualte")
    parser.add_argument('-b',
                        '--bands',
                        nargs='+',
                        type=pathlib.Path,
                        help='list (space seperated) of bands to calculate index. IMPORTANT: order from shortest wavelength to longest',
                        required=True,
                        )
    parser.add_argument('-f',
                        '--force_recompute',
                        action='store_true')

    args = parser.parse_args()

    if args.index in index:
        if (args.force_recompute):
            logging.info('-'*80)
            logging.info("Forced recomputation - recomputing ...")
        index[args.index](args.bands, args.index, args.force_recompute)
    else:
        print("Index not found")

# Helper function to check if band has been seen before & therefor does not need to be re-written to disk
def bands_exist(bands, recompute):
    for band in bands:
        if not (pathlib.Path((band.with_suffix('.pickle').name)).exists()) or recompute:
            logging.info("{} does not exist. Generating ...".format(band.with_suffix('.pickle').name))
            band_link = rasterio.open(str(band))
            band_array = band_link.read()
            band_link.close()
            write_band_to_file(band.with_suffix('').name, band_array, band)
        else:
            logging.info("{} exists! Skipping ingestion ...".format(band.with_suffix('.pickle').name))

def gen_output_name(band, index):
    index_out = band.with_suffix('').name.split("_")
    index_out[2] = index
    index_out = '_'.join(index_out)
    return index_out

############### Define spectral vegetation indicies ##############
##################################################################
"""
Index's are described here: https://eos.com/blog/vegetation-indices/
"""

# Normalized Difference Vegetation Index (NDVI) definition
"""
NDVI is used thoughout crop production and measures 
phtotsynthetically active biomass in plants. 
However, this index is senstive to soil brightness and atmospheric effects -
this can be mitigated though other indices (EVI, SAVI, ARVI, GCL, SIPI)
"""

def ndvi(bands, index, recompute):
    logging.info('-'*80)
    logging.info("Creating NDVI matrix")
    band_data = []
    # Create outfile name 
    index_out = gen_output_name(bands[0], index) # Currently on pause as it relies on the file name
    # Check if the band arrays already exist
    bands_exist(bands, recompute)
    # Check if the index data already exists
    print(pathlib.Path(index_out).with_suffix('.pickle'))
    if (not pathlib.Path(index_out).with_suffix('.pickle').exists()) or recompute:
        logging.info("Index matrix does not exist. Creating ...")
        # Open each bands datafile for index calculation.
        for band in bands:
            band_data.append(read_band_from_file(band.with_suffix('.pickle').name))
        # Set as associated band for code readability
        B04 = band_data[0][1].astype('f4')
        B8A = band_data[1][1].astype('f4')
        # Write index to disk
        write_index_to_file(index_out, (B8A - B04)/(B8A + B04), band_data[0][2])
    else:
        logging.info("Index matrix exists! Skipping computation ...")

# Red-Edge Chlorophyll Vegetation Index (RECI)
"""
Index measures chlorophyll content in leaves that are nourished by nitrogen. 
Shows the photosyntheic activity of the canopy cover. 
"""
def reci(bands, index, recompute):
    logging.info('-'*80)
    logging.info("Creating RECI matrix")
    band_data = []
    # Create outfile name
    index_out = gen_output_name(bands[0], index)
    # Check if the band arrays already exist
    bands_exist(bands, recompute)
    # Check if the index data already exists
    if not (pathlib.Path(index_out).with_suffix('.pickle').exists()) or recompute:
        logging.info("Index matrix does not exist. Creating ...")
        # Open each bands datafile for index calculation.
        for band in bands:
            band_data.append(read_band_from_file(band.with_suffix('.pickle').name))
        # Set as associated band for code readability
        B04 = band_data[0][1].astype('f4')
        B8A = band_data[1][1].astype('f4')
        # Write index to disk
        write_index_to_file(index_out,(B8A/B04) -1, band_data[0][2])
    else:
        logging.info("Index matrix exists! Skipping computation ...")

# Normalized Difference Red Edge Vegetation Index (NDRE)
"""
Is a joint measure of NDVI and RECI indices. 
This index combines NIR spectral bands and a specific band for 
the narrow range between the visible red and read-nir transition
zone. 
"""
def ndre(bands, index, recompute):
    logging.info('-'*80)
    logging.info("Creating NDRE matrix")
    band_data = []
    # Create outfile name
    index_out = gen_output_name(bands[0], index)
    # Check if the band arrays already exist
    bands_exist(bands, recompute)
    # Check if the index data already exists
    if not (pathlib.Path(index_out).with_suffix('.pickle').exists()) or recompute:
        logging.info("Index matrix does not exist. Creating ...")
        # Open each bands datafile for index calculation.
        for band in bands:
            band_data.append(read_band_from_file(band.with_suffix('.pickle').name))
        # Set as associated band for code readability
        B05 = band_data[0][1].astype('f4')
        B8A = band_data[1][1].astype('f4')
        # Write index to disk
        write_index_to_file(index_out,(B8A - B05) / (B8A + B05), band_data[0][2])
    else:
        logging.info("Index matrix exists! Skipping computation ...")

# Green Normalized Difference Vegetation Index (GNDVI)
"""
GNDVI is a modification of NDVI but substitutes the green band for the red band.
GNDVI measures chlorophyll content more accurately than NDVI.
"""
def gndvi(bands, index, recompute):
    logging.info('-'*80)
    logging.info("Creating GNDVI matrix")
    band_data = []
    # Create outfile name
    index_out = gen_output_name(bands[0], index)
    # Check if the band arrays already exist
    bands_exist(bands, recompute)
    # Check if the index data already exists
    if not (pathlib.Path(index_out).with_suffix('.pickle').exists()) or recompute:
        logging.info("Index matrix does not exist. Creating ...")
        # Open each bands datafile for index calculation.
        for band in bands:
            band_data.append(read_band_from_file(band.with_suffix('.pickle').name))
        # Set as associated band for code readability
        B03 = band_data[0][1].astype('f4')
        B8A = band_data[1][1].astype('f4')
        # Write index to disk
        write_index_to_file(index_out,((B8A - B03) / (B8A + B03)), band_data[0][2])
    else:
        logging.info("Index matrix exists! Skipping computation ...")
    

##### TODO: re-organise inputs so it is shortest wavelength TO longest wavelength ########

# Modified Soil-Adjusted Vegetation Index (MSAVI)
"""
This index is designated to mitigate soil effects on crop monitoring 
results. It is applied when NDVI can't provide accurate values - particually
with a high percentage of bare soil, scarce vegetation, or low chlorophyll
content in plants
"""
def msavi(band4, band3):
    logging.info("Creating MSAVI matrix")
    a = 2*band4+1
    write_index_to_file("MSAVI",
                        ((a - sqrt((a*2)-8*(band4-band3)))/2))

# Normalized Difference Water Index (NDWI)
"""
This index outlines open water bodies and assess their turbidity,
mitigating the reflectance of soil and land vegetation cover. 
"""
def ndwi(nir, green):
    logging.info("Creating NDWI matrix")
    write_index_to_file("NDWI",((green - nir) / (green + nir)))

# Soil Adjusted Vegetation Index (SAVI)
"""
Corrects the NDVI index by adding an adjustment factor L to the equation. 
This corrects for soil noise (soil color, moisture, variability etc)
"""
def savi(nir, red, l):
    logging.info("Creating SAVI matrix")
    write_index_to_file("SAVI",(((nir - red) / (nir + red + l)) * (1 + l)))

# Optimized Soil Adjusted Vegetation Index (OSAVI)
"""
Modified SAVI index, which uses reflectance in the NIR and red bands. 
The difference between OSAVI and SAVI is that OSAVI takes into account
the standard value of the canopy background adjustment factor (0.16)
"""
def osavi(nir, red):
    logging.info("Making OSAVI matrix")
    write_index_to_file("OSAVI",(nir - red) / (nir + red + 0.16))

# Atmospherically Resistant Vegetation Index (ARVI)
"""
A vegetation index which mitigates atmospheric factors (e.g., aerosols).
Kuafman and Tanré corrected NDVI to mitigate atomspheric scattering effects
by doubling the red band measurements and adding blue wavelengths
"""
def arvi(nir, red, blue):
    logging.info("Making ARVI matrix")
    write_index_to_file("ARVI",((nir - (2*red) + blue) / (nir + (2*red) + blue)))

# Enhanced Vegetation Index (EVI)
"""
Liu and Huete introduced EVI to adjust NDVI results to atmospheric and 
soil noises, particually in dense vegetation areas.
The value range for EVI is -1 to 1, and for healthy vegetation, it
varies between 0.2 and 0.8
"""
def evi(nir, red, blue, c1, c2, l):
    logging.info("Making EVI matrix")
    # c1 and c2 are coefficents to adjust for aerosol scattering
    # for MODIS sensor, c1 = 6; c2 = 7.5 & l = 1
    write_index_to_file("EVI",(2.5 * ((nir - red) / ((nir) + (c1 * red) - (c2 * blue) + l))))

# Visible Atmospherically Resistant Index (VARI)
"""
Enhances vegetation under strong atmospheric impact while smooting illumination
variations. 
"""
def vari(red, green, blue):
    logging.info("Making VARI matrix")
    write_index_to_file("VARI",(green - red) / (green + red - blue))

# Leaf Area Vegetation Index (LAI)
"""
Designed to analyze the foliage surface of earth and estimate the quantity
of leaves in a specific region. 
"""
def lai():
    # This index requires some form of computer vision to identify the land 
    # mass of an image, and than create a ratio of land mass covered by biomass
    # I have excluded it for now. 
    pass 

# Normalized Burn Ratio (NBR)
"""
Used to highlight burned areas following a fire. 
Healthy vegetation shows a high reflectance in the NIR spectum, whereas 
the recently burned areas of vegetation reflect highly in the SWIR spectrum
"""
def nbr(nir, swir):
    logging.info("Making NBR matrix")
    # SWIR for sentinel2 can be band 12 -> 2190mm short wave infrared
    write_index_to_file("NBR",((nir - swir) / (nir + swir)))

# Structure Insensitive Pigment Vegetation Index (SIPI)
"""
Provides analysis of vegetation with variable sanopy structure. It estimates
the ratio of carotenoids to chlorophyll: an increasing valye signals vegetation stress
"""
def sipi(nir, red, blue):
    logging.info("Making SIPI matrix")
    write_index_to_file("SIPI",((nir - blue) / (nir - red)))

# Green Chlorophyll Vegetation Index (GCI)
"""
Used to estimate the content of leaf chlorophyll in various species of plant. 
The chlorophyll content reflects the physiological state of vegetation; it 
decreases in stressed plants and can therefore be used as a measurement of 
vegetation health
"""
def gci(nir, green):
    logging.info("Making GCI matrix")
    write_index_to_file("GCI",(nir / green - 1))

# Normalized Difference Snow Index (NDSI)
"""
Detects snow cover. Snow has high reflectance in the SWIR band, and low reflectance
in the VIS band. Cloud reflection in these bands are high, allowing snow 
and clouds to be distingushed from each other. 
"""
def ndsi(green, swir):
    logging.info("Making NDSI matrix")
    write_index_to_file("NDSI",((green - swir) / (green + swir)))


if __name__ == "__main__":
    main()