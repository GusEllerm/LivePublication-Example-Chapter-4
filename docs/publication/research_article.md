```python exec always
# Interface connections for incoming interface.crate objects
import json
from pathlib import Path

# Load the interface.crate
crate_path = Path("interface.crate/ro-crate-metadata.json")
with crate_path.open() as f:
    interface_crate = json.load(f)

# Index by @id for convenience
graph = interface_crate["@graph"]
by_id = {entry["@id"]: entry for entry in graph}

# A quick helper to create readable dates
from datetime import datetime

def parse_iso8601(dt_str):
    try:
        # Remove 'Z' if present and parse
        dt_str = dt_str.rstrip("Z")
        dt = datetime.fromisoformat(dt_str)
        # Format as "YYYY-MM-DD HH:MM:SS"
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt_str  # fallback to original if parsing fails
```

```python exec always
# Load metadata for E1: Data Producer Output
import xml.etree.ElementTree as ET
import re

e1_data = by_id.get("#E1-data-producer", {})
e1_files = e1_data.get("hasPart", [])
e1_file_ids = [f["@id"] for f in e1_files if "@id" in f]

# Representative image
e1_thumbnail_id = next((f for f in e1_file_ids if f.endswith("-ql.jpg")), None)
e1_thumbnail = f"interface.crate/{e1_thumbnail_id}" if e1_thumbnail_id else None

# Find the MTD_MSIL2A.xml file among e1_files
mtd_filename = "MTD_MSIL2A.xml"
mtd_id = next((fid for fid in e1_file_ids if fid.endswith(mtd_filename)), None)
mtd_path = Path("interface.crate") / mtd_id if mtd_id else None
e1_metadata = {}

def get_namespace(root):
    m = re.match(r"\{(.*)\}", root.tag)
    return {"n1": m.group(1)} if m else {}

def extract_child_texts(parent, ns):
    return {
        child.tag.replace(f"{{{ns['n1']}}}", ""): child.text
        for child in parent
        if child.text is not None and child.text.strip()
    }

if mtd_path.exists():
    tree = ET.parse(mtd_path)
    root = tree.getroot()
    ns = get_namespace(root)

    # Helper: Find tag and extract key:value pairs
    def extract_metadata(tag):
        elem = root.find(f".//{tag}", ns)
        return extract_child_texts(elem, ns) if elem is not None else {}


    e1_product_info = extract_metadata("Product_Info")
    e1_platform_info = extract_metadata("Datatake")
    e1_image_quality = extract_metadata("Image_Content_QI")

    # Round all float values in e1_image_quality to two decimal places (if possible)
    for k, v in e1_image_quality.items():
        try:
            e1_image_quality[k] = round(float(v), 2)
        except (ValueError, TypeError):
            pass

    e1_product_info_human = dict(e1_product_info)
    e1_platform_info_human = dict(e1_platform_info)

    for key in ["PRODUCT_START_TIME", "PRODUCT_STOP_TIME", "GENERATION_TIME"]:
      if key in e1_product_info_human:
        e1_product_info_human[key + "_HUMAN"] = parse_iso8601(e1_product_info_human[key])

    for key in ["DATATAKE_SENSING_START"]:
      for k in list(e1_platform_info_human.keys()):
        e1_platform_info_human[k + "_HUMAN"] = parse_iso8601(e1_platform_info_human[k]) 

    e1_metadata = {
        "product_info": e1_product_info_human,
        "platform_info": e1_platform_info_human,
        "image_quality": e1_image_quality
    }
```

```python exec always
# Load metadata for E2.1: Workflow Infrastructure
e2_1_data = by_id.get("#E2.1-workflow-infrastructure", {})
e2_1_parts = e2_1_data.get("hasPart", [])
e2_1_dockerfile = next((f["@id"] for f in e2_1_parts if f["@id"] == "Dockerfile"), None)

e2_1_dockerfile_content = None
if e2_1_dockerfile:
  dockerfile_path = Path("interface.crate") / e2_1_dockerfile
  if dockerfile_path.exists():
    with dockerfile_path.open() as f:
      e2_1_dockerfile_content = f.read()

e2_1_container_url = next((f["@id"] for f in e2_1_parts if "docker.com" in f["@id"]), None)
```

```python exec always
# --- NEW: Load the provenance_output.crate ---
# Get the path to the nested crate from the E2.2 entry
e22_wms = by_id.get("#E2.2-wms", {})
provenance_crate_path = e22_wms.get("hasPart", [{}])[0].get("@id", None)

# Load the nested provenance crate if the path is found
provenance_data = {}
if provenance_crate_path:
    provenance_manifest = Path("interface.crate") / provenance_crate_path / "ro-crate-metadata.json"
    if provenance_manifest.exists():
        with provenance_manifest.open() as f:
            provenance_data = json.load(f)


provenance_graph = provenance_data["@graph"]
provenance_by_id = {entry["@id"]: entry for entry in provenance_graph}
workflow = next((e for e in provenance_graph if e.get("@type") == ["File", "SoftwareSourceCode", "ComputationalWorkflow", "HowTo"]), None)
steps = sorted([e for e in provenance_graph if e.get("@type") == "ControlAction"], key=lambda x: x.get("position", 0))

FormalParameters = [e for e in provenance_graph if e.get("@type") == "FormalParameter"]

step_summaries = []
for step in steps:
    for e in provenance_graph:
        if e.get("@id") == step.get("object").get("@id"):
            create_action = e

    inputs = create_action.get("object")
    outputs = create_action.get("result")

    input_entities = []
    output_entities = []

    for e in provenance_graph:
        for input in inputs:
            if input.get("@id") == e.get("@id"):
                input_entities.append(e)

    for e in provenance_graph:
        for output in outputs:
            if output.get("@id") == e.get("@id"):
                output_entities.append(e)
    
    for e in provenance_graph:
        if create_action.get("instrument").get("@id") == e.get("@id"):
            softwareApplication = e
            
    for e in provenance_graph:
        if create_action.get("containerImage").get("@id") == e.get("@id"):
            ContainerImage = e

    # replace the startTime and endTime with human-readable format
    create_action["startTime"] = parse_iso8601(create_action["startTime"])
    create_action["endTime"] = parse_iso8601(create_action["endTime"]) 
    
    step_summaries.append({
        "CreateAction": create_action,
        "SoftwareApplication": softwareApplication,
        "ContainerImage": ContainerImage,
        "Inputs": input_entities,
        "Outputs": output_entities,
    })
```

```python exec always
# Extract E3 result info
e3_dataset = by_id.get("#E3-experimental-results", {})
zenodo_entry = e3_dataset.get("hasPart", [{}])[0].get("@id", None)
```

# Example LivePublication -- dynamic narratives that reflect experimental states

some body text here

## Computational Workflow

```python exec always
png_path = None
png_dir = Path("interface.crate/provenance_output.crate")
if png_dir.exists():
    for file in png_dir.iterdir():
        if file.suffix.lower() == ".png":
            png_path = str(file)
            break
```

`dict(type="ImageObject", contentUrl=png_path)`{python exec}

### Parameters

::: for parameter in FormalParameters {python}

::::: if parameter.get("description") {python}

#### **`parameter["name"].upper()`{python exec}**

| **Description**                         | **Type**                                   |
| --------------------------------------- | ------------------------------------------ |
| `parameter["description"]`{python exec} | `parameter["additionalType"]`{python exec} |

:::::

:::

### Steps

::: for step in step_summaries

### Step `step["SoftwareApplication"]["name"]`{python exec}

This step, **`step["CreateAction"]["name"]`{python exec}**, uses the tool _`step["SoftwareApplication"]["name"]`{python exec}_.

`step["SoftwareApplication"]["description"]`{python exec}

It was executed from **`step["CreateAction"]["startTime"]`{python exec}** to **`step["CreateAction"]["endTime"]`{python exec}**, using the container image **`step["ContainerImage"]["name"]`{python exec}**.

#### Inputs

::::: for input in step["Inputs"]

| Name                                                              | Reference                                                                                                                                                                                        |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `input["name"] if "name" in input else input["@id"]`{python exec} | `", ".join(e["@id"] if isinstance(e, dict) and "@id" in e else str(e) for e in (input["exampleOfWork"] if isinstance(input["exampleOfWork"], list) else [input["exampleOfWork"]]))`{python exec} |

:::::

#### Outputs

::::: for output in step["Outputs"]

| Name                                                                 | Reference                                                                                                                                                                                           |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `output["name"] if "name" in output else output["@id"]`{python exec} | `", ".join(e["@id"] if isinstance(e, dict) and "@id" in e else str(e) for e in (output["exampleOfWork"] if isinstance(output["exampleOfWork"], list) else [output["exampleOfWork"]]))`{python exec} |

:::::

:::

## Sentinel-2A Data Product Overview

This publication uses a **`e1_platform_info_human["SPACECRAFT_NAME"]`{python exec}** `e1_product_info_human["PROCESSING_LEVEL"]`{python exec} product acquired during orbit `e1_platform_info_human["SENSING_ORBIT_NUMBER"]`{python exec} on `e1_platform_info_human["DATATAKE_SENSING_START_HUMAN"]`{python exec}. The dataset, identified by this `dict(type="Link", target=e1_product_info_human["PRODUCT_DOI"], content=[dict(type="Text", value=f"DOI")])`{python exec}, was processed using baseline **`e1_product_info_human["PROCESSING_BASELINE"]`{python exec}** (see [here](https://sentiwiki.copernicus.eu/web/s2-processing) for information on baseline processing algorithms) on `e1_product_info_human["GENERATION_TIME_HUMAN"]`{python exec}.

## Data Alerts

```python exec always
# Create boolean flags for data Alerts
data_alert_flags = {
    "cloudy_pixels": float(e1_image_quality["CLOUDY_PIXEL_OVER_LAND_PERCENTAGE"]) > 50.0,
    "thin_cirrus": float(e1_image_quality["THIN_CIRRUS_PERCENTAGE"]) > 30.0,
    "saturated_pixels": float(e1_image_quality["SATURATED_DEFECTIVE_PIXEL_PERCENTAGE"]) > 0.1,
    "cloud_shadow": float(e1_image_quality["CLOUD_SHADOW_PERCENTAGE"]) > 10.0,
    "low_vegetation": float(e1_image_quality["VEGETATION_PERCENTAGE"]) < 5.0,
    "low_data": float(e1_image_quality["NODATA_PIXEL_PERCENTAGE"]) > 10.0,
}

# Ranked list of all flags
priority_order = [
    "low_data",
    "cloudy_pixels",
    "thin_cirrus",
    "cloud_shadow",
    "saturated_pixels",
    "low_vegetation"
]


active_ranked_flags = [flag for flag in priority_order if data_alert_flags.get(flag)]

active_flags_len = len(active_ranked_flags)

# Workaround: ensure it's at least 2 items so the loop will execute
if len(active_ranked_flags) == 1:
    active_ranked_flags.append("no_op")
```

The Sentinel-2A scene was assessed for conditions that may impact analysis reliability. There are currently **`active_flags_len`{python exec}** active data quality flags:

::: for flag in active_ranked_flags {python}

::::: if flag == "low_data" {python}

A significant portion of the scene contains no data ({{ e1_image_quality["NODATA_PIXEL_PERCENTAGE"] }}%), which may limit the reliability of GNDVI calculations.

:::::

::::: if flag == "cloudy_pixels" {python}

A large proportion of the land surface is cloud-covered ({{ e1_image_quality["CLOUDY_PIXEL_OVER_LAND_PERCENTAGE"] }}%), which may significantly distort GNDVI signals.

:::::

::::: if flag == "thin_cirrus" {python}

Thin cirrus clouds are present ({{ e1_image_quality["THIN_CIRRUS_PERCENTAGE"] }}%), potentially elevating NIR values and distorting vegetation estimates.

:::::

::::: if flag == "cloud_shadow" {python}

Cloud shadows affect part of the scene ({{ e1_image_quality["CLOUD_SHADOW_PERCENTAGE"] }}%), possibly reducing GNDVI by lowering NIR reflectance.

:::::

::::: if flag == "saturated_pixels" {python}

Saturation has been detected in {{ e1_image_quality["SATURATED_DEFECTIVE_PIXEL_PERCENTAGE"] }}% of pixels, indicating possible data corruption in bright areas.

:::::

::::: if flag == "low_vegetation" {python}

Vegetation coverage is low ({{ e1_image_quality["VEGETATION_PERCENTAGE"] }}%), which can make GNDVI more sensitive to atmospheric noise or edge effects.

:::::

::::: if flag == "no_op" {python}

:::::

:::

Analysts should carefully consider these conditions before using this dataset in quantitative workflows.

### Image Preview

```python exec always
# Scan the directory containing crate_path for a .jpg file and return its path
jpg_path = None
for file in crate_path.parent.iterdir():
    if file.suffix.lower() == ".jpg":
        jpg_path = str(file)
        break
```

`dict(type="ImageObject", contentUrl=jpg_path)`{python exec}

### Image Quality Summary

| Property                            | Value                                                                    |
| ----------------------------------- | ------------------------------------------------------------------------ |
| **Cloudy Pixels Over Land**         | `e1_image_quality["CLOUDY_PIXEL_OVER_LAND_PERCENTAGE"]`{python exec}%    |
| **No Data Pixels**                  | `e1_image_quality["NODATA_PIXEL_PERCENTAGE"]`{python exec}%              |
| **Saturated/Defective Pixels**      | `e1_image_quality["SATURATED_DEFECTIVE_PIXEL_PERCENTAGE"]`{python exec}% |
| **Dark Features**                   | `e1_image_quality["DARK_FEATURES_PERCENTAGE"]`{python exec}%             |
| **Cloud Shadow**                    | `e1_image_quality["CLOUD_SHADOW_PERCENTAGE"]`{python exec}%              |
| **Vegetation**                      | `e1_image_quality["VEGETATION_PERCENTAGE"]`{python exec}%                |
| **Not Vegetated**                   | `e1_image_quality["NOT_VEGETATED_PERCENTAGE"]`{python exec}%             |
| **Water**                           | `e1_image_quality["WATER_PERCENTAGE"]`{python exec}%                     |
| **Unclassified**                    | `e1_image_quality["UNCLASSIFIED_PERCENTAGE"]`{python exec}%              |
| **Medium Probability Clouds**       | `e1_image_quality["MEDIUM_PROBA_CLOUDS_PERCENTAGE"]`{python exec}%       |
| **High Probability Clouds**         | `e1_image_quality["HIGH_PROBA_CLOUDS_PERCENTAGE"]`{python exec}%         |
| **Thin Cirrus**                     | `e1_image_quality["THIN_CIRRUS_PERCENTAGE"]`{python exec}%               |
| **Snow/Ice**                        | `e1_image_quality["SNOW_ICE_PERCENTAGE"]`{python exec}%                  |
| **Radiative Transfer Accuracy**     | `e1_image_quality["RADIATIVE_TRANSFER_ACCURACY"]`{python exec}           |
| **Water Vapour Retrieval Accuracy** | `e1_image_quality["WATER_VAPOUR_RETRIEVAL_ACCURACY"]`{python exec}       |
| **AOT Retrieval Accuracy**          | `e1_image_quality["AOT_RETRIEVAL_ACCURACY"]`{python exec}                |
| **AOT Retrieval Method**            | `e1_image_quality["AOT_RETRIEVAL_METHOD"]`{python exec}                  |
| **Granule Mean AOT**                | `e1_image_quality["GRANULE_MEAN_AOT"]`{python exec}                      |
| **Granule Mean Water Vapour**       | `e1_image_quality["GRANULE_MEAN_WV"]`{python exec}                       |
| **Ozone Source**                    | `e1_image_quality["OZONE_SOURCE"]`{python exec}                          |
| **Ozone Value**                     | `e1_image_quality["OZONE_VALUE"]`{python exec}                           |
