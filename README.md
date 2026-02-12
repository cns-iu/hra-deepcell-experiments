# 🧬 HRA DeepCell Experiments

An integrated framework for **cell segmentation** and **cell type annotation** using [CellSAM](https://vanvalenlab.github.io/cellSAM/index.html) and [DeepCell Types](https://vanvalenlab.github.io/deepcell-types/site/tutorial.html).

This repository provides reproducible pipelines for processing, segmenting, and classifying cells in multi-channel microscopy datasets.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Prerequisites](#-prerequisites)
- [Environment Setup](#️-environment-setup)
- [API Configuration](#-api-configuration)
  - [DeepCell API](#deepcell-api)
  - [HuBMAP Globus API](#hubmap-globus-api)
- [Workflow](#-workflow)
- [Expected Outputs](#-expected-outputs)
- [Troubleshooting](#-troubleshooting)
- [References](#-references)

---

## 🚀 Overview

This repository implements an end-to-end workflow for microscopy image analysis:

1. **Segmentation** — Identify individual cells using *CellSAM*
2. **Annotation** — Predict cell types using *DeepCell Types* API
3. **Reporting** — Generate per-cell CSVs and visual summaries

---

## 📋 Prerequisites

- **Python 3.12+** (required)
- **Conda** or **pip/venv** for environment management
- **DeepCell API token** (for cell type annotation)
- **Globus account** (for HuBMAP data access)
- **GPU recommended** (for faster inference)

---

## ⚙️ Environment Setup

### Option 1: Using Conda (Recommended)

```bash
# Clone the repository
git clone https://github.com/cns-iu/hra-deepcell-experiments.git
cd hra-deepcell-experiments

# Create and activate conda environment
conda create -n hra-deepcell python=3.12
conda activate hra-deepcell

# Install dependencies
pip install -r requirements.txt
pip install git+https://github.com/vanvalenlab/cellSAM.git
pip install git+https://github.com/vanvalenlab/deepcell-types@master
```

### Option 2: Using pip/venv

```bash
# Create and activate virtual environment
python3.12 -m venv hra-deepcell

# Activate environment
source hra-deepcell/bin/activate       # macOS/Linux
hra-deepcell\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt
pip install git+https://github.com/vanvalenlab/cellSAM.git
pip install git+https://github.com/vanvalenlab/deepcell-types@master
```

---

## 🔑 API Configuration

### DeepCell API

**Step 1:** Obtain your API token

1. Visit [DeepCell API Key Management](https://deepcell.readthedocs.io/en/master/API-key.html)
2. Log in and generate a new API key
3. Copy the token

**Step 2:** Configure the token (choose one method)

**A. For Conda users (persistent):**
```bash
conda env config vars set -n hra-deepcell DEEPCELL_ACCESS_TOKEN=<your-token>
conda deactivate && conda activate hra-deepcell
```

**B. For system environment (persistent):**

*macOS/Linux:*
```bash
export DEEPCELL_ACCESS_TOKEN=<your-token>
# Add to ~/.bashrc or ~/.zshrc for persistence
```

*Windows PowerShell:*
```powershell
setx DEEPCELL_ACCESS_TOKEN "<your-token>"
```

*Windows CMD:*
```cmd
set DEEPCELL_ACCESS_TOKEN=<your-token>
```

**C. In Python (temporary):**
```python
import os
os.environ["DEEPCELL_ACCESS_TOKEN"] = "<your-token>"
```

> 💡 **Note:** Restart your terminal or IDE after setting environment variables.

---

### HuBMAP Globus API

#### 1. Install Atlas Consortia CLI Tools

```bash
pip install atlas-consortia-clt
```

#### 2. Authenticate with Globus

```bash
globus login --no-local-server
```

Follow the authentication link in your browser and authorize access.

**Verify authentication:**
```bash
globus whoami --verbose
```

#### 3. Install Globus Connect Personal

Download and install Globus Connect Personal:

```bash
wget https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
tar -xzf globusconnectpersonal-latest.tgz
cd globusconnectpersonal-*
./globusconnectpersonal -start &
```

Follow the setup prompts. For detailed instructions, see [Globus Connect Personal for Linux](https://docs.globus.org/globus-connect-personal/install/linux/).

#### 4. Create Manifest File

Create a `manifest.txt` file following the [HuBMAP Manifest File Documentation](https://docs.hubmapconsortium.org/clt/index.html#manfiles).

⚠️ **Important:** Ensure the manifest file contains **no comments**, as they may cause parsing errors.

#### 5. Transfer Data

```bash
hubmap-clt transfer manifest.txt -d /path/to/destination/data-original/
```

> 💡 **Tip:** Use `screen` or `tmux` to run long transfers in the background:
> ```bash
> screen -S hubmap-transfer
> hubmap-clt transfer manifest.txt -d /path/to/destination/
> # Press Ctrl+A, then D to detach
> ```

#### 6. Troubleshooting: Session Re-authentication

If you see `"Session reauthentication required"`, run:

```bash
globus session update <SESSION-ID>
```

Follow the prompts to re-authenticate.

---

## 🔄 Workflow

Navigate to the `scripts/` folder corresponding to your dataset (e.g., `scripts/thymus/`).

### Step 1: Generate Descendant IDs

Extract descendant HuBMAP IDs from parent IDs:

```bash
python3 00_hubmap-id_desc.py
```

**Input:** CSV file with parent HuBMAP IDs  
**Output:** CSV with descendant IDs

> ⚠️ **Note:** Some parent IDs may not have descendants — this is expected and handled automatically.

#### Obtaining HuBMAP API Token

To use the API:

1. [Login to HuBMAP Portal](https://portal.hubmapconsortium.org/search/datasets)
2. Navigate to the [CCF-EUI Portal](https://portal.hubmapconsortium.org/ccf-eui)
3. Right-click → Inspect → Network tab
4. Find a request and copy the token from `token=...&` in the URL
5. Paste the token in `00_hubmap-id_desc.py`

> ⚠️ **Note:** Tokens expire periodically. Repeat this process if authentication fails.

### Step 2: Create Manifest Files

Generate `manifest.txt` files for each dataset:

```bash
python3 01_manifest_creation.py
```

Datasets without descendants are automatically skipped.

### Step 3: Download Data

Transfer data using Globus:

```bash
hubmap-clt transfer manifest.txt -d /path/to/data-original/
```

> 💡 **Tip:** Run in a `screen` session for long downloads.

### Step 4: Generate Configuration Files

Create `config.yaml` files with channel information:

```bash
python3 02_hubmap-config.py
```

This script:
- Extracts `nucleus_channel` and `cell_channel` from pipeline metadata
- Restructures file names in `input-data/`
- Generates configuration files for inference

### Step 5: Run Inference Pipeline

Navigate to the `src/` directory and run:

```bash
python run_inference_pipeline.py \
    --input_root /path/to/input-data/ \
    --output_root /path/to/output-data/
```

**What happens:**
1. **Segmentation** — CellSAM identifies cell boundaries
2. **Annotation** — DeepCell Types predicts cell types
3. **Output generation** — Masks, CSVs, and summaries are saved

> ⚠️ **Note:** Datasets missing `nucleus_channel` will be automatically skipped.

#### Running Multiple GPU Processes

To utilize multiple GPUs simultaneously:

```bash
# Terminal 1 (GPU 0)
CUDA_VISIBLE_DEVICES=0 python run_inference_pipeline.py \
    --input_root /path/to/input-data-1/ \
    --output_root /path/to/output-data-1/ &

# Terminal 2 (GPU 1)
CUDA_VISIBLE_DEVICES=1 python run_inference_pipeline.py \
    --input_root /path/to/input-data-2/ \
    --output_root /path/to/output-data-2/
```

> 💡 **Tip:** Run each command in a separate `screen` session.

---

## 📊 Expected Outputs

After a successful run, each dataset will produce:

```
output-data/
├── <dataset-id>/
│   ├── mask.tif                    # Segmentation masks
│   ├── cell_populations.csv        # Morphological metrics
│   ├── cell_types.csv              # Cell type annotations
```

**File descriptions:**
- **`mask.tif`** — Labeled instance segmentation masks
- **`cell_populations.csv`** — Per-cell morphological features (area, perimeter, etc.)
- **`cell_types.csv`** — Cell type predictions with confidence scores

---

## 🛠️ Troubleshooting

### Common Issues

**Issue:** `ModuleNotFoundError: No module named 'cellSAM'`  
**Solution:** Ensure you installed CellSAM from source:
```bash
pip install git+https://github.com/vanvalenlab/cellSAM.git
```

**Issue:** `DeepCell API authentication failed`  
**Solution:** Verify your token is set correctly:
```bash
echo $DEEPCELL_ACCESS_TOKEN
```

**Issue:** `CUDA out of memory`  
**Solution:** Reduce batch size or process fewer images at once. Use `CUDA_VISIBLE_DEVICES` to assign specific GPUs.

**Issue:** Globus transfer stalls  
**Solution:** Ensure Globus Connect Personal is running:
```bash
./globusconnectpersonal -status
```

**Issue:** Missing nucleus channel  
**Solution:** This is expected for some datasets. The pipeline will automatically skip them and continue.

---

### 📌 Results Comparison with [hubmap-mirror-data-api](https://github.com/hubmapconsortium/hubmap-mirror-data-api)

Use the two scripts from the `scripts` folder:

1. **`getsample.py`** – Reads HuBMAP Zarr archives from S3, extracts the `cell_types/predictions` attribute (`hubmap_dct`) from each dataset, converts it to a DataFrame with `cell_type` and `CL_id` columns, and writes one CSV per dataset to `ross_results/`. Skips datasets missing the required attribute and logs errors.

2. **`preprocess.py`** – Processes each CSV in `ross_results/`, counts cells per `cell_type`, calculates percentages, sorts by count descending, and outputs summary CSVs to `processed_ross/` with cleaned filenames (e.g., `*_deepcell_population.csv`).

---

## 🧠 References

- **CellSAM:** [Documentation](https://vanvalenlab.github.io/cellSAM/tutorial.html) | [GitHub](https://github.com/vanvalenlab/cellSAM)
- **DeepCell Types:** [Tutorial](https://vanvalenlab.github.io/deepcell-types/site/tutorial.html) | [GitHub](https://github.com/vanvalenlab/deepcell-types)
- **DeepCell API:** [Setup Guide](https://deepcell.readthedocs.io/en/master/API-key.html)
- **HuBMAP:** [API Reference](https://docs.hubmapconsortium.org/apis.html) | [CLI Guide](https://docs.hubmapconsortium.org/clt/index.html)
- **Globus:** [Connect Personal Installation](https://docs.globus.org/globus-connect-personal/install/linux/)

---




