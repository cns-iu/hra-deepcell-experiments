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

---

## 🌐 HuBMAP GLOBUS API Setup

To enable data access from the [HuBMAP Data Portal](https://docs.hubmapconsortium.org/apis.html) or interact programmatically with the **Search & Index API**, follow these steps for Globus authentication.

### ✅ 1. Install Atlas Consortia Command Line Tools
```bash
pip install atlas-consortia-clt
```

### ✅ 2. Authenticate using Globus CLI
```bash
globus login --no-local-server
```
Copy the link shown in the terminal, open it in your browser, complete the authentication, and authorize Globus access.

To verify authentication:
```bash
globus whoami --verbose
```

---

### ✅ 3. Create `manifest.txt` file

Follow the [HuBMAP Manifest File Documentation](https://docs.hubmapconsortium.org/clt/index.html#manfiles) to create a `manifest.txt` file listing the dataset(s) to download.  
⚠️ **Important:** Ensure that there are **no comments** in the manifest file, as they may cause parsing errors.

---

### ✅ 4. Install and Configure Globus Connect Personal

Refer to [How To Install, Configure, and Uninstall Globus Connect Personal for Linux](https://docs.globus.org/globus-connect-personal/install/linux/).  
You can also download it directly using:

```bash
wget https://downloads.globus.org/globus-connect-personal/linux/stable/globusconnectpersonal-latest.tgz
```

Extract and navigate into the directory:
```bash
tar -xzf globusconnectpersonal-latest.tgz
cd globusconnectpersonal-x.y.z
```
*(Replace `x.y.z` with the extracted version number.)*

Start Globus Connect Personal for the first time:
```bash
./globusconnectpersonal -start &
```
Complete setup as prompted. After setup, exit the directory:
```bash
cd ..
```

---

### ✅ 5. Transfer Data using HuBMAP CLI

Once authenticated and your `manifest.txt` is ready, you can transfer HuBMAP data using:

```bash
hubmap-clt transfer manifest.txt
```

This will initiate a secure data transfer using Globus.


### ⚠️ 5.1. Common Error: “Session reauthentication required”

You may see this message:
```
The resource you are trying to access requires you to re-authenticate.
Session reauthentication required (Globus Transfer)
```

### Fix: Re-authenticate Globus CLI

The CLI will provide a command like:

```
globus session update <SESSION-ID>
```

*You have successfully updated your CLI session.

### ⚠️ Common Error: “Markers are extracted from the .ome.tiff metadata and not the pipeline_config.json due to mismatch size”

---

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
- [HuBMAP API Reference](https://docs.hubmapconsortium.org/apis.html)  
- [HuBMAP CLT Guide](https://docs.hubmapconsortium.org/clt/index.html#manfiles)

---
