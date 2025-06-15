#!/bin/bash

set -e  # Exit on any error

# Step 0: Clean the project directory
echo "🧹 Cleaning project directory..."
rm -rf Workflow_inputs/Data/*
find . -maxdepth 1 -name "*.pickle" -delete
find . -maxdepth 1 -name "*.tif" -delete

# Step 1: Download new Copernicus data and patch workflow inputs
echo "🛰️ Downloading Copernicus data and patching workflow input..."
python copernicus_data.py

# Step 2: Run the CWL workflow with provenance tracking
echo "▶️ Running CWL workflow..."
cwltool --strict-memory-limit --provenance provenance_output Workflows/workflow.cwl Workflow_inputs/GNDVI_10m.yaml

# Step 3: Generate the Provenance Run Crate
echo "📦 Converting to Provenance Run Crate..."
runcrate convert provenance_output

# Step 4: Generate the HTML website from the crate
echo "🌐 Generating HTML preview of the provenance crate..."
rochtml provenance_output.crate/ro-crate-metadata.json

# Step 5: Copy the preview HTML to your GitHub Pages docs/
echo "📁 Copying preview HTML to docs/index.html..."
mkdir -p docs
cp provenance_output.crate/ro-crate-preview.html docs/index.html

# Step 6: Run your Zenodo upload script
echo "☁️ Uploading new version to Zenodo..."
python zenodo_upload.py

# Step 7: Generate the Interface Crate and zip it
echo "🧬 Generating Interface Crate..."
python interface_crate.py
zip -r interface.crate.zip interface.crate

# Step 8: Commit and push to GitHub
echo "📤 Committing and pushing to GitHub..."
git add .
git commit -m "Automated publish: new CWL run, crate, and Zenodo version"
git push

echo "✅ Done. Your pipeline has been published and pushed!"