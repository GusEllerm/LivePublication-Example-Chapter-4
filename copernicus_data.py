# copernicus_data.py

import requests
import os
from copernicus_token import COPERNICUS_USER, COPERNICUS_PASS
import json
import pprint
import zipfile
import random
import yaml
import glob
import shutil

STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac/collections/SENTINEL-2/items"
   
BBOX = "6.301926,41.422467,22.843947,52.947502"

def get_access_token(username: str, password: str) -> str:
    data = {
        "client_id": "cdse-public",
        "username": username,
        "password": password,
        "grant_type": "password",
    }
    try:
        r = requests.post(
            "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
            data=data,
        )
        r.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Access token creation failed. Reponse from the server was: {r.json()}"
        )
    return r.json()["access_token"]



def list_sentinel2_l2a(limit=100):
    query = f"{STAC_URL}?bbox={BBOX}&limit={limit}"
    response = requests.get(query)
    response.raise_for_status()
    items = response.json().get("features", [])

    # Filter items where ID contains 'L2A'
    filtered_items = [item for item in items if 'L2A' in item.get("id", "")]

    print(f"Found {len(filtered_items)} items containing 'L2A'.")

    return filtered_items

def select_random_item(items):
    if not items:
        return None
    return random.choice(items)


# Download a selected item
def download_selected_item(item, uuid, token, target_dir="Workflow_inputs/Data"):

    download_url = f"https://zipper.dataspace.copernicus.eu/odata/v1/Products({uuid})/$value"

    filename = os.path.join(target_dir, item["id"] + ".zip")

    print(f"Downloading {filename} from {download_url}")

    headers = {"Authorization": f"Bearer {token}"}
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(download_url, headers=headers, stream=True)

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    response.raise_for_status()  # Ensure the download was successful

    if not os.path.exists(filename):
        raise Exception(f"Failed to download {filename}. Please check the link or your network connection.")
    
    print(f"Download complete: {filename}")
    
    return filename

def get_uuid_from_product_name(product_name: str, token: str) -> str:
    url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "$filter": f"Name eq '{product_name}'",
        "$top": 1
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json().get("value", [])
    
    if not results:
        raise Exception(f"No UUID found for product name: {product_name}")
    
    print(f"Found UUID for product {product_name}: {results[0]['Id']}")
    
    return results[0]["Id"]


def find_band_files(base_dir, band_ids=["B03", "B08"], resolution="R10m"):
    band_files = {}
    for band in band_ids:
        pattern = os.path.join(base_dir, "GRANULE", "*", "IMG_DATA", resolution, f"*_{band}_10m.jp2")
        print(pattern)
        matches = glob.glob(pattern)
        if matches:
            band_files[band] = matches[0]  # use the first match
        else:
            raise FileNotFoundError(f"Could not find {band} band file in {base_dir}")
    return band_files

def update_cwl_job_file(band_files, output_path="Workflow_inputs/GNDVI_10m.yaml"):
    job_data = {
        "index": "GNDVI",
        "bands": [
            {"class": "File", "path": os.path.abspath(band_files["B03"])},
            {"class": "File", "path": os.path.abspath(band_files["B08"])},
        ],
        "color": "RdYlGn"
    }
    with open(output_path, "w") as f:
        yaml.dump(job_data, f, default_flow_style=False)
    print(f"Updated CWL input file: {output_path}")


if __name__ == "__main__":
    access_token = get_access_token(COPERNICUS_USER, COPERNICUS_PASS)

    products = list_sentinel2_l2a()
    if products:
        selected_item = select_random_item(products)
        if selected_item is not None:
            print(f"Selected item: {selected_item['id']}")
            uuid = get_uuid_from_product_name(selected_item['id'], access_token)
            data = download_selected_item(selected_item, uuid, access_token)
            # Unzip the downloaded file
            unzipped_dir = os.path.splitext(data)[0]
            print(f"Unzipping {data} to {unzipped_dir}")
            with zipfile.ZipFile(data, 'r') as zip_ref:
                zip_ref.extractall(unzipped_dir)
            os.remove(data)
            print(f"Removed zipped file: {data}")

            # Fix potential nested .SAFE directory
            extracted_dirs = [name for name in os.listdir(unzipped_dir) if name.endswith(".SAFE")]
            if len(extracted_dirs) == 1:
                inner_dir = os.path.join(unzipped_dir, extracted_dirs[0])
                if os.path.isdir(inner_dir):
                    for item in os.listdir(inner_dir):
                        shutil.move(os.path.join(inner_dir, item), unzipped_dir)
                    os.rmdir(inner_dir)
                    print(f"Flattened nested .SAFE directory: {inner_dir}")

            print(f"Extracted to: {unzipped_dir}")

            # --- Automatically update CWL job input file after extracting .SAFE data ---
            band_files = find_band_files(unzipped_dir)
            update_cwl_job_file(band_files)

        else:
            print("No item was selected.")
    else:
        print("No items found.")