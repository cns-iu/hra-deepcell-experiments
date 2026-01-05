#!/usr/bin/env python3
"""
run_inference_pipeline.py
-------------------------
Run full cell segmentation + annotation pipeline on a dataset folder
containing multiple subfolders, each with a pipelineConfig.json and OME-TIFF image.
"""

#!/usr/bin/env python3
"""
run_inference_pipeline.py
--------------------------
Batch processing pipeline for cell segmentation and annotation across multiple samples.
"""

import os
import shutil
from pathlib import Path
from cell_segmentation import run_segmentation
from cell_annotations import run_annotation


def process_single_sample(input_dir: Path, output_dir: Path, hubmap_id: str):
    """
    Process a single sample through segmentation and annotation.
    
    Args:
        input_dir (Path): Directory containing config.yaml and .ome.tiff
        output_dir (Path): Directory to save all outputs
        hubmap_id (str): HubMAP ID for naming outputs
    """
    print(f"\n{'='*60}")
    print(f"Processing: {hubmap_id}")
    print(f"{'='*60}")
    
    # Create output directory
    sample_output_dir = output_dir / hubmap_id
    sample_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Run segmentation
    print(f"\n[1/2] Running segmentation...")
    seg_output_path = sample_output_dir / f"{hubmap_id}_segmented.tiff"
    
    try:
        segmentation_path = run_segmentation(
            input_dir=str(input_dir),
            output_path=str(seg_output_path)
        )
        print(f"✅ Segmentation complete: {segmentation_path}")
    except Exception as e:
        print(f"❌ Segmentation failed: {e}")
        return False
    
    # Step 2: Run annotation
    print(f"\n[2/2] Running cell type annotation...")
    
    try:
        annotation_results = run_annotation(
            input_dir=str(input_dir),
            input_segmentation=segmentation_path,
            output_dir=str(sample_output_dir)
        )
        
        # Rename output files to match naming convention
        old_cell_types = Path(annotation_results["cell_types_csv"])
        old_population = Path(annotation_results["population_csv"])
        
        new_cell_types = sample_output_dir / f"{hubmap_id}_deepcell_type.csv"
        new_population = sample_output_dir / f"{hubmap_id}_deepcell_population.csv"
        
        shutil.move(str(old_cell_types), str(new_cell_types))
        shutil.move(str(old_population), str(new_population))
        
        print(f"✅ Annotation complete")
        print(f"   Cell types: {new_cell_types}")
        print(f"   Population: {new_population}")
        
        return True
        
    except Exception as e:
        print(f"❌ Annotation failed: {e}")
        return False


def run_pipeline(input_root: str, output_root: str):
    """
    Run the complete pipeline on all samples in the input directory.
    
    Args:
        input_root (str): Root directory containing all sample folders
        output_root (str): Root directory for saving all outputs
    """
    input_root = Path(input_root)
    output_root = Path(output_root)
    
    if not input_root.exists():
        raise FileNotFoundError(f"Input directory not found: {input_root}")
    
    # Create output root
    output_root.mkdir(parents=True, exist_ok=True)
    
    # Get all sample directories
    sample_dirs = sorted([d for d in input_root.iterdir() if d.is_dir()])
    
    print(f"\n{'='*60}")
    print(f"Found {len(sample_dirs)} samples to process")
    print(f"Input:  {input_root}")
    print(f"Output: {output_root}")
    print(f"{'='*60}")
    
    # Process each sample
    success_count = 0
    failed_samples = []
    
    for i, sample_dir in enumerate(sample_dirs, 1):
        hubmap_id = sample_dir.name
        
        print(f"\n[{i}/{len(sample_dirs)}] Processing {hubmap_id}...")
        
        success = process_single_sample(sample_dir, output_root, hubmap_id)
        
        if success:
            success_count += 1
        else:
            failed_samples.append(hubmap_id)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Successfully processed: {success_count}/{len(sample_dirs)}")
    
    if failed_samples:
        print(f"\nFailed samples ({len(failed_samples)}):")
        for sample in failed_samples:
            print(f"  - {sample}")
    else:
        print(f"\n✅ All samples processed successfully!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run batch cell segmentation and annotation pipeline"
    )
    parser.add_argument(
        "--input_root",
        type=str,
        required=True,
        help="Root directory containing all sample folders with config.yaml and .ome.tiff files"
    )
    parser.add_argument(
        "--output_root",
        type=str,
        required=True,
        help="Root directory where all outputs will be saved"
    )
    
    args = parser.parse_args()
    run_pipeline(args.input_root, args.output_root)


# sample run command

# step 01:

# screen -S deepcell_pipeline

# Step 02:

# python run_inference_pipeline.py --input_root /teradata/sbdubey/deepcell-experiments-data/intestine-codex-stanford/input-data/ --output_root /teradata/sbdubey/deepcell-experiments-data/intestine-codex-stanford/output-data/

