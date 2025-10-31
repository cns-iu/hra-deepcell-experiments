

import tifffile
import xml.etree.ElementTree as ET
import imageio.v3 as iio
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
import matplotlib.patches as patches

from cellSAM import cellsam_pipeline, get_model
from cellSAM.utils import format_image_shape, normalize_image



def segmentation_cli(channel, img):

    for i,j in channel:
        print('hi')




def readfile(iinput_dir: str, output_name: str):

    input_dir = Path(input_dir)
    config_path = input_dir / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # --- Step 1: Load configuration ---
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    image_path = input_dir / config["image_path"]
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    use_wsi = config.get("use_wsi", True)
    print(f" Using WSI mode: {use_wsi}")      
        
    # --- Step 2: Load image ---
    img = iio.imread(image_path)
    print(f" Image loaded: shape={img.shape}, dtype={img.dtype}")

    # --- Step 3: Parse channel configuration ---
    channels_cfg = config.get("channels", [])
    print()
    print(channels_cfg)
    print(f'Type of data {type(channels_cfg)}')
    print()
    if len(channels_cfg) < 2:
        raise ValueError("Config must specify at least two channels under 'channels'.")
    
    ch_a_idx = int(channels_cfg[0]["number"])
    ch_b_idx = int(channels_cfg[1]["number"])
    ch_a_name = channels_cfg[0]["name"]
    ch_b_name = channels_cfg[1]["name"]   

    

    print(" Selected channels:")
    print(f" - {ch_a_name} (index={ch_a_idx})")
    print(f" - {ch_b_name} (index={ch_b_idx})")  



