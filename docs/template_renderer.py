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
            elif "publication.crate" in crate_html_path:
                entity["name"] = "LivePublication Crate"
            break

    updated_json_str = json.dumps(decoded_json, indent=2)
    updated_script = f'<script type="application/ld+json">\n{updated_json_str}\n</script>'
    content = re.sub(r'<script type="application/ld\+json">.*?</script>', updated_script, content, flags=re.DOTALL)

    with open(crate_html_path, "w", encoding="utf-8") as f:
        f.write(content)

def render_crate_page(crate_html_path, output_html_path, title, content_override=None):
    if content_override is not None:
        crate_html = content_override
    else:
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
        },
        {
            "input": "publication.crate/ro-crate-preview.html",
            "output": "docs/publication.html",
            "title": "LivePublication Crate"
        }
    ]

    for crate in crates:
        if os.path.exists(crate["input"]):
            if "provenance_output.crate" in crate["input"]:
                update_description_and_name_in_preview(crate["input"], "Represents the provenance of the CWL workflow execution")
            elif "interface.crate" in crate["input"]:
                update_description_and_name_in_preview(crate["input"], "Containerises the Experiment Infrastructure outputs for LivePublication")
            elif "publication.crate" in crate["input"]:
                update_description_and_name_in_preview(crate["input"], "A complete and reproducible LivePublication instance including data, workflow, and narrative.")

            render_crate_page(crate["input"], crate["output"], crate["title"])
        else:
            print(f"Warning: {crate['input']} does not exist.")

    # Render research article as a standalone page
    research_article_input = "docs/publication/research_article.html"
    research_article_output = "docs/research_article.html"
    if os.path.exists(research_article_input):
        try:
            with open(research_article_input, "r", encoding="utf-8") as rf:
                article_html = rf.read()
            alert_html = (
                '<div class="alert-warning" style="border:1px solid #f5c6cb; background:#f8d7da; padding:10px; margin-bottom:20px;">'
                '<strong>Note:</strong> This embedded article is currently broken and waiting on downstream development.'
                '</div>'
            )
            # Removed alert_html from the article content as it is now rendering correctly. 
            full_content = article_html
            render_crate_page(research_article_input, research_article_output, "Research Article", content_override=full_content)
        except Exception as e:
            print(f"Warning: Could not render research article: {e}")
    else:
        print(f"Warning: {research_article_input} does not exist.")