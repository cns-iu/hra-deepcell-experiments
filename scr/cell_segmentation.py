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
from cellSAM.utils import normalize_image


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

    # --- Step 3: Handle channel/Z-axis inference ---
    # Typical OME-TIFF shapes:
    #  (C, Z, Y, X), (Z, C, Y, X), (Z, Y, X), or (Y, X)
    ndim = img.ndim

    if ndim == 4:
        # Determine which axis is channels
        if img.shape[0] < 10:  # channels first
            cdim = 0
        elif img.shape[1] < 10:
            cdim = 1
        else:
            raise ValueError("Cannot infer channel dimension from shape.")
    elif ndim == 3:
        # Single channel Z-stack (Z, Y, X)
        cdim = None
    elif ndim == 2:
        # Single plane grayscale
        cdim = None
    else:
        raise ValueError(f"Unsupported image shape: {img.shape}")

    # --- Step 4: Extract or synthesize channels ---
    channels = config["channels"]
    ch1 = channels[0]
    ch2 = channels[1]
    ch1_idx, ch2_idx = ch1["number"], ch2["number"]

    print("Using channels:")
    print(f" - {ch1['name']} (index={ch1_idx})")
    print(f" - {ch2['name']} (index={ch2_idx})")

    if cdim is None:
        # No explicit channels; use same image twice as pseudo-channels
        hoechst = np.mean(img, axis=0) if img.ndim == 3 else img
        cytokeratin = hoechst.copy()
        print("⚠️ Single-channel image detected; duplicating channel for segmentation.")
    else:
        if cdim == 0:
            # shape (C, Z, Y, X)
            if img.shape[1] == 1:
                hoechst = img[ch1_idx, 0]
                cytokeratin = img[ch2_idx, 0] if ch2_idx < img.shape[0] else img[ch1_idx, 0]
            else:
                hoechst = np.mean(img[ch1_idx], axis=0)
                cytokeratin = np.mean(img[ch2_idx], axis=0)
        else:
            # shape (Z, C, Y, X)
            if img.shape[1] == 1:
                hoechst = img[0, 0]
                cytokeratin = img[0, 0]
                print("⚠️ Only one channel present across Z; duplicating channel.")
            else:
                hoechst = np.mean(img[:, ch1_idx], axis=0)
                cytokeratin = np.mean(img[:, ch2_idx], axis=0)

    # --- Step 5: Stack into (2, Y, X) ---
    selected = np.stack([hoechst, cytokeratin], axis=0)
    print(f"Selected stacked image shape: {selected.shape}")

    # --- Step 6: Save visualization ---
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(hoechst, cmap="gray")
    axes[0].set_title(f"{ch1['name']} (Channel {ch1_idx})")
    axes[0].axis("off")

    axes[1].imshow(cytokeratin, cmap="gray")
    axes[1].set_title(f"{ch2['name']} (Channel {ch2_idx})")
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig("channel_preview.png", dpi=150)
    plt.close(fig)
    print("✅ Channel preview saved as channel_preview.png")

    # --- Step 7: Prepare pseudo-RGB ---
    rgb_img = np.zeros((3, *selected.shape[1:]), dtype=np.float32)
    rgb_img[1] = normalize_image(selected[0])  # nuclear → G
    rgb_img[2] = normalize_image(selected[1])  # membrane → B
    rgb_img = np.transpose(rgb_img, (1, 2, 0))  # (Y, X, 3)

    # --- Step 8: Run segmentation pipeline ---
    print("Running segmentation...")
    mask = cellsam_pipeline(
        rgb_img,
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
