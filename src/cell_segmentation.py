#!/usr/bin/env python3
"""
segmentation.py
----------------
Generalized CLI and module-compatible script for running cell segmentation
on OME-TIFF images using the CellSAM pipeline.

Simplified version without channel-axis inference — assumes the channel
dimension is the first axis (0) unless your data structure differs.

Usage (CLI):
    python segmentation.py --input_dir /path/to/input --output_name mask_output.tiff

Expected directory structure:
    /path/to/input/
        ├── <image>.ome.tiff
        └── config.yaml

The config.yaml file must specify:
    image_path: "reg001_expr.ome.tiff"
    use_wsi: true
    channels:
      - name: "ChannelA_name"
        number: 0
      - name: "ChannelB_name"
        number: 48
"""

import argparse
import yaml
import tifffile
import imageio.v3 as iio
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from cellSAM import cellsam_pipeline


def run_segmentation(input_dir: str, output_path: str = None):
    """
    Run segmentation using an image and configuration file in the input directory.

    Args:
        input_dir (str): Path containing the .ome.tiff image and config.yaml
        output_path (str): Full path for the segmentation mask output (optional)
    
    Returns:
        str: Path to the saved segmentation mask
    """
    input_dir = Path(input_dir)
    config_path = None
    
    # Find config.yaml file (flexible naming)
    for file in input_dir.glob("*config.yaml"):
        config_path = file
        break
    
    if config_path is None or not config_path.exists():
        raise FileNotFoundError(f"Config file not found in: {input_dir}")

    # Load configuration
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    image_path = input_dir / config["image_path"]
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    use_wsi = config.get("use_wsi", True)
    print(f"Using WSI mode: {use_wsi}")

    # Load image
    img = iio.imread(image_path)
    print(f"Image loaded: shape={img.shape}, dtype={img.dtype}")

    # Parse channel configuration
    channels_cfg = config.get("channels", [])
    if len(channels_cfg) < 2:
        raise ValueError("Config must specify at least two channels under 'channels'.")

    ch_a_idx = int(channels_cfg[0]["number"])
    ch_b_idx = int(channels_cfg[1]["number"])
    ch_a_name = channels_cfg[0]["name"]
    ch_b_name = channels_cfg[1]["name"]

    print("Selected channels:")
    print(f"  - {ch_a_name} (index={ch_a_idx})")
    print(f"  - {ch_b_name} (index={ch_b_idx})")

    # Extract channel planes
    channel_a = img[ch_a_idx, 0, :, :]
    channel_b = img[ch_b_idx, 0, :, :]   

    if channel_a.shape != channel_b.shape:
        raise ValueError(f"Channel shape mismatch: {channel_a.shape} vs {channel_b.shape}")

    print(f"Extracted channels shape: {channel_a.shape}")

    # Prepare 3-channel image for segmentation
    blank = np.zeros_like(channel_a)
    input_img = np.stack([blank, channel_a, channel_b], axis=-1)
    print(f"Prepared RGB image for segmentation: {input_img.shape}")

    # Run CellSAM segmentation
    print("⚙️  Running segmentation...")
    mask = cellsam_pipeline(
        input_img,
        use_wsi=use_wsi,
        low_contrast_enhancement=True,
        gauge_cell_size=False
    )

    # Save output
    if output_path is None:
        output_path = input_dir / "segmentation_mask.tiff"
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tifffile.imwrite(output_path, mask)
    print(f"✅ Segmentation completed. Output saved to: {output_path}")

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Run generalized cell segmentation on OME-TIFF images.")
    parser.add_argument("--input_dir", type=str, required=True,
                        help="Directory containing the .ome.tiff image and config.yaml")
    parser.add_argument("--output_path", type=str, default=None,
                        help="Output path for the segmentation mask")

    args = parser.parse_args()
    run_segmentation(args.input_dir, args.output_path)


if __name__ == "__main__":
    main()