import logging
import argparse
import pathlib
import matplotlib.pyplot as plt
from file_handling import read_band_from_file

# Turn logging on
logging.getLogger().setLevel(logging.INFO)
logging.info("tiff_gen module loaded")
logging.info(f"Current working directory: {pathlib.Path.cwd()}")

def main():
    parser = argparse.ArgumentParser(description="Creates TIFF images from index files. Different Color reliefs can be applied")
    parser.add_argument('-i',
                        '--index_file',
                        type=pathlib.Path,
                        required=True,
                        help="Previously calculated matrix")
    parser.add_argument('-c',
                        '--color',
                        type=str,
                        required=False,
                        help="A color profile for the resulting TiFF output")
    parser.add_argument('-f',
                        '--force_recompute',
                        action='store_true',
                        help="Recomputes tiff regardless if it is found in directory")

    args = parser.parse_args()

    if (args.force_recompute):
        logging.info("Forced recomputation - recomputing ...")

    generate_tiff(args.index_file, args.color, args.force_recompute)


## Image generation
def generate_tiff(index, color, recompute):
    logging.info('-'*80)
    logging.info("Creating {}.tif".format(index.stem))
    # Extract index information
    index = read_band_from_file(str(index))
    index_name, index_matrix, index_profile = index[0], index[1][0], index[2]
    # Make outfile name
    outfile = pathlib.Path(index_name).with_suffix('.tif')
    # Check if tiff already exists for this index
    if not (outfile.exists()) or recompute:
        logging.info("Tiff image does not exist. Creating ...")
        if (color != None):
            plt.imshow(index_matrix, cmap=color)
        else:
            plt.imshow(index_matrix)
        plt.colorbar()
        plt.title(index_name)
        plt.xlabel("Column #")
        plt.ylabel("Row #")
        logging.info(f"Saving tiff image to {str(outfile)}")
        plt.savefig(outfile, dpi=800)
    else:
        logging.info("{} exists! Skipping computation ...".format(str(outfile)))


if __name__ == "__main__":
    main()