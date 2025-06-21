from rocrate.rocrate import ROCrate, ContextEntity, Dataset
from pathlib import Path
import os
import shutil
import re
import subprocess


# Helper functions for DNF contextual entities
def add_dnf_evaluated_document(crate):
    wrapper = crate.add(ContextEntity(crate, "#dnf-evaluated-document", properties={
        "@type": "CreativeWork",
        "name": "DNF Evaluated Document",
        "description": "The machine-readable, coompiled DNF document containing resolved dynamic content."
    }))

    evaluated_file = crate.add_file("DNF_Evaluated_Document.json", properties={
        "@type": "CreativeWork",
        "name": "DNF Evaluated Document File",
        "description": "The actual evaluated JSON file corresponding to the DNF document.",
        "encodingFormat": "application/json"
    })

    dnf_document = add_dnf_document(crate)
    dnf_engine = add_dnf_engine(crate)
    dnf_data_dependencies = add_dnf_data_dependencies(crate)
    # Only include the evaluated file as hasPart
    wrapper["hasPart"] = [evaluated_file]
    return wrapper

def add_dnf_document(crate):
    wrapper = crate.add(ContextEntity(crate, "#dnf-document", properties={
        "@type": "CreativeWork",
        "name": "DNF Document",
        "description": "The unresolved dynamic narrative document serving as input to the DNF Engine."
    }))

    dnf_file = crate.add_file("DNF_Document.json", properties={
        "@type": "CreativeWork",
        "name": "DNF Document File",
        "description": "The unresolved DNF document in JSON format.",
        "encodingFormat": "application/json"
    })

    dnf_schema = add_dnf_schema(crate)
    wrapper["hasPart"] = [dnf_file]
    return wrapper

import subprocess

def add_dnf_engine(crate):
    wrapper = crate.add(ContextEntity(crate, "#dnf-engine", properties={
        "@type": "CreativeWork",
        "name": "DNF Engine",
        "description": "The software application responsible for evaluating the DNF Document."
    }))

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

    wrapper["hasPart"] = [stencila_software]
    return wrapper

def add_dnf_engine_spec(crate):
    wrapper = crate.add(ContextEntity(crate, "#dnf-engine-specification", properties={
        "@type": "CreativeWork",
        "name": "DNF Engine Specification",
        "description": "Formal specification of the DNF Engine's expected behavior and schema usage."
    }))

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

    wrapper["hasPart"] = [stencila_spec]
    return wrapper

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
    wrapper = crate.add(ContextEntity(crate, "#dnf-data-dependencies", properties={
        "@type": "Dataset",
        "name": "DNF Operation Data Dependencies",
        "description": "Metadata describing the data outputs required by DNF operations for resolution."
    }))

    interface_crate_path = "interface.crate"
    if not os.path.isdir(interface_crate_path):
        raise Exception(f"{interface_crate_path} directory is missing.")


    nested_interface_crate = crate.add(Dataset(crate, os.path.basename(interface_crate_path), properties={
        "name": "Interface Crate",
        "description": "Nested interface.crate containing Experiment Infrastructure execution data.",
        "license": "https://creativecommons.org/licenses/by/4.0/"
    }))

    wrapper["hasPart"] = [nested_interface_crate]
    return wrapper

def add_main_article(crate):
    main_article = crate.add(ContextEntity(crate, "#research-article", properties={
        "@type": "ScholarlyArticle",
        "name": "LivePublication: A Dynamic and Reproducible Research Article",
        "description": "Human-Readable, compiled article generated from dynamic inputs, code, and narrative."
    }))

    html_article = crate.add_file("docs/publication/research_article.html", properties={
        "@type": "MediaObject",
        "name": "LivePublication HTML View",
        "description": "HTML-rendered version of the LivePublication article.",
        "encodingFormat": "text/html"
    })

    markdown_article = crate.add_file("docs/publication/research_article.md", properties={
        "@type": "MediaObject",
        "name": "LivePublication Markdown Source",
        "description": "Markdown-rendered version of the LivePublication article.",
        "encodingFormat": "text/markdown"
    })

    main_article["hasPart"] = [html_article, markdown_article]

    crate.mainEntity = main_article
    return main_article

def create_publication_crate(crate_name: str):
    crate = ROCrate()

    main_article = add_main_article(crate)

    add_dnf_engine_spec(crate)

    add_dnf_evaluated_document(crate)
    add_dnf_presentation_env(crate)

    # Establish isBasedOn relationships
    crate.get("#dnf-evaluated-document")["isBasedOn"] = [
        crate.get("#dnf-document"),
        crate.get("#dnf-data-dependencies"),
        crate.get("#dnf-engine")
    ]

    crate.get("#dnf-presentation-environment")["isBasedOn"] = [
        crate.get("#dnf-engine")
    ]

    crate.get("#dnf-engine")["isBasedOn"] = [
        crate.get("#dnf-engine-specification")
    ]

    crate.get("#research-article")["isBasedOn"] = [
        crate.get("#dnf-evaluated-document"),
        crate.get("#dnf-presentation-environment")
    ]

    # Add the specified relationships
    crate.get("#dnf-evaluated-document")["conformsTo"] = crate.get("#dnf-engine-specification")

    crate.get("#research-article")["wasGeneratedBy"] = crate.get("#dnf-presentation-environment")

    crate.get("#dnf-document")["conformsTo"] = crate.get("#dnf-schema")

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