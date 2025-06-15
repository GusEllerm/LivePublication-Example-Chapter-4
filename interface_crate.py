import requests
import json
from datetime import datetime, timezone

from rocrate.rocrate import ROCrate
from rocrate.model.dataset import Dataset
from rocrate.model.contextentity import ContextEntity
import shutil
import os


# Copernicus Data Space Ecosystem API helpers
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
            f"Access token creation failed. Response from the server was: {r.json()}"
        )
    return r.json()["access_token"]

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


def encode_e1_data_producer(crate):
    import glob

    # Find the .SAFE data product directory dynamically
    safe_dirs = glob.glob("Workflow_inputs/Data/*.SAFE")
    if not safe_dirs:
        raise Exception("No .SAFE directories found in Workflow_inputs/Data/")
    safe_dir = safe_dirs[0]
    safe_name = os.path.basename(safe_dir)

    import copernicus_token  # assuming your tokens are stored here
    token = get_access_token(copernicus_token.COPERNICUS_USER, copernicus_token.COPERNICUS_PASS)
    uuid = get_uuid_from_product_name(safe_name, token)

    catalog = crate.add(ContextEntity(crate, "https://dataspace.copernicus.eu/", properties={
        "@type": "DataCatalog",
        "name": "Copernicus Data Space Ecosystem",
        "description": "The official Copernicus Data Space Ecosystem portal providing access to Sentinel and Copernicus services data.",
        "url": "https://dataspace.copernicus.eu/",
        "publisher": {
            "@id": "https://www.copernicus.eu/",
            "@type": "Organization",
            "name": "Copernicus Programme"
        }
    }))

    product_url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({uuid})/$value"

    external_dataset = crate.add(ContextEntity(crate, product_url, properties={
        "@type": "Dataset",
        "identifier": safe_name,
        "name": f"Sentinel-2 Level-2A product: {safe_name}",
        "description": "Remote dataset hosted by the Copernicus Data Space Ecosystem.",
        "isPartOf": {
            "@id": "https://dataspace.copernicus.eu/",
            "@type": "DataCatalog",
            "name": "Copernicus Data Space Ecosystem"
        }
    }))

    # Expected metadata files and a single JPG file inside the SAFE directory
    metadata_files = ["INSPIRE.xml", "manifest.safe", "MTD_MSIL2A.xml"]
    image_files = glob.glob(os.path.join(safe_dir, "*.jpg"))
    if not image_files:
        raise Exception("No .jpg image found in the SAFE directory.")
    image_file = image_files[0]

    # Add the E1 context entity
    e1 = crate.add(ContextEntity(crate, "#E1-data-producer", properties={
        "@type": "Dataset",
        "name": "E1: Data Producer Output",
        "description": "Metadata and references to acquired raw data products.",
    }))

    # Add metadata files and the image file as data entities
    related_files = metadata_files + [os.path.basename(image_file)]
    data_entities = []
    for file_name in related_files:
        full_path = os.path.join(safe_dir, file_name)
        if not os.path.isfile(full_path):
            raise Exception(f"Expected file {file_name} not found in {safe_dir}")
        data_entity = crate.add_file(full_path, properties={
            "encodingFormat": "application/xml" if file_name.endswith(".xml") or file_name.endswith(".safe") else "image/jpeg",
            "about": e1
        })
        data_entities.append(data_entity)

    # Link the data entities to the E1 dataset
    e1["hasPart"] = data_entities + [external_dataset]

    return e1

def encode_e2_1_workflow_infrastructure(crate):
    e2_1 = crate.add(ContextEntity(crate, "#E2.1-workflow-infrastructure", properties={
        "@type": "Dataset",
        "name": "E2.1: Workflow Infrastructure",
        "description": "Description of hardware and software environments used."
    }))

    # Add the Dockerfile
    dockerfile_entity = crate.add_file("Dockerfile", properties={
        "encodingFormat": "text/x-dockerfile-config",
        "name": "Workflow Dockerfile",
        "description": "Defines the container environment for executing the CWL workflow.",
        "about": e2_1
    })

    # Add the Docker container as a SoftwareApplication
    docker_image_url = "https://hub.docker.com/r/gusellerm/veg-index-container"
    docker_entity = crate.add(ContextEntity(crate, docker_image_url, properties={
        "@type": "SoftwareApplication",
        "name": "Vegetation Index Container",
        "description": "Docker container used to execute the vegetation analysis workflow.",
        "softwareRequirements": {"@id": dockerfile_entity["@id"]},
        "applicationCategory": "ContainerEnvironment",
        "url": docker_image_url,
        "softwareVersion": "sha256:77d2d32a93fe2d90f5a0057fb8b12a3967f179cb6110805aadea3302056508a5",
    }))

    # Link the container as a part of the E2.1 dataset
    e2_1["hasPart"] = [dockerfile_entity, docker_entity]

    return e2_1

def encode_e2_2_wms(crate, output_dir):
    e2_2 = crate.add(ContextEntity(crate, "#E2.2-wms", properties={
        "@type": "Dataset",
        "name": "E2.2: Workflow Management System",
        "description": "Provenance of workflow execution including workflow steps and parameters."
    }))
    # Add the nested provenance crate directory
    prov_crate_path = "provenance_output.crate"
    if not os.path.isdir(prov_crate_path):
        raise Exception(f"{prov_crate_path} directory is missing.")

    # Copy the provenance_output.crate into the main RO-Crate output directory
    dst_path = os.path.join(output_dir, os.path.basename(prov_crate_path))
    shutil.copytree(prov_crate_path, dst_path)

    nested_prov = crate.add(Dataset(crate, os.path.basename(prov_crate_path), properties={
        "name": "Provenance Run Crate",
        "description": "Nested RO-Crate containing workflow execution provenance.",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
        "license": "https://creativecommons.org/licenses/by/4.0/"
    }))

    nested_prov["isPartOf"] = {"@id": "#livepublication-interface"}

    e2_2["hasPart"] = [nested_prov]
    return e2_2

def encode_e3_experimental_results(crate):
    e3 = crate.add(ContextEntity(crate, "#E3-experimental-results", properties={
        "@type": "Dataset",
        "name": "E3: Experimental Results and Outcomes",
        "description": "Results of the executed workflow, such as figures and summary data products."
    }))
    zenodo_entity = crate.add(ContextEntity(crate, "https://doi.org/10.5281/zenodo.15665401", properties={
        "@type": "Dataset",
        "name": "Vegetation Analysis Results",
        "description": "Zenodo archive of results generated by the LivePublication Experiment Infrastructure.",
        "identifier": "10.5281/zenodo.15665401",
        "publisher": {
            "@id": "https://zenodo.org/",
            "@type": "Organization",
            "name": "Zenodo"
        },
        "url": "https://doi.org/10.5281/zenodo.15665401",
        "distribution": [
            {
                "@id": "#zenodo-download-gndvi",
                "@type": "DataDownload",
                "contentUrl": "https://zenodo.org/records/15665401/files/GNDVI_10m_example.tif?download=1",
                "encodingFormat": "image/tiff",
                "name": "GNDVI 10m Example TIFF"
            }
        ]
    }))
    e3["hasPart"] = [zenodo_entity]
    return e3


# RO-Crate scaffolding for LivePublication Interface
def create_interface_crate(output_dir: str):
    crate = ROCrate()

    # Create a main entity representing the LivePublication Interface
    main_entity = crate.add(ContextEntity(crate, "#livepublication-interface", properties={
        "@type": "Dataset",
        "name": "LivePublication Interface Outputs",
        "description": "This Dataset represents the outputs of the Experiment Infrastructure required by the LivePublication interface. It includes references to data produced by E1 (Data Producer), E2.1 (Workflow Infrastructure), E2.2 (Workflow Management System), and E3 (Experimental Results and Outcomes).",
        "datePublished": datetime.now(timezone.utc).isoformat()
    }))

    # Define dummy components for E1–E3
    e1 = encode_e1_data_producer(crate)
    e2_1 = encode_e2_1_workflow_infrastructure(crate)
    e2_2 = encode_e2_2_wms(crate, output_dir)
    e3 = encode_e3_experimental_results(crate)

    # Link these components to the mainEntity
    main_entity["hasPart"] = [e1, e2_1, e2_2, e3]

    crate.mainEntity = main_entity

    # Write the RO-Crate to the specified output directory
    crate.write(output_dir)
    print(f"RO-Crate written to {output_dir}")

    import zipfile

    zip_path = f"{output_dir}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    print(f"RO-Crate zipped to {zip_path}")


if __name__ == "__main__":
    crate_name = "interface.crate"
    if os.path.exists(crate_name):
      shutil.rmtree(crate_name)
    create_interface_crate(crate_name)
