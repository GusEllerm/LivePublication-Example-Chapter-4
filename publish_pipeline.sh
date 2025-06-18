#!/bin/bash

set -e  # Exit on any error

# Step 0: Clean the project directory
echo "🧹 Cleaning project directory..."
rm -rf Workflow_inputs/Data/*
find . -maxdepth 1 -name "*.pickle" -delete
find . -maxdepth 1 -name "*.tif" -delete
rm -rf interface.crate/ provenance_output/ provenance_output.crate/
rm -f DNF_document.json dynamic_article.json
rm -rf docs/publication/


# Step 1: Download new Copernicus data and patch workflow inputs
echo "🛰️ Downloading Copernicus data and patching workflow input..."
python copernicus_data.py

# Step 2: Run the CWL workflow with provenance tracking
echo "▶️ Running CWL workflow..."
cwltool --strict-memory-limit --provenance provenance_output Workflows/workflow.cwl Workflow_inputs/GNDVI_10m.yaml

# Step 3: Generate the Provenance Run Crate
echo "📦 Converting to Provenance Run Crate..."
runcrate convert provenance_output --output provenance_output.crate

# Step 4: Generate workflow preview image
echo "🖼️ Generating CWL workflow diagram..."
cwltool --print-dot provenance_output.crate/packed.cwl | dot -Tpng -o workflow_preview.png
cp workflow_preview.png provenance_output.crate/workflow_preview.png

# Step 5: Run your Zenodo upload script
echo "☁️ Uploading new version to Zenodo..."
python zenodo_upload.py

# Step 6: Generate the Interface Crate and zip it
echo "🧬 Generating Interface Crate..."
python interface_crate.py
zip -r interface.crate.zip interface.crate

# Step 7: Generate the HTML preview of the provenance crate
echo "🌐 Generating HTML preview of the provenance crate..."
rochtml provenance_output.crate/ro-crate-metadata.json

# Step 8: Generate HTML preview of the interface crate
echo "🌐 Generating HTML preview of the interface crate..."
rochtml interface.crate/ro-crate-metadata.json

# Step 9: Generate the templated website with navigation
echo "🧱 Generating templated HTML site..."
python docs/template_renderer.py

# Step 10: Generate the DNF Document from the dynamic_publication.smd specification
echo "📄 Generating DNF Document..."
stencila convert dynamic_publication.smd DNF_document.json

# Step 11: Render the DNF Document using the interface.crate
echo "📑 Rendering DNF Document with interface.crate..."
stencila render --no-save DNF_Document.json dynamic_article.json    

# Step 12: Create exmaple presentation verisons of the rendered article
echo "📊 Creating example presentation versions of the rendered article..."
stencila convert dynamic_article.json  docs/publication/dynamic_article.html
stencila convert dynamic_article.json docs/publication/dynamic_article.pdf

# Step 11: Commit and push to GitHub
echo "📤 Committing and pushing to GitHub..."
git add .
git commit -m "Automated publish: new CWL run, crate, and Zenodo version"
git push

echo "✅ Done. Your pipeline has been published and pushed!"