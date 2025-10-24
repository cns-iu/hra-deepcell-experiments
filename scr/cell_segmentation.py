#!/usr/bin/env python3
"""
segmentation.py
----------------
Generalized CLI and module-compatible script for running cell segmentation
on OME-TIFF images using the CellSAM pipeline.

This script is designed for flexible use — it supports any two imaging channels
specified in a YAML configuration file, making it suitable for API-driven or
batch processing workflows.

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
def _infer_channel_axis(shape, required_max_idx):
    """
    Identify the axis in the image corresponding to the channel dimension.

    Args:
        shape (tuple): Image shape (can be 4D, 5D, etc.)
        required_max_idx (int): Maximum channel index requested by config

    Returns:
        int or None: The axis index that represents channels, or None if not found
    """
    for ax, size in enumerate(shape):
        if size > required_max_idx:
            return ax
    return None


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

    # Assume the last two axes are Y, X. If extra axes exist (Z, T, etc.), select the first frame
    for ax in range(img.ndim - 2):  # skip last two (Y, X)
        if ax == channel_axis:
            continue
        if img.shape[ax] > 1:
            selector[ax] = 0

    arr = np.squeeze(img[tuple(selector)])
    if arr.ndim != 2:
        arr = arr.reshape(arr.shape[-2], arr.shape[-1])

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

    # --- Step 2: Load image ---
    img = iio.imread(image_path)
    print(f"🧠 Image loaded: shape={img.shape}, dtype={img.dtype}")

    # --- Step 3: Parse channel configuration ---
    channels_cfg = config.get("channels", [])
    if len(channels_cfg) < 2:
        raise ValueError("Config must specify at least two channels under 'channels'.")

    ch_a_idx = int(channels_cfg[0]["number"])
    ch_b_idx = int(channels_cfg[1]["number"])
    ch_a_name = channels_cfg[0]["name"]
    ch_b_name = channels_cfg[1]["name"]

    print("🎨 Selected channels:")
    print(f" - {ch_a_name} (index={ch_a_idx})")
    print(f" - {ch_b_name} (index={ch_b_idx})")

    # --- Step 4: Detect channel axis automatically ---
    channel_axis = _infer_channel_axis(img.shape, max(ch_a_idx, ch_b_idx))
    if channel_axis is None:
        raise IndexError(
            f"Could not identify channel axis for shape {img.shape}. "
            f"Check the channel indices in config.yaml."
        )

    print(f"📏 Inferred channel axis: {channel_axis} (length={img.shape[channel_axis]})")

    # --- Step 5: Extract individual channel planes ---
    channel_a = _extract_2d_channel(img, channel_axis, ch_a_idx)
    channel_b = _extract_2d_channel(img, channel_axis, ch_b_idx)

    if channel_a.shape != channel_b.shape:
        raise ValueError(f"Channel shape mismatch: {channel_a.shape} vs {channel_b.shape}")

    print(f"🧩 Extracted channel shapes: {channel_a.shape}")

    # --- Step 6: Save a quick channel visualization for QC ---
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

    # --- Step 7: Build the CellSAM-compatible 3-channel image ---
    # R = blank; G = channel_a; B = channel_b
    blank = np.zeros_like(channel_a, dtype=np.float32)
    channel_a = channel_a.astype(np.float32, copy=False)
    channel_b = channel_b.astype(np.float32, copy=False)

    input_img = np.stack([blank, channel_a, channel_b], axis=-1)
    print("🧮 Prepared 3-channel image for segmentation:", input_img.shape)

    # --- Step 8: Run CellSAM segmentation pipeline ---
    print("⚙️  Running segmentation...")
    mask = cellsam_pipeline(
        input_img,
        use_wsi=use_wsi,
        low_contrast_enhancement=True,
        gauge_cell_size=False
    )

    # --- Step 9: Save output segmentation mask ---
    output_path = Path(output_name).resolve()
    tifffile.imwrite(output_path, mask.astype(np.uint16))
    print(f"🏁 Segmentation completed successfully.\n🖼️  Output saved to: {output_path}")

    return output_path


# --------------------------------------------------------------------------- #
#                            CLI Entrypoint                                   #
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="Run generalized cell segmentation on OME-TIFF images.")
    parser.add_argument(
        "--input_dir", type=str, required=True,
        help="Directory containing the .ome.tiff image and config.yaml"
    )
    parser.add_argument(
        "--output_name", type=str, default="segmentation_mask.tiff",
        help="Output filename for the segmentation mask"
    )

    args = parser.parse_args()
    run_segmentation(args.input_dir, args.output_name)


# --------------------------------------------------------------------------- #
#                            Reusable as Package                              #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
