# LivePublication example application (Chapter 4)

## What this is
This repository contains the Chapter 4 LivePublication example application used in the thesis to demonstrate the LivePublication Framework end-to-end. It implements a CWL-based experiment infrastructure, generates provenance and interface crates, and renders a LivePaper-style publication using a dynamic narrative workflow. The example computes the GNDVI vegetation index from Sentinel-2 data and produces a rendered research article from those results.

## What it demonstrates
- Experiment Infrastructure: CWL workflow execution with provenance capture.
- Interface: generation of provenance and interface RO-Crates for downstream use.
- LivePaper: dynamic narrative rendering into publication outputs using Stencila.
- Provenance handoff between workflow outputs and publication rendering.

## How to run
Prerequisites: Python 3, Docker (32 GB RAM recommended), CWL toolchain, Stencila CLI, and Node.js for crate HTML preview.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt rocrate runcrate
npm install -g ro-crate-html-js
./publish_pipeline.sh
```

## Outputs
- `provenance_output.crate.zip`: provenance run crate generated from the CWL workflow.
- `interface.crate.zip`: interface crate representing outputs consumed by the LivePaper.
- `publication.crate.zip`: publication crate for the rendered article.
- `docs/publication/research_article.html`: rendered publication output.
- `docs/index.html`: generated HTML site entry point.

## How to view
- Open `docs/index.html` in a browser to browse the rendered site locally.
- Open `docs/publication/research_article.html` directly to view the LivePaper output.
- Live demo: https://gusellerm.github.io/LivePublication-Example-Chapter-4/

## How to cite
Use `CITATION.cff` in this repository. A Zenodo DOI will be added after a GitHub Release is deposited.

## Related artefacts
- LivePublication Interface Schemas (DPC/DSC): https://doi.org/10.5281/zenodo.18250033

## License
Apache-2.0 (see `LICENSE`).
