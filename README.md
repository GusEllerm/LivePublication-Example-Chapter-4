# CWL Provenance RunCrate Demo

This repository demonstrates a **reproducible, transparent workflow execution** using the Common Workflow Language (CWL), including the **generation of a PROV-compliant Provenance Run Crate** and an interactive HTML website to inspect results.

The example workflow calculates a vegetation index (e.g., GNDVI) from Sentinel-2 satellite bands using Python and CWL. 

![Workflow Diagram](workflow.png)

---

## 📦 Contents

```
.
├── Workflows/             	# CWL workflow 
├── Workflows/Modules/          # CWL tool definitions
├── Workflows/Modules/Scripts/  # Python scripts used in the workflow
├── Workflow_inputs/       	# YAML job file
├── Workflow_inputs/Data/     	# Example sentinal-2 data
├── provenance_output/     	# provenance generated via `cwltool --provenance provenance_output Workflows/workflow.cwl Workflow_inputs/GNDVI_10m.yaml`  
└── provenance_output.crate/    # Workflow Run Crate genearted via `runcrate convert provenance_output`   
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. Create and activate a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install cwltool rocrate runcrate
```

---

## 🔁 Run the CWL Workflow

```bash
cwltool --provenance provenance_output Workflows/workflow.cwl Workflow_inputs/GNDVI_10m.yaml
```

This will:

- Run the CWL workflow
- Generate a provenance directory at `provenance_output/`

---

## 🔄 Convert to Workflow Run Crate

```bash
runcrate convert provenance_output
```

---

## 🌐 Create Crate Website

Install via npx (requires Node.js and npm):

```bash
npx ro-crate-html-js --directory provenance_output
```

To preview locally:

```bash
open provenance_output/index.html
```

---

## 📚 References

- [Common Workflow Language](https://www.commonwl.org/)
- [RO-Crate](https://www.researchobject.org/ro-crate/)
- [runcrate](https://github.com/ResearchObject/runcrate)
- [ro-crate-html-js](https://www.npmjs.com/package/ro-crate-html-js)

---

## 📄 License

MIT License.
