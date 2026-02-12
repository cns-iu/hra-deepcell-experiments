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
   ```bash  (prefer Python version >= 3.12 )
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
hubmap-clt transfer manifest.txt -d /teradata/username/deepcell-experiments-data/intestine-codex-stanford
```

This will initiate a secure data transfer using Globus.
#### Bonus Tip: Run the download on `Screen` command to ensure good sleep at night.


### 5.1. Common Error: “Session reauthentication required”

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



### ✅ 6. Run the Scripts

Once you have your Input csv of the data with the parent hubmap id's. 
Get inside the scripts folder and any one of the folder of datasets eg. Thymus”

Steps: 
1. Using Parent Hubmap ID  derive Descendents ID using (00_hubmap-id_desc.py)
2. Create Manifest.txt Files for each dataset using (01_manifest_creation.py)
3. Create config files once you have downloaded the data in the 'data-original' using step 5 command . 
4. Now you are ready to run the inferencing which will do both `segmentation` and `annotation` in one step. 


###  6.1.   Creation of Descendents.

This block finds the descendent hubmap id which is required to download the descendents `pipeline.json` and `.ome.tiff` files. 
```
python3 00_hubmap-id_desc.py
```

#### ⚠️ Remember: “Some Parents will not have descendents, so no need to remove them from the csv file”

###  6.2.   Creation of `Manifest.txt`.

This block helps create the manifest file which is to be downloaded by globus for each hubmap id 
```
python3 01_manifest_creation.py
```

#### Note:  The files which do not have descendent will automatically be taken care of. 

###  6.3.   Download `Manifest.txt` contents.

Read the `Globus.md` for more information related to common errors.
```
hubmap-clt transfer manifest.txt -d /teradata/username/deepcell-experiments-data/intestine-codex-stanford/data-original/
```
#### Bonus Tip   1: Don't forget to run the `Screen` command.


###  6.4.   Creation `config.yaml` and clean file structure names in .

this will create a config.yaml file which has the `nucleus_channel` and `cell_channel` and a renamed file structure in input-data
```
python3 02_hubmap-config.py
```

###  6.5.   Final Step: Run inferencing on the input-data (Segmentation + Annotation):

Navigate to teh `src` file to run this for output. Which takes two things as an input :
a. the input file location
b. the output file location

```
python run_inference_pipeline.py --input_root /teradata/sbdubey/deepcell-experiments-data/intestine-codex-stanford/input-data/ --output_root /teradata/sbdubey/deepcell-experiments-data/intestine-codex-stanford/output-data/
```
#### ⚠️ Remember: “Some data will have missing `nucleus_channel`so the segmentation process will not work for those cases and skip to next example. 
#### Bonus Points 1: The code run segmentation -> Annotation for a single example then for next, next .... 
#### Bonus Point  2: To run two seperate process on GPU make sure to run the command with 👇 on two seperate `Screen`
```
CUDA_VISIBLE_DEVICES=0 python run_inference_pipeline.py ... &
CUDA_VISIBLE_DEVICES=1 python run_inference_pipeline.py ...
```
---


### ✅  For API of Descendents follow the steps:

#### ⚠️ Remember: You need to be the member of HuBMAP for using this Token

1. [Login to HuBMAP](https://portal.hubmapconsortium.org/search/datasets?N4IgzgxgYglgdgEwAoEMBOKC2YQC5gC+BQA)
2. [Right click on the EUI portal and click Inspect](https://portal.hubmapconsortium.org/ccf-eui)
3. Copy the Code of token (after Token= until before `&` ) eg: token=`AgzPl9yNgdeQlbadgzvPjq0d89OMgJM56ql0lMeW6K7Ddw9m7MfkClj13rpknp4Go0nPYm0N9xxv2Pxxxxxxxxxxxxxx`&quot;
4. Paste this the `00_hubmap-id_desc.py` 

#### ⚠️ Remember: The Token expires in some time so re-do the same process again. 


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
