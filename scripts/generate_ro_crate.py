#!/usr/bin/env python3
from pathlib import Path
import shutil

from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity

TITLE = "LivePublication example application (Chapter 4)"
DESCRIPTION = (
    "Example application for Chapter 4 of the LivePublication Framework thesis, "
    "demonstrating a CWL-based experiment infrastructure, RO-Crate interface outputs, "
    "and dynamic publication rendering."
)
LICENSE = "Apache-2.0"
VERSION = "1.0.1"
DOI_URL = "https://doi.org/10.5281/zenodo.18252594"
REPO_URL = "https://github.com/GusEllerm/LivePublication-Example-Chapter-4"
ORCID_URL = "https://orcid.org/0000-0001-8260-231X"


def add_if_exists(crate, path_str):
    path = Path(path_str)
    if not path.exists():
        return None
    dest_path = f"./{path.as_posix()}"
    return crate.add_file(
        str(path),
        dest_path=dest_path,
        properties={"name": path.as_posix()},
    )


def main():
    crate = ROCrate()

    person = crate.add(
        ContextEntity(
            crate,
            ORCID_URL,
            properties={
                "@type": "Person",
                "name": "Augustus Ellerm",
                "givenName": "Augustus",
                "familyName": "Ellerm",
            },
        )
    )

    software = crate.add(
        ContextEntity(
            crate,
            "#livepublication-example",
            properties={
                "@type": "SoftwareSourceCode",
                "name": TITLE,
                "description": DESCRIPTION,
                "codeRepository": REPO_URL,
                "identifier": DOI_URL,
                "version": VERSION,
                "license": LICENSE,
                "author": person,
                "programmingLanguage": "Python",
            },
        )
    )

    root = crate.root_dataset
    root["name"] = TITLE
    root["description"] = DESCRIPTION
    root["license"] = LICENSE
    root["version"] = VERSION
    root["identifier"] = DOI_URL
    root["creator"] = person
    root["mainEntity"] = software
    root["conformsTo"] = {"@id": "https://w3id.org/ro/crate/1.1"}

    key_paths = [
        "README.md",
        "LICENSE",
        "CITATION.cff",
        "codemeta.json",
        ".zenodo.json",
        "requirements.txt",
        "Dockerfile",
        "publish_pipeline.sh",
        "copernicus_data.py",
        "interface_crate.py",
        "publication_crate.py",
        "dynamic_publication.smd",
        "Workflows/workflow.cwl",
        "Workflow_inputs/GNDVI_10m.yaml",
        "workflow_preview.png",
        "docs/index.html",
        "docs/publication/research_article.html",
        "scripts/generate_ro_crate.py",
        "scripts/validate_metadata.py",
        "Makefile",
    ]

    parts = [part for part in (add_if_exists(crate, p) for p in key_paths) if part]
    if parts:
        root["hasPart"] = parts

    temp_dir = Path(".ro-crate-temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    crate.write(temp_dir)

    metadata_path = temp_dir / "ro-crate-metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError("RO-Crate metadata was not generated as expected.")
    shutil.copy2(metadata_path, Path("ro-crate-metadata.json"))
    shutil.rmtree(temp_dir)
    print("RO-Crate metadata written to ro-crate-metadata.json")


if __name__ == "__main__":
    main()

