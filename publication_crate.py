from rocrate.rocrate import ROCrate, Dataset
from rocrate.model.contextentity import ContextEntity
from pathlib import Path
import os
import shutil
from datetime import datetime, timezone
import subprocess
import re

def encode_interface_crate(crate, output_dir):
   
    # Add the nested provenance crate directory
    interface_crate_path = "interface.crate"
    if not os.path.isdir(interface_crate_path):
        raise Exception(f"{interface_crate_path} directory is missing.")

    # Copy the provenance_output.crate into the main RO-Crate output directory
    dst_path = os.path.join(output_dir, os.path.basename(interface_crate_path))
    shutil.copytree(interface_crate_path, dst_path)

    nexted_interface_crate = crate.add(Dataset(crate, os.path.basename(interface_crate_path), properties={
        "name": "Interface Crate",
        "description": "Nested interface.crate containing Experiement Infrastrutcure execution data.",
        "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
        "license": "https://creativecommons.org/licenses/by/4.0/"
    }))


    return nexted_interface_crate

def create_publication_crate(crate_name: str):
    publication_crate = ROCrate()

    # Create a main entity representing the Research Article itself
    article = publication_crate.add_file("docs/publication/dynamic_article.html", properties={
        "@type": "ScholarlyArticle",
        "name": "LivePublication: A Dynamic and Reproducible Research Article",
        "description": "A rendered article generated from the DNF Evaluated Document using the DNF Engine and Presentation Environment.",
        "datePublished": datetime.now(timezone.utc).isoformat(),
        "encodingFormat": "html"
    })

    publication_crate.mainEntity = article

    evaluated_doc = publication_crate.add_file("dynamic_article.json", properties={
        "@type": "CreativeWork",
        "name": "Evaluated DNF Document",
        "description": "Resolved dynamic narrative, produced by the DNF Engine using the interface.crate and DNF Document.",
        "encodingFormat": "application/json"
    })

    # Link the main article to its source evaluated document
    article["isBasedOn"] = evaluated_doc

    dnf_document = publication_crate.add_file("DNF_document.json", properties={
        "@type": "CreativeWork",
        "name": "DNF Document",
        "description": "The unresolved dynamic narrative source used by the DNF Engine to produce the evaluated document.",
        "encodingFormat": "application/json"
    })

    evaluated_doc["isBasedOn"] = [dnf_document]

  

    try:
        version_output = subprocess.check_output(["stencila", "--version"], text=True).strip()
    except subprocess.CalledProcessError:
        version_output = "unknown"

    dnf_engine = publication_crate.add(ContextEntity(publication_crate, "#stencila", properties={
        "@type": "SoftwareApplication",
        "name": "Stencila",
        "description": "The DNF Engine used to resolve the dynamic narrative.",
        "softwareVersion": version_output,
        "url": "https://github.com/stencila/stencila",
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
        "howToUse": "https://github.com/stencila/stencila/blob/main/docs/reference/cli.md",
        "operatingSystem": "all"
    }))

    evaluated_doc["producedBy"] = dnf_engine

    # Add interface crate as a nested entity
    interface_entity = encode_interface_crate(publication_crate, crate_name)
    
    evaluated_doc["uses"] = [interface_entity]

    # Attempt to normalize version string to use in URL
    version_match = re.search(r"(\d+\.\d+\.\d+)", version_output)
    version_tag = f"v{version_match.group(1)}" if version_match else "main"

    dnf_engine_spec = publication_crate.add(ContextEntity(publication_crate, f"https://github.com/stencila/stencila/tree/{version_tag}/schema", properties={
        "@type": "CreativeWork",
        "name": "Stencila DNF Engine Specification",
        "description": "Specification and JSON Schemas used by the Stencila DNF Engine to validate and interpret dynamic documents.",
        "url": f"https://github.com/stencila/stencila/tree/{version_tag}/schema",
        "license": "https://www.apache.org/licenses/LICENSE-2.0"
    }))

    dnf_engine["conformsTo"] = dnf_engine_spec
    dnf_document["conformsTo"] = dnf_engine_spec
    # Specify that the article was created using the Stencila engine as the presentation environment
    article["usedSoftware"] = [dnf_engine]

    publication_crate.write(crate_name)

    import zipfile

    zip_path = f"{crate_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(crate_name):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, crate_name)
                zipf.write(file_path, arcname)
    print(f"RO-Crate zipped to {zip_path}")


if __name__ == "__main__":
    crate_name = "publication.crate"
    if os.path.exists(crate_name):
      shutil.rmtree(crate_name)
    create_publication_crate(crate_name)


# Starting scaffold for the publication crate; additional artefacts will be added next.
