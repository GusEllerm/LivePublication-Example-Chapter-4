```python exec
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
```

```python exec
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

```python exec
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

```python exec
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

step_summaries = []
for step in steps:
    step_id = step.get("@id")
    for e in provenance_graph:
        if e.get("@id") == step.get("object").get("@id"):
            tool_action = e

    inputs = tool_action.get("object")
    outputs = tool_action.get("result")
    
    for e in provenance_graph:
        if e.get("@id") == step.get("instrument").get("@id"):
            script = e

    step_summaries.append({
        "step_id": step_id,
        "script": script,
        "inputs": inputs,
        "outputs": outputs
    })
```

```python exec
# Extract E3 result info
e3_dataset = by_id.get("#E3-experimental-results", {})
zenodo_entry = e3_dataset.get("hasPart", [{}])[0].get("@id", None)
```

# Example LivePublication -- dynamic narratives that reflect experimental states

some body text here

## Computational Workflow

on computational workflow

## Sentinel-2A Data Product Overview

This publication uses a **`e1_platform_info_human.get("SPACECRAFT_NAME")`{docsql exec}** `e1_product_info_human.get("PROCESSING_LEVEL")`{docsql exec} product acquired during orbit `e1_platform_info_human.get("SENSING_ORBIT_NUMBER")`{docsql exec} on `e1_platform_info_human.get("DATATAKE_SENSING_START_HUMAN")`{docsql exec}.
The dataset, identified by this [DOI]({{e1_product_info_human.get("PRODUCT_DOI")}}), was processed using baseline **`e1_product_info_human.get("PROCESSING_BASELINE")`{docsql exec}** (see [here](https://sentiwiki.copernicus.eu/web/s2-processing) for information on baseline processing algorithms) on `e1_product_info_human.get("GENERATION_TIME_HUMAN")`{docsql exec}.

```python exec
from IPython.display import Markdown

def render_thumbnail_md_direct(thumbnail_path, alt_text="Sentinel-2A preview"):
    """
    Display the image directly in the output cell using Markdown rendering.
    """
    if not thumbnail_path:
        display(Markdown("> ⚠️ No thumbnail available."))
    else:
        display(Markdown(f"![{alt_text}]({thumbnail_path})"))

    print(f"![{alt_text}]({thumbnail_path})")

render_thumbnail_md_direct(e1_thumbnail)
```

### Image Quality Summary

- **CLOUDY_PIXEL_OVER_LAND_PERCENTAGE**: `e1_image_quality.get("CLOUDY_PIXEL_OVER_LAND_PERCENTAGE")`{docsql exec}
- **NODATA_PIXEL_PERCENTAGE**: `e1_image_quality.get("NODATA_PIXEL_PERCENTAGE")`{docsql exec}
- **SATURATED_DEFECTIVE_PIXEL_PERCENTAGE**: `e1_image_quality.get("SATURATED_DEFECTIVE_PIXEL_PERCENTAGE")`{docsql exec}
- **DARK_FEATURES_PERCENTAGE**: `e1_image_quality.get("DARK_FEATURES_PERCENTAGE")`{docsql exec}
- **CLOUD_SHADOW_PERCENTAGE**: `e1_image_quality.get("CLOUD_SHADOW_PERCENTAGE")`{docsql exec}
- **VEGETATION_PERCENTAGE**: `e1_image_quality.get("VEGETATION_PERCENTAGE")`{docsql exec}
- **NOT_VEGETATED_PERCENTAGE**: `e1_image_quality.get("NOT_VEGETATED_PERCENTAGE")`{docsql exec}
- **WATER_PERCENTAGE**: `e1_image_quality.get("WATER_PERCENTAGE")`{docsql exec}
- **UNCLASSIFIED_PERCENTAGE**: `e1_image_quality.get("UNCLASSIFIED_PERCENTAGE")`{docsql exec}
- **MEDIUM_PROBA_CLOUDS_PERCENTAGE**: `e1_image_quality.get("MEDIUM_PROBA_CLOUDS_PERCENTAGE")`{docsql exec}
- **HIGH_PROBA_CLOUDS_PERCENTAGE**: `e1_image_quality.get("HIGH_PROBA_CLOUDS_PERCENTAGE")`{docsql exec}
- **THIN_CIRRUS_PERCENTAGE**: `e1_image_quality.get("THIN_CIRRUS_PERCENTAGE")`{docsql exec}
- **SNOW_ICE_PERCENTAGE**: `e1_image_quality.get("SNOW_ICE_PERCENTAGE")`{docsql exec}
- **RADIATIVE_TRANSFER_ACCURACY**: `e1_image_quality.get("RADIATIVE_TRANSFER_ACCURACY")`{docsql exec}
- **WATER_VAPOUR_RETRIEVAL_ACCURACY**: `e1_image_quality.get("WATER_VAPOUR_RETRIEVAL_ACCURACY")`{docsql exec}
- **AOT_RETRIEVAL_ACCURACY**: `e1_image_quality.get("AOT_RETRIEVAL_ACCURACY")`{docsql exec}
- **AOT_RETRIEVAL_METHOD**: `e1_image_quality.get("AOT_RETRIEVAL_METHOD")`{docsql exec}
- **GRANULE_MEAN_AOT**: `e1_image_quality.get("GRANULE_MEAN_AOT")`{docsql exec}
- **GRANULE_MEAN_WV**: `e1_image_quality.get("GRANULE_MEAN_WV")`{docsql exec}
- **OZONE_SOURCE**: `e1_image_quality.get("OZONE_SOURCE")`{docsql exec}
- **OZONE_VALUE**: `e1_image_quality.get("OZONE_VALUE")`{docsql exec}

## Data Caveats
