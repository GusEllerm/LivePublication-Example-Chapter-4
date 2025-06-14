# #!/bin/bash
# set -e  # Exit on any error

# # Step 1: Run the CWL workflow with provenance tracking
# echo "▶️ Running CWL workflow..."
# cwltool --strict-memory-limit --provenance provenance_output Workflows/workflow.cwl Workflow_inputs/GNDVI_10m.yaml

# # Step 2: Generate the Provenance Run Crate
# echo "📦 Converting to Provenance Run Crate..."
# runcrate convert provenance_output

# # Step 3: Generate the HTML website from the crate
# echo "🌐 Generating HTML preview of the provenance crate..."
# rochtml provenance_output.crate/ro-crate-metadata.json

# # Step 4: Copy the preview HTML to your GitHub Pages docs/
# echo "📁 Copying preview HTML to docs/index.html..."
# mkdir -p docs
# cp provenance_output.crate/ro-crate-preview.html docs/index.html

# # Step 5: Run your Zenodo upload script
# echo "☁️ Uploading new version to Zenodo..."
# python zenodo_upload.py

# Step 6: Commit and push to GitHub
echo "📤 Committing and pushing to GitHub..."
git add .
git commit -m "Automated publish: new CWL run, crate, and Zenodo version"
git push

echo "✅ Done. Your pipeline has been published and pushed!"