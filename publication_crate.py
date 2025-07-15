from rocrate.rocrate import ROCrate, ContextEntity, Dataset
from pathlib import Path
import os
import shutil
import re
import subprocess


# Helper functions for DNF contextual entities
def add_dnf_evaluated_document(crate):
    evaluated_file = crate.add_file("DNF_Evaluated_Document.json", properties={
        "name": "DNF Evaluated Document File",
        "description": "The machine-readable, coompiled DNF document containing resolved dynamic content.",
        "encodingFormat": "application/json"
    })
    return evaluated_file

def add_dnf_document(crate):
    dnf_file = crate.add_file("DNF_Document.json", properties={
        "name": "DNF Document File",
        "description": "The unresolved dynamic narrative document serving as input to the DNF Engine.",
        "encodingFormat": "application/json"
    })
    return dnf_file

def add_dnf_engine(crate):
    try:
        version_output = subprocess.check_output(["stencila", "--version"], text=True).strip()
    except Exception:
        version_output = "unknown"

    stencila_software = crate.add(ContextEntity(crate, "#stencila", properties={
        "@type": "SoftwareApplication",
        "name": "Stencila",
        "description": "The DNF Engine used to resolve the dynamic narrative.",
        "softwareVersion": version_output,
        "url": "https://github.com/stencila/stencila",
        "license": "https://www.apache.org/licenses/LICENSE-2.0",
        "howToUse": "https://github.com/stencila/stencila/blob/main/docs/reference/cli.md",
        "operatingSystem": "all"
    }))

    return stencila_software

def add_dnf_engine_spec(crate):
    try:
        version_output = subprocess.check_output(["stencila", "--version"], text=True).strip()
    except subprocess.CalledProcessError:
        version_output = "unknown"

    version_match = re.search(r"(\d+\.\d+\.\d+)", version_output)
    version_tag = f"v{version_match.group(1)}" if version_match else "main"

    stencila_spec = crate.add(ContextEntity(crate, "#stencila-schema", properties={
        "@type": "CreativeWork",
        "name": "Stencila DNF Engine Specification",
        "description": "Specification and JSON Schemas used by the Stencila DNF Engine to validate and interpret dynamic documents.",
        "url": f"https://github.com/stencila/stencila/tree/{version_tag}/schema",
        "license": "https://www.apache.org/licenses/LICENSE-2.0"
    }))

    return stencila_spec

def add_dnf_presentation_env(crate):
    wrapper = crate.add(ContextEntity(crate, "#dnf-presentation-environment", properties={
        "@type": "CreativeWork",
        "name": "DNF Presentation Environment",
        "description": "Environment responsible for converting the evaluated DNF document into presentation formats."
    }))

    return wrapper

def add_dnf_schema(crate):
    wrapper = crate.add(ContextEntity(crate, "#dnf-schema", properties={
        "@type": "CreativeWork",
        "name": "DNF Document Schema",
        "description": "Schema used to validate the structure and fields of the DNF Document."
    }))

    wrapper["conformsTo"] = crate.get("#stencila-schema")

    return wrapper

def add_dnf_data_dependencies(crate):
    interface_crate_path = "interface.crate"
    if not os.path.isdir(interface_crate_path):
        raise Exception(f"{interface_crate_path} directory is missing.")


    nested_interface_crate = crate.add(Dataset(crate, os.path.basename(interface_crate_path), properties={
        "name": "Interface Crate",
        "@type": ["RO-Crate", "Dataset"],
        "description": "Nested interface.crate containing Experiment Infrastructure execution data.",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "@type": ["RO-Crate", "Dataset"],
    }))

    return nested_interface_crate

def add_main_article(crate):
    main_article = crate.add(ContextEntity(crate, "#research-article", properties={
        "@type": "ScholarlyArticle",
        "name": "LivePublication: A Dynamic and Reproducible Research Article",
        "description": "Human-Readable, compiled article generated from dynamic inputs, code, and narrative."
    }))

    html_article = crate.add_file("docs/publication/research_article.html", properties={
        "name": "LivePublication HTML View",
        "description": "HTML-rendered version of the LivePublication article.",
        "encodingFormat": "text/html"
    })

    markdown_article = crate.add_file("docs/publication/research_article.md", properties={
        "name": "LivePublication Markdown Source",
        "description": "Markdown-rendered version of the LivePublication article.",
        "encodingFormat": "text/markdown"
    })

    main_article["hasPart"] = [html_article, markdown_article]

    crate.mainEntity = main_article
    return main_article

def create_publication_crate(crate_name: str):
    crate = ROCrate()

    research_article = add_main_article(crate)

    dnf_document = add_dnf_document(crate)
    dnf_engine = add_dnf_engine(crate)
    dnf_engine_spec = add_dnf_engine_spec(crate)
    dnf_data_dependencies = add_dnf_data_dependencies(crate)
    dnf_engine_schema = add_dnf_schema(crate)

    dnf_eval_doc = add_dnf_evaluated_document(crate)
    dnf_presentation_env = add_dnf_presentation_env(crate)

    dnf_eval_doc["isBasedOn"] = [dnf_document, dnf_data_dependencies, dnf_engine]
    dnf_presentation_env["isBasedOn"] = [dnf_engine]
    dnf_engine["isBasedOn"] = [dnf_engine_spec]
    research_article["isBasedOn"] = [dnf_eval_doc, dnf_presentation_env]

    dnf_document["conformsTo"] = dnf_engine_spec
    research_article["wasGeneratedBy"] = dnf_presentation_env
    dnf_document["conformsTo"] = dnf_engine_schema

    crate.write(crate_name)

    print(f"RO-Crate written to {crate_name}")

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