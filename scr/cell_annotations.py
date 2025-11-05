# ...existing code...
import argparse
import yaml
import imageio.v3 as iio 
import numpy as np
import pandas as pd
from pathlib import Path
import deepcell_types
import torch
from collections import defaultdict
# ...existing code...

def run_annotation(input_dir: str, input_segmentation: str, output_dir: str):
    """
    Run Annotation using an image and configuration file and the segmentation image in the input directory.

    Args:
        input_dir (str): Directory containing the config.yaml and image file (relative image_path used).
        input_segmentation (str): Path or filename of the segmentation mask (absolute or relative to input_dir).
        output_dir (str): Directory where CSV outputs will be saved.
    """
    input_dir = Path(input_dir)
    config_path = input_dir / "config.yaml"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    segmentation_mask = Path(input_segmentation)
    if not segmentation_mask.exists():
        # try relative to input_dir
        segmentation_mask = input_dir / input_segmentation

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    if not segmentation_mask.exists():
        raise FileNotFoundError(f"Segmentation mask not found: {segmentation_mask}")

    # --- Step 1: Load configuration ---
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    mpp = float(config.get("MPP", 0.0))
    print(f" The value of the MPP is : {mpp} and the datatype is {type(mpp)}")

    image_path = input_dir / config.get("image_path", "")
    if not image_path.exists():
        raise FileNotFoundError(f"Image file from config not found: {image_path}")

    # --- Step 2: Load image and mask ---
    mask = iio.imread(segmentation_mask)
    print(f" Segmentation Image loaded: shape={mask.shape}, dtype={mask.dtype}")

    img = iio.imread(image_path)
    print(f" Image loaded: shape={img.shape}, dtype={img.dtype}")

    # --- Step 2.5: Load markers robustly ---
    markers_cfg = config.get("markers", [])
    if isinstance(markers_cfg, dict):
        markers_cfg = [markers_cfg]
    all_markers = []
    for m in markers_cfg:
        if isinstance(m, dict):
            name = m.get("name") or m.get("marker") or None
            if name is None:
                raise ValueError(f"Marker entry missing name: {m}")
            all_markers.append(name)
        else:
            all_markers.append(str(m))
    print("Markers:", all_markers)

    # --- Step 3: Squeeze singleton axes if present (C,Z,Y,X) -> (C,Y,X) or (Z,C,Y,X)->(Z,Y,X) ---
    img_input = np.squeeze(img)
    print(f'The input image shape after squeeze is {img_input.shape}')

    # --- Step 4: Deep Cell Annotations ----
    model = "deepcell-types_2025-06-09"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    num_data_loader_threads = 1

    cell_types = deepcell_types.predict(
        img_input,
        mask,
        all_markers,
        mpp,
        model_name=model,
        device_num=device,
        num_workers=num_data_loader_threads,
    )

    print('Done Done Done')

    idx_to_pred = dict(enumerate(cell_types, start=1))

    # Convert to DataFrame with correct column names and save
    df_cell_types = pd.DataFrame(list(idx_to_pred.items()), columns=["Cell_ID", "Cell_Name"])
    cell_types_csv = output_dir / "deepcell_type_label.csv"
    df_cell_types.to_csv(cell_types_csv, index=False)
    print(f"✅ Saved per-cell labels → {cell_types_csv}")

    # Convert the 1-1 `cell: type` mapping to a 1-many `type: list-of-cells` mapping
    labels_by_celltype = defaultdict(list)
    for idx, ct in idx_to_pred.items():
        labels_by_celltype[ct].append(idx)

    from pprint import pprint

    num_cells = int(np.max(mask))
    print(f"Total number of cells: {num_cells}")

    pprint(
        {
            k: f"{len(v)} ({100 * len(v) / num_cells:02.2f}%)"
            for k, v in labels_by_celltype.items()
        },
        sort_dicts=False,
    )

    # --- Create and save the summary table ---
    pop_summary = {
        k: {"Cell_Count": len(v), "Percentages": 100 * len(v) / num_cells}
        for k, v in labels_by_celltype.items()
    }

    df_population = (
        pd.DataFrame.from_dict(pop_summary, orient="index")
        .reset_index()
        .rename(columns={"index": "Cell_type"})
        .sort_values("Cell_Count", ascending=False)
    )

    # Round percentages for readability
    df_population["Percentages"] = df_population["Percentages"].round(4)

    pop_csv = output_dir / "deepcell_population.csv"
    df_population.to_csv(pop_csv, index=False)
    print(f"✅ Saved population summary → {pop_csv}")

    return {"cell_types_csv": str(cell_types_csv), "population_csv": str(pop_csv)}




def main():
    parser = argparse.ArgumentParser(description="Run generalized cell annotations on HUBMAP.")
    parser.add_argument("--input_dir", type=str, required=True,
                        help="Directory containing the config.yaml")
    parser.add_argument("--input_segmentation", type=str, default="segmentation_mask.tif",
                        help="input filename for the segmentation mask (absolute or relative to input_dir)")
    parser.add_argument("--output_dir", type=str, default="results",
                        help="Directory to save output CSV files")
    args = parser.parse_args()
    run_annotation(args.input_dir, args.input_segmentation, args.output_dir)

if __name__ == "__main__":
    main()
