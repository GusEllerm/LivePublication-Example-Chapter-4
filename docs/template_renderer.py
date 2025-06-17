import os
from jinja2 import Environment, FileSystemLoader
import json
import re
import html

def update_description_and_name_in_preview(crate_html_path, new_description):
    with open(crate_html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the JSON-LD script block
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', content, re.DOTALL)
    if not match:
        return

    raw_json = html.unescape(match.group(1)).strip()
    raw_json = re.sub(r'[\x00-\x1F\x7F]', '', raw_json)
    try:
        decoded_json = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON-LD from {crate_html_path}:\n{e}")
        print("Offending JSON snippet:")
        print(raw_json[:500])
        return
    for entity in decoded_json.get("@graph", []):
        if entity.get("@id") == "./":
            entity["description"] = new_description
            if "provenance_output.crate" in crate_html_path:
                entity["name"] = "Workflow Provenance Record (CWL Execution)"
            elif "interface.crate" in crate_html_path:
                entity["name"] = "LivePublication Experiment Interface Crate"
            break

    updated_json_str = json.dumps(decoded_json, indent=2)
    updated_script = f'<script type="application/ld+json">\n{updated_json_str}\n</script>'
    content = re.sub(r'<script type="application/ld\+json">.*?</script>', updated_script, content, flags=re.DOTALL)

    with open(crate_html_path, "w", encoding="utf-8") as f:
        f.write(content)

def render_crate_page(crate_html_path, output_html_path, title):
    with open(crate_html_path, "r", encoding="utf-8") as f:
        crate_html = f.read()

    env = Environment(loader=FileSystemLoader("docs/templates"))
    template = env.get_template("base.html")
    rendered = template.render(title=title, content=crate_html)

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(rendered)

if __name__ == "__main__":
    crates = [
        {
            "input": "provenance_output.crate/ro-crate-preview.html",
            "output": "docs/provenance.html",
            "title": "Provenance Crate"
        },
        {
            "input": "interface.crate/ro-crate-preview.html",
            "output": "docs/interface.html",
            "title": "Interface Crate"
        },
        {
            "input": "provenance_output.crate/ro-crate-preview.html",
            "output": "docs/index.html",
            "title": "Provenance Crate"
        }
    ]

    for crate in crates:
        if os.path.exists(crate["input"]):
            if "provenance_output.crate" in crate["input"]:
                update_description_and_name_in_preview(crate["input"], "Represents the provenance of the CWL workflow execution")
            elif "interface.crate" in crate["input"]:
                update_description_and_name_in_preview(crate["input"], "Containerises the Experiment Infrastructure outputs for LivePublication")
            render_crate_page(crate["input"], crate["output"], crate["title"])
        else:
            print(f"Warning: {crate['input']} does not exist.")