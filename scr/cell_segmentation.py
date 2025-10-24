#!/usr/bin/env python3
"""
segmentation.py
----------------
CLI and module-compatible script for running segmentation on OME-TIFF images
based on config.yaml.

Usage (CLI):
    python segmentation.py --input_dir /path/to/input --output_name mask_output.tiff

Expected input directory:
    /path/to/input/
        ├── reg001_expr.ome.tiff
        └── config.yaml
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
    Find an axis in `shape` whose size is > required_max_idx.
    Prefer earlier axes if multiple match.
    """
    for ax, s in enumerate(shape):
        if s > required_max_idx:
            return ax
    return None


def _slice_to_2d(img, channel_axis, channel_index):
    """
    Slice the ND image to return a 2D (Y, X) array for the requested channel.
    - channel_axis: axis index in img which corresponds to channels
    - channel_index: which channel to select (0-based, as in config)
    Strategy:
      * Set selector[channel_axis] = channel_index
      * For any other axis except the last two (assumed Y,X) if size > 1 choose index 0
      * Squeeze and ensure the result is 2D
    """
    if channel_index >= img.shape[channel_axis]:
        raise IndexError(
            f"Channel index {channel_index} out of bounds for axis {channel_axis} with size {img.shape[channel_axis]}"
        )

    sel = [slice(None)] * img.ndim
    sel[channel_axis] = int(channel_index)

    # Identify last two axes as Y, X
    y_axis = img.ndim - 2
    x_axis = img.ndim - 1

    # For other axes (time/z/etc.), if size > 1 choose index 0 (first plane)
    for ax in range(img.ndim):
        if ax == channel_axis or ax in (y_axis, x_axis):
            continue
        if img.shape[ax] > 1:
            sel[ax] = 0  # pick first z/frame

    arr = img[tuple(sel)]
    arr = np.squeeze(arr)

    if arr.ndim != 2:
        # If there are still extra dims, try to collapse to last two dims
        arr = arr.reshape(arr.shape[-2], arr.shape[-1])

    return arr


# --------------------------------------------------------------------------- #
#                            Core Segmentation Logic                          #
# --------------------------------------------------------------------------- #
def run_segmentation(input_dir: str, output_name: str):
    """
    Runs segmentation using image + config in the input directory.

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

    # --- Step 2: Read image ---
    img = iio.imread(image_path)
    print(f"Image loaded: {img.shape}, dtype={img.dtype}")

    # --- Step 3: Read channel indices from config ---
    channels_cfg = config.get("channels", [])
    if len(channels_cfg) < 2:
        raise ValueError("Config must contain at least two channels under 'channels'")

    ch1_idx = int(channels_cfg[0]["number"])
    ch2_idx = int(channels_cfg[1]["number"])

    max_req_idx = max(ch1_idx, ch2_idx)
    print("Using channels:")
    print(f" - {channels_cfg[0]['name']} (index={ch1_idx})")
    print(f" - {channels_cfg[1]['name']} (index={ch2_idx})")

    # --- Step 4: Infer channel axis robustly ---
    channel_axis = _infer_channel_axis(img.shape, max_req_idx)
    if channel_axis is None:
        raise IndexError(
            f"Could not find an axis in image shape {img.shape} that can hold channel index {max_req_idx}. "
            f"Check config and image layout."
        )
    print(f"Inferred channel axis: {channel_axis} (axis length = {img.shape[channel_axis]})")

    # --- Step 5: Slice out the two channels as 2D images (z-plane selected if present) ---
    hoechst1 = _slice_to_2d(img, channel_axis, ch1_idx)
    cytokeratin = _slice_to_2d(img, channel_axis, ch2_idx)

    # Ensure both are 2D and same shape
    if hoechst1.shape != cytokeratin.shape:
        raise ValueError(f"Selected channels have incompatible shapes: {hoechst1.shape} vs {cytokeratin.shape}")

    print(f"Selected shapes -> Hoechst1: {hoechst1.shape}, Cytokeratin: {cytokeratin.shape}")

    # --- Step 6: Save preview of the selected channels (sanity check) ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    axes[0].imshow(hoechst1, cmap="gray")
    axes[0].set_title(f"{channels_cfg[0]['name']} (Channel {ch1_idx})")
    axes[0].axis("off")

    axes[1].imshow(cytokeratin, cmap="gray")
    axes[1].set_title(f"{channels_cfg[1]['name']} (Channel {ch2_idx})")
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig("channel_preview.png", dpi=150)
    plt.close(fig)
    print("✅ Channel preview saved as channel_preview.png")

    # --- Step 7: Build the 3-channel CellSAM-compatible image (no normalization) ---
    # Channel 0 (R): blank
    # Channel 1 (G): Hoechst1
    # Channel 2 (B): Cytokeratin
    blank_channel = np.zeros_like(hoechst1, dtype=np.float32)
    g_chan = hoechst1.astype(np.float32, copy=False)
    b_chan = cytokeratin.astype(np.float32, copy=False)
    three_channel_img = np.stack([blank_channel, g_chan, b_chan], axis=-1)  # shape (Y, X, 3)

    print("Final input image shape:", three_channel_img.shape)  # (Y, X, 3)

    # --- Step 8: Run segmentation pipeline (pass use_wsi from config) ---
    print("Running segmentation...")
    mask = cellsam_pipeline(
        three_channel_img,
        use_wsi=use_wsi,
        low_contrast_enhancement=True,
        gauge_cell_size=False
    )

    # --- Step 9: Save segmentation mask ---
    output_path = Path(output_name).resolve()
    tifffile.imwrite(output_path, mask.astype(np.uint16))
    print(f"✅ Segmentation completed and saved to {output_path}")

    return output_path


# --------------------------------------------------------------------------- #
#                            CLI Entrypoint                                   #
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="Run cell segmentation on OME-TIFF images.")
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
