#!/usr/bin/env python3
"""
HuBMAP CODEX File Manifest Generator
Generates a manifest file for downloading CODEX expression files and config files
"""

import numpy as np 
import pandas as pd 
import os
import requests
import re
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")


def get_last_uuid(hubmap_id):
    """Fetch UUID for a HuBMAP ID from the API"""
    base_url = "https://entity.api.hubmapconsortium.org/entities/"
    url = f"{base_url}{hubmap_id}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            uuids = re.findall(r'"uuid"\s*:\s*"([a-f0-9\-]+)"', r.text)
            return uuids[-1] if uuids else None
        return None
    except Exception as e:
        print(f"  Error fetching UUID for {hubmap_id}: {e}")
        return None


def check_url_exists(url, timeout=10):
    """
    Check if a file exists on HuBMAP assets server.
    Uses GET request with byte range to avoid downloading large files.
    """
    try:
        response = requests.get(
            url, 
            timeout=timeout, 
            stream=True, 
            headers={'Range': 'bytes=0-1'}, 
            allow_redirects=True
        )
        # 200 = OK, 206 = Partial Content, 416 = Range Not Satisfiable (file exists)
        return response.status_code in [200, 206, 416]
    except Exception:
        return False


def main():
    """Main execution function"""
    # Configuration
    CSV_PATH = '/u/sbdubey/CLI_HUBMAP/hra-deepcell-experiments/scripts/spleen-codex-ufl/data/descendant_hubmapID_spleen.csv'
    OUT_DIR = "/u/sbdubey/CLI_HUBMAP/hra-deepcell-experiments/scripts/spleen-codex-ufl/data"
    MANIFEST_FILENAME = "manifest_spleen.txt"
    
    # Define possible expression file paths
    PRIMARY_EXPR_PATH = "pipeline_output/expr/reg001_expr.ome.tiff"
    ALTERNATIVE_EXPR_PATH = "stitched/expressions/reg1_stitched_expressions.ome.tiff"
    CONFIG_PATH = "pipelineConfig.json"
    
    # HuBMAP assets server base URL
    ASSETS_BASE_URL = "https://assets.hubmapconsortium.org"
    
    # Step 1: Load CSV file
    print(f"Loading data from: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"✓ Loaded {len(df)} records")
    
    # Step 2: Fetch UUIDs
    print("\nFetching UUIDs from HuBMAP API...")
    df['last_uuid'] = [
        get_last_uuid(hid) for hid in tqdm(df['Found_CODEX_IDs'], desc="Fetching UUIDs")
    ]
    
    print(f"\n✓ UUID mapping complete")
    print(f"  Total IDs: {len(df)}")
    print(f"  With UUIDs: {df['last_uuid'].notna().sum()}")
    print(f"  Missing UUIDs: {df['last_uuid'].isna().sum()}")
    
    # Step 3: Create output directory
    if not os.path.exists(OUT_DIR):
        print(f"\nCreating directory: {OUT_DIR}")
        os.makedirs(OUT_DIR, exist_ok=True)
    else:
        print(f"\n✓ Directory exists: {OUT_DIR}")
    
    # Step 4: Configuration display
    print("\nFile Configuration:")
    print(f"  Primary path: {PRIMARY_EXPR_PATH}")
    print(f"  Alternative path: {ALTERNATIVE_EXPR_PATH}")
    print(f"  Config path: {CONFIG_PATH}")
    
    # Step 5: Check file availability and build manifest
    manifest_lines = []
    found_count = 0
    not_found_count = 0
    missing_uuid_count = 0
    
    print(f"\nChecking file availability for {len(df)} datasets...")
    print("-" * 60)
    
    for idx, row in df.iterrows():
        hubmap_id = row['Found_CODEX_IDs']
        uuid = row['last_uuid']
        
        print(f"\n[{idx+1}/{len(df)}] {hubmap_id}")
        
        # Skip if UUID is missing
        if pd.isna(uuid):
            print(f"  ✗ No UUID found")
            missing_uuid_count += 1
            continue
        
        print(f"  UUID: {uuid}")
        
        # Build URLs to check
        primary_url = f"{ASSETS_BASE_URL}/{uuid}/{PRIMARY_EXPR_PATH}"
        alternative_url = f"{ASSETS_BASE_URL}/{uuid}/{ALTERNATIVE_EXPR_PATH}"
        
        # Check which expression file exists
        expr_file_to_use = None
        
        print(f"  Checking primary path...", end=" ")
        if check_url_exists(primary_url):
            expr_file_to_use = PRIMARY_EXPR_PATH
            print(f"✓ Found")
        else:
            print(f"✗ Not found")
            print(f"  Checking alternative path...", end=" ")
            if check_url_exists(alternative_url):
                expr_file_to_use = ALTERNATIVE_EXPR_PATH
                print(f"✓ Found")
            else:
                print(f"✗ Not found")
                not_found_count += 1
                continue
        
        # Add to manifest (use HuBMAP ID, not UUID)
        manifest_lines.append(f"{hubmap_id} /{expr_file_to_use}")
        manifest_lines.append(f"{hubmap_id} /{CONFIG_PATH}")
        found_count += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  ✓ {found_count} datasets with files available")
    print(f"  ✗ {not_found_count} datasets with missing files")
    print(f"  ✗ {missing_uuid_count} datasets with missing UUIDs")
    print(f"  Total manifest lines: {len(manifest_lines)}")
    print("=" * 60)
    
    # Step 6: Save manifest to file
    manifest_path = os.path.join(OUT_DIR, MANIFEST_FILENAME)
    
    with open(manifest_path, "w") as f:
        f.write("\n".join(manifest_lines))
    
    print(f"\n✓ Manifest saved to: {manifest_path}")
    print(f"  Total lines: {len(manifest_lines)}")
    print(f"\nTo download files, run:")
    print(f"  hubmap-clt transfer {manifest_path} -d /path/to/destination/")


if __name__ == "__main__":
    main()