#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import yaml

TITLE = "LivePublication example application (Chapter 4)"
DESCRIPTION_PREFIX = "Example application for Chapter 4 of the LivePublication Framework thesis"
LICENSE = "Apache-2.0"
ORCID = "0000-0001-8260-231X"
ORCID_URL = f"https://orcid.org/{ORCID}"

REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "codemeta.json",
    ".zenodo.json",
    "ro-crate-metadata.json",
    "scripts/generate_ro_crate.py",
    "scripts/validate_metadata.py",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def normalize_orcid(value):
    if not value:
        return ""
    if value.startswith("https://orcid.org/"):
        return value.replace("https://orcid.org/", "")
    return value


def check_no_ellipsis(label, text, errors):
    if text and "..." in text:
        errors.append(f"{label} contains ellipsis")


def main():
    errors = []

    for path in REQUIRED_FILES:
        if not Path(path).exists():
            errors.append(f"Missing required file: {path}")

    if errors:
        print("❌ Metadata validation failed.")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    cff = load_yaml("CITATION.cff")
    codemeta = load_json("codemeta.json")
    zenodo = load_json(".zenodo.json")
    ro_crate = load_json("ro-crate-metadata.json")

    cff_title = cff.get("title")
    if cff_title != TITLE:
        errors.append("CITATION.cff title does not match expected title")

    codemeta_name = codemeta.get("name")
    if codemeta_name != TITLE:
        errors.append("codemeta.json name does not match expected title")

    zenodo_title = zenodo.get("title")
    if zenodo_title != TITLE:
        errors.append(".zenodo.json title does not match expected title")

    graph = ro_crate.get("@graph", [])
    root_dataset = next(
        (item for item in graph if item.get("@id") in ("./", "")), None
    )
    if not root_dataset or root_dataset.get("name") != TITLE:
        errors.append("ro-crate root dataset name does not match expected title")

    cff_orcid = normalize_orcid(
        (cff.get("authors") or [{}])[0].get("orcid", "")
    )
    if cff_orcid != ORCID:
        errors.append("CITATION.cff ORCID does not match expected ORCID")

    codemeta_orcid = normalize_orcid(
        (codemeta.get("author") or {}).get("@id", "")
    )
    if codemeta_orcid != ORCID:
        errors.append("codemeta.json ORCID does not match expected ORCID")

    zenodo_orcid = normalize_orcid(
        (zenodo.get("creators") or [{}])[0].get("orcid", "")
    )
    if zenodo_orcid != ORCID:
        errors.append(".zenodo.json ORCID does not match expected ORCID")

    rocrate_orcids = {
        normalize_orcid(item.get("@id", ""))
        for item in graph
        if "Person" in (item.get("@type") or [])
    }
    if ORCID not in rocrate_orcids:
        errors.append("ro-crate metadata does not include expected ORCID")

    if cff.get("license") != LICENSE:
        errors.append("CITATION.cff license does not match expected license")
    if codemeta.get("license") != LICENSE:
        errors.append("codemeta.json license does not match expected license")
    if zenodo.get("license") != LICENSE:
        errors.append(".zenodo.json license does not match expected license")
    if root_dataset and root_dataset.get("license") != LICENSE:
        errors.append("ro-crate root dataset license does not match expected license")

    check_no_ellipsis("CITATION.cff abstract", cff.get("abstract", ""), errors)
    check_no_ellipsis("codemeta.json description", codemeta.get("description", ""), errors)
    check_no_ellipsis(".zenodo.json description", zenodo.get("description", ""), errors)
    if root_dataset:
        check_no_ellipsis("ro-crate description", root_dataset.get("description", ""), errors)

    if not codemeta.get("description", "").startswith(DESCRIPTION_PREFIX):
        errors.append("codemeta.json description does not match expected wording")
    if not zenodo.get("description", "").startswith(DESCRIPTION_PREFIX):
        errors.append(".zenodo.json description does not match expected wording")
    if root_dataset and not root_dataset.get("description", "").startswith(DESCRIPTION_PREFIX):
        errors.append("ro-crate description does not match expected wording")

    metadata_descriptor = next(
        (item for item in graph if item.get("@id") == "ro-crate-metadata.json"),
        None,
    )
    conforms_to = (
        metadata_descriptor.get("conformsTo", {}).get("@id")
        if metadata_descriptor
        else None
    )
    if conforms_to != "https://w3id.org/ro/crate/1.1":
        errors.append("ro-crate metadata descriptor does not conform to RO-Crate 1.1")

    if errors:
        print("❌ Metadata validation failed.")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    print("✅ Metadata validation passed.")


if __name__ == "__main__":
    main()

