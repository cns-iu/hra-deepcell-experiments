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
You can create the environment using either **Conda** or **venv**, as described below.

### 🧩 Option 1: Using Conda

1. **Clone this repository**
   ```bash
   git clone https://github.com/<your-username>/hra-deepcell-experiments.git
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

### 🧩 Option 2: Using Python Virtual Environment (venv)

1. **Create and activate the environment**
   ```bash
   python3.12 -m venv hra-deepcell
   source hra-deepcell/bin/activate       # On Mac/Linux
   hra-deepcell\Scripts\activate        # On Windows
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
3. Save the token using one of the methods below.

### Option 1: Save the token permanently to Conda environment
```bash
conda env config vars set -n hra-deepcell DEEPCELL_ACCESS_TOKEN=<your-token>
# reload the environment to pick up the token
conda deactivate && conda activate hra-deepcell
```

### Option 2: Set temporarily in your Python session
```python
import os
os.environ["DEEPCELL_ACCESS_TOKEN"] = "<your-token>"
```



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

## 👥 Authors

**Satyam Dubey**, **Yash**, and collaborators  
📧 sbdubey@iu.edu  
