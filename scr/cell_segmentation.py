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


# --------------------------------------------------------------------------- #
#                            Helper functions                                 #
# --------------------------------------------------------------------------- #
def _extract_2d_channel(img, channel_axis, channel_index):
    """
    Extract a single 2D channel image from a potentially multi-dimensional OME-TIFF.

    Args:
        img (ndarray): Input image (N-D)
        channel_axis (int): Axis corresponding to channels
        channel_index (int): Index of the desired channel

    Returns:
        2D ndarray: Extracted (Y, X) image
    """
    if channel_index >= img.shape[channel_axis]:
        raise IndexError(
            f"Channel index {channel_index} out of bounds for axis {channel_axis} (size={img.shape[channel_axis]})"
        )

    # Build a slicing selector
    selector = [slice(None)] * img.ndim
    selector[channel_axis] = int(channel_index)

    # If extra axes exist (Z, T, etc.), select the first frame
    for ax in range(img.ndim - 2):  # skip last two (Y, X)
        if ax == channel_axis:
            continue
        if img.shape[ax] > 1:
            selector[ax] = 0

    arr = np.squeeze(img[tuple(selector)])
    if arr.ndim != 2:
        arr = arr.reshape(arr.shape[-2], arr.shape[-1])

    print(f" Extracted channel {channel_index} shape: {arr.shape}")
    return arr


# --------------------------------------------------------------------------- #
#                            Core Segmentation Logic                          #
# --------------------------------------------------------------------------- #
def run_segmentation(input_dir: str, output_name: str):
    """
    Run segmentation using an image and configuration file in the input directory.

    Args:
        input_dir (str): Path containing the .ome.tiff image and config.yaml
        output_name (str): Name for the segmentation mask output
    """
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
    if len(channels_cfg) < 2:
        raise ValueError("Config must specify at least two channels under 'channels'.")

    ch_a_idx = int(channels_cfg[0]["number"])
    ch_b_idx = int(channels_cfg[1]["number"])
    ch_a_name = channels_cfg[0]["name"]
    ch_b_name = channels_cfg[1]["name"]

    print(f'Type of data {type(channels_cfg)}')

    print(" Selected channels:")
    print(f" - {ch_a_name} (index={ch_a_idx})")
    print(f" - {ch_b_name} (index={ch_b_idx})")

    # --- Step 4: Assume channel axis = 0 (common in OME-TIFFs: C, Z, Y, X) ---
    channel_axis = 0
    print(f" Assuming channel axis = {channel_axis}")

    # --- Step 5: Extract channel planes ---
    # channel_a = _extract_2d_channel(img, channel_axis, ch_a_idx)
    # channel_b = _extract_2d_channel(img, channel_axis, ch_b_idx)

    channel_a = img[ch_a_idx,0, :, :]
    channel_b = img[ch_b_idx,0, :, :]   

    if channel_a.shape != channel_b.shape:
        raise ValueError(f"Channel shape mismatch: {channel_a.shape} vs {channel_b.shape}")

    print(f" Extracted channels shape: {channel_a.shape}")

    # --- Step 6: Save quick visualization for QC ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    axes[0].imshow(channel_a, cmap="gray")
    axes[0].set_title(f"{ch_a_name} (Channel {ch_a_idx})")
    axes[0].axis("off")

    axes[1].imshow(channel_b, cmap="gray")
    axes[1].set_title(f"{ch_b_name} (Channel {ch_b_idx})")
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig("channel_preview.png", dpi=150)
    plt.close(fig)
    print("✅ Channel preview saved as channel_preview.png")

    # --- Step 7: Prepare 3-channel image for segmentation ---
    blank = np.zeros_like(channel_a)
    input_img = np.stack([blank, channel_a, channel_b], axis=-1)
    print(f" Prepared RGB image for segmentation: {input_img.shape}")

    # --- Step 8: Run CellSAM segmentation ---
    print("⚙️  Running segmentation...")
    mask = cellsam_pipeline(
        input_img,
        use_wsi=use_wsi,
        low_contrast_enhancement=True,
        gauge_cell_size=False
    )

    # --- Step 9: Save output ---
    output_path = Path(output_name).resolve()
    tifffile.imwrite(output_path, mask)
    print(f"🏁 Segmentation completed.\n Output saved to: {output_path}")

    return output_path


# --------------------------------------------------------------------------- #
#                            CLI Entrypoint                                   #
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="Run generalized cell segmentation on OME-TIFF images.")
    parser.add_argument("--input_dir", type=str, required=True,
                        help="Directory containing the .ome.tiff image and config.yaml")
    parser.add_argument("--output_name", type=str, default="segmentation_mask.tiff",
                        help="Output filename for the segmentation mask")

    args = parser.parse_args()
    run_segmentation(args.input_dir, args.output_name)


if __name__ == "__main__":
    main()
