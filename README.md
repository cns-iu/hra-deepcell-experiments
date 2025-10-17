# 🧬 HRA DeepCell Experiments

An integrated framework for **cell segmentation** and **cell type annotation** using [CellSAM](https://vanvalenlab.github.io/cellSAM/index.html) and [DeepCell Types](https://vanvalenlab.github.io/deepcell-types/site/tutorial.html).  
This repository provides reproducible pipelines for processing, segmenting, and classifying cells in multi-channel microscopy datasets.

---

## 🚀 Overview

This repository implements the following workflow:
1. **Segmentation** with *CellSAM* for identifying single cells in microscopy images.    
2. **Annotation** with *DeepCell Types* via API for cell identity prediction.  
3. **Output reports** with per-cell CSVs and visual summaries.

---

## ⚙️ Environment Setup

This project requires **Python 3.12**.  
You can create the environment using **Conda** or **pip/venv**, as described below.

---

### 🧩 Option 1: Using Conda

1. **Clone this repository**
   ```bash
   git clone https://github.com/cns-iu/hra-deepcell-experiments.git
   cd hra-deepcell-experiments
   ```

2. **Create and activate the environment**
   ```bash
   conda create -n hra-deepcell python=3.12
   conda activate hra-deepcell
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install git+https://github.com/vanvalenlab/cellSAM.git
   pip install git+https://github.com/vanvalenlab/deepcell-types@master
   ```

---

### 🧩 Option 2: Using pip (without Conda)

If you’re not using Conda, you can create a standard virtual environment:

1. **Create and activate the environment**
   ```bash
   python3.12 -m venv hra-deepcell
   source hra-deepcell/bin/activate       # On Mac/Linux
   hra-deepcell\Scripts\activate          # On Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install git+https://github.com/vanvalenlab/cellSAM.git
   pip install git+https://github.com/vanvalenlab/deepcell-types@master
   ```

---

## 🔑 DeepCell API Configuration

Before running DeepCell for cell type predictions, configure your API access token.

1. Go to [DeepCell API Key Management](https://deepcell.readthedocs.io/en/master/API-key.html).  
2. Log in and **generate a new API key**.  
3. Save the token using one of the following methods.

---

### ✅ Option 1: Save permanently to Conda environment
```bash
conda env config vars set -n hra-deepcell DEEPCELL_ACCESS_TOKEN=<your-token>
conda deactivate && conda activate hra-deepcell
```

---

### ✅ Option 2: Save permanently for pip users (system environment variable)

**On Mac/Linux:**
```bash
export DEEPCELL_ACCESS_TOKEN=<your-token>
```

**On Windows (PowerShell):**
```bash
setx DEEPCELL_ACCESS_TOKEN "<your-token>"
```

**On Windows (CMD):**
```bash
set DEEPCELL_ACCESS_TOKEN=<your-token>
```

> 💡 Restart your terminal or IDE after setting the environment variable.

---

### ✅ Option 3: Temporary session variable in Python
```python
import os
os.environ["DEEPCELL_ACCESS_TOKEN"] = "<your-token>"
```

<!-- ---

## 🧩 Running the Workflow

### 1. **Prepare Input Data**

Place microscopy images under:
```
input-data/img_test/
├── img.ome.tif
├── config.yaml
```

### 2. **Run Cell Segmentation**
```bash
python src/cell_segmentation.py --input input-data/img_test/img.ome.tif --output output-data/img_test/
```

Outputs include:
- `mask.tif` — segmented cells  
- `cell_populations.csv` — per-cell metrics  

### 3. **Run Cell Annotation**
```bash
python src/cell_annotation.py --input output-data/img_test/cell_populations.csv --output output-data/img_test/
```

This step communicates with the **DeepCell API** to classify cell types.

### 4. **Generate Final Report**
```bash
python src/run_inference_pipeline.py --input output-data/img_test/ --output output-data/img_test/
```

Output includes:
- `cell_types.csv` — predicted cell types  
- `cell_report.json` — summary statistics  

---

## 📂 Directory Structure

```
hra-deepcell-experiments/
├── scripts/
│   ├── setup.sh                      # Environment setup script
│   └── download_hubmap_data.sh       # Optional: Download HuBMAP data
│
├── nbs/
│   ├── tutorial_cellsam_deepcelltypes.ipynb  # Guided pipeline tutorial
│   └── hubmap_cellsam_deepcelltypes.ipynb    # HuBMAP example workflow
│
├── src/
│   ├── __init__.py
│   ├── cell_segmentation.py          # Runs CellSAM segmentation
│   ├── cell_annotation.py            # DeepCell Types annotation
│   ├── dataset.py                    # Data loader utilities
│   ├── utils.py                      # Helper functions
│   └── run_inference_pipeline.py     # Full segmentation + annotation pipeline
│
├── input-data/
│   └── img_test/
│       ├── img.ome.tif
│       └── config.yaml
│
├── output-data/
│   └── img_test/
│       ├── mask.tif
│       ├── cell_types.csv
│       ├── cell_populations.csv
│       └── cell_report.json
│
└── README.md
```

--- -->

## 📊 Expected Outputs

After a successful run, you will obtain:
- **`mask.tif`** — labeled segmentation masks  
- **`cell_populations.csv`** — morphological cell metrics  
- **`cell_types.csv`** — annotated cell types  
  

---

## 🧠 References

- [CellSAM Documentation](https://vanvalenlab.github.io/cellSAM/tutorial.html)  
- [DeepCell Types Tutorial](https://vanvalenlab.github.io/deepcell-types/site/tutorial.html)  
- [DeepCell API Setup](https://deepcell.readthedocs.io/en/master/API-key.html)

---


