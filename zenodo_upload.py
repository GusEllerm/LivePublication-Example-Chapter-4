import requests
import json
import os
from datetime import date
from zenodo_token import token

ZENODO_API_BASE = "https://zenodo.org/api"
CONCEPT_RECORD_ID = 15644629  # The concept record that groups all versions

def list_depositions():
    url = f"{ZENODO_API_BASE}/deposit/depositions"
    params = {"access_token": token}
    response = requests.get(url, params=params)
    response.raise_for_status()
    print(response.json())
    return response.json()

def create_new_version():
    url = f"{ZENODO_API_BASE}/deposit/depositions/{CONCEPT_RECORD_ID}/actions/newversion"
    params = {"access_token": token}
    response = requests.post(url, params=params)
    if response.status_code == 404:
        print(f"❌ Concept record ID {CONCEPT_RECORD_ID} not found. It may not exist or you may not have access.")
        return None
    elif response.status_code == 403:
        print(f"❌ Access forbidden to concept record ID {CONCEPT_RECORD_ID}. You may not be the owner.")
        return None
    response.raise_for_status()
    new_draft_url = response.json()["links"]["latest_draft"]
    new_deposition_id = int(new_draft_url.split("/")[-1])
    return new_deposition_id

def get_incremented_version(deposition_id):
    
    # Retrieve the concept record for the deposition
    deposition_url = f"{ZENODO_API_BASE}/deposit/depositions/{deposition_id}"
    params = {"access_token": token}
    response = requests.get(deposition_url, params=params)
    response.raise_for_status()
    conceptrecid = response.json().get("conceptrecid")

    # Get the latest published version associated with the concept record
    url = f"{ZENODO_API_BASE}/records"
    query_params = {
        "q": f"conceptrecid:{conceptrecid}",
        "sort": "mostrecent",
        "size": 1,
        "access_token": token
    }
    records_response = requests.get(url, params=query_params)
    records_response.raise_for_status()
    hits = records_response.json().get("hits", {}).get("hits", [])
    if hits:
        metadata = hits[0].get("metadata", {})
        current_version = metadata.get("version", "1.0.0")
    else:
        current_version = "1.0.0"

    print(f"Current version from latest published record: {current_version}")
    try:
        major, minor, patch = map(int, current_version.split("."))
        minor += 1
        return f"{major}.{minor}.{patch}"
    except Exception:
        print("⚠️ Could not parse current version; defaulting to 1.0.0")
        return "1.0.0"

def update_metadata(deposition_id):
    url = f"{ZENODO_API_BASE}/deposit/depositions/{deposition_id}"
    params = {"access_token": token}
    headers = {"Content-Type": "application/json"}
    metadata = {
        "metadata": {
            "title": "Vegetation Index Image Output from CWL Workflow",
            "upload_type": "image",
            "image_type": "plot",
            "publication_date": date.today().isoformat(),
            "description": "<p><em>Generated by a CWL-based workflow using cwltool and CWLProv. Provenance Run Crate available via <a href='https://github.com/GusEllerm/cwl-provenance-crate-example/blob/master/provenance_output.crate.zip'>GitHub</a>.</em></p>",
            "creators": [
                {
                    "name": "Ellerm, Augustus",
                    "orcid": "0000-0001-8260-231X"
                }
            ],
            "access_right": "open",
            "license": "cc-by-4.0",
            "keywords": ["vegetation index", "remote sensing", "Sentinel-2", "NDVI", "GNDVI", "workflow provenance", "CWL"],
            "related_identifiers": [
                {
                    "identifier": "https://github.com/GusEllerm/cwl-provenance-crate-example/blob/master/provenance_output.crate.zip",
                    "relation": "isDerivedFrom",
                    "resource_type": "software"
                }
            ],
            "version": get_incremented_version(deposition_id),
            "language": "eng"
        }
    }
    response = requests.put(url, params=params, data=json.dumps(metadata), headers=headers)
    response.raise_for_status()
    return response.json()

def upload_file_to_deposition(deposition_id, file_path):
    url = f"{ZENODO_API_BASE}/deposit/depositions/{deposition_id}/files"
    params = {"access_token": token}
    # Check for and delete existing file with the same name
    files_url = f"{ZENODO_API_BASE}/deposit/depositions/{deposition_id}/files"
    list_response = requests.get(files_url, params=params)
    list_response.raise_for_status()
    for existing_file in list_response.json():
        if existing_file["filename"] == os.path.basename(file_path):
            file_id = existing_file["id"]
            delete_url = f"{files_url}/{file_id}"
            del_response = requests.delete(delete_url, params=params)
            del_response.raise_for_status()
            print(f"Deleted existing file with same name: {existing_file['filename']}")
    with open(file_path, "rb") as fp:
        files = {"file": (os.path.basename(file_path), fp)}
        response = requests.post(url, params=params, files=files)
    if response.status_code == 400:
        print("❌ Bad request (400) when uploading file. Response content:")
        print(response.text)
        response.raise_for_status()
    elif response.status_code != 201:
        print("❌ Failed to upload file. Response:")
        print(response.status_code, response.text)
        response.raise_for_status()
    return response.json()

def publish_deposition(deposition_id):
    url = f"{ZENODO_API_BASE}/deposit/depositions/{deposition_id}/actions/publish"
    params = {"access_token": token}
    response = requests.post(url, params=params)
    response.raise_for_status()
    return response.json()

def main():
    deposition_id = create_new_version()
    if not deposition_id:
        print("Exiting due to failure creating new version.")
        return

    tif_file = next((f for f in os.listdir(".") if f.endswith(".tif")), None)
    if not tif_file:
        print("No .tif file found in current directory.")
        return
    
    os.rename(tif_file, "GNDVI_10m_example.tif")
    tif_file = "GNDVI_10m_example.tif"

    print(f"New draft deposition ID: {deposition_id}")

    print(f"Uploading {tif_file}...")
    try:
        upload_response = upload_file_to_deposition(deposition_id, tif_file)
        print(f"Uploaded file metadata: {upload_response}")
    except requests.HTTPError as e:
        print("Upload failed with error:")
        print(e)
        print("Please check the error details above for more information.")
        return

    print("Updating metadata...")
    update_metadata(deposition_id)

    print("Publishing new version...")
    publish_response = publish_deposition(deposition_id)
    print(f"Published: {publish_response['doi']}")

if __name__ == "__main__":
    main()