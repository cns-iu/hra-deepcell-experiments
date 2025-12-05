#!/usr/bin/env python3
"""
run_inference_pipeline.py
-------------------------
Run full cell segmentation + annotation pipeline on a dataset folder
containing multiple subfolders, each with a pipelineConfig.json and OME-TIFF image.
"""

import argparse
from pathlib import Path
import shutil
from cell_segmentation import run_segmentation
from cell_annotations import run_annotation
import json

def process_sample(sample_dir: Path, output_base: Path):
    """
    Process a single sample folder: run segmentation + annotation.
    """
    print(f"\nProcessing sample: {sample_dir.name}")
    
    # Read pipelineConfig.json
    config_json_path = sample_dir / "pipelineConfig.json"
    if not config_json_path.exists():
        raise FileNotFoundError(f"Config JSON not found: {config_json_path}")
    
    with open(config_json_path, "r") as f:
        config = json.load(f)
    
    # Get image filename
    image_file = config.get("image_path", "reg001_expr.ome.tiff")
    image_path = sample_dir / image_file
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Create output directory for this sample
    sample_output_dir = output_base / sample_dir.name
    sample_output_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Segmentation ---
    segmentation_output = sample_output_dir / "segmentation_mask.tiff"
    print(f"Running segmentation → {segmentation_output}")
    mask_path = run_segmentation(str(sample_dir), str(segmentation_output))

    # --- Step 2: Annotation ---
    # Copy pipelineConfig.json to mimic expected input for annotation
    annotation_input_dir = sample_output_dir / "annotation_input"
    annotation_input_dir.mkdir(exist_ok=True)
    shutil.copy(config_json_path, annotation_input_dir / "config.yaml")  # annotation expects config.yaml
    shutil.copy(image_path, annotation_input_dir / image_file)
    
    print("Running annotation...")
    annotation_results = run_annotation(
        input_dir=str(annotation_input_dir),
        input_segmentation=str(mask_path),
        output_dir=str(sample_output_dir)
    )

    print(f"✅ Finished sample: {sample_dir.name}")
    return annotation_results


def main():
    parser = argparse.ArgumentParser(description="Run segmentation + annotation on a dataset folder.")
    parser.add_argument("--input_dir", type=str, required=True,
                        help="Input dataset folder containing multiple sample subfolders")
    parser.add_argument("--output_dir", type=str, required=True,
                        help="Directory to store output CSVs and segmentation masks")
    args = parser.parse_args()

    input_base = Path(args.input_dir)
    output_base = Path(args.output_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    # Loop over all subfolders
    for sample_dir in input_base.iterdir():
        if sample_dir.is_dir():
            try:
                process_sample(sample_dir, output_base)
            except Exception as e:
                print(f"❌ Failed processing {sample_dir.name}: {e}")


if __name__ == "__main__":
    main()
