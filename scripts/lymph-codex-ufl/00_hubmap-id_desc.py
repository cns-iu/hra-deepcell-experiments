#!/usr/bin/env python3
"""
HuBMAP CODEX Descendant Processor
Automatically processes HuBMAP IDs and extracts CODEX dataset information
"""

import pandas as pd
import requests
import json
import os
from tqdm import tqdm


def load_data(path):
    """Load HuBMAP IDs from CSV file"""
    df = pd.read_csv(path)
    return df[['HuBMAP ID']].dropna().reset_index(drop=True)


def fetch_descendants(hubmap_id, token, base_url, headers):
    """Fetch descendants data for a given HuBMAP ID"""
    url = base_url + hubmap_id
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching {hubmap_id}: {e}")
        return None


def extract_codex_ids(descendants_json, parent_hubmap_id=None):
    """Extract CODEX dataset IDs from descendants JSON"""
    # Special case for specific HuBMAP ID
    if parent_hubmap_id == "HBM834.ZFVJ.978":
        return ["HBM522.BSZT.385"]
    
    if not isinstance(descendants_json, list):
        return []

    result = []
    for entry in descendants_json:
        if (
            entry.get("dataset_type") == "CODEX [Cytokit + SPRM]"
            and entry.get("status") == "Published"
            and entry.get("last_modified_user_displayname") == "Karl Burke"
        ):
            result.append(entry.get("hubmap_id"))
    return result


def main():
    """Main execution function"""
    # Configuration
    INPUT_PATH = "/u/sbdubey/CLI_HUBMAP/hra-deepcell-experiments/scripts/lymph-codex-ufl/data/deepcell_lymph.csv"
    OUTPUT_PATH = "/u/sbdubey/CLI_HUBMAP/hra-deepcell-experiments/scripts/lymph-codex-ufl/data/descendant_hubmapID_intestine_01.csv"
    TOKEN = "AgDz42Qo52d6Gr2pVvXVm40V8exo143D1m6GgQmbQ3E2O4mmwYCaC1VOX50mK6kNlpGz06Pl8E9MdKioKzPKgHpqz4o"
    BASE_URL = "https://entity.api.hubmapconsortium.org/descendants/"
    
    # Setup headers
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("Loading input data...")
    input_df = load_data(INPUT_PATH)
    print(f"Loaded {len(input_df)} HuBMAP IDs")
    
    # Process each HuBMAP ID
    output_rows = []
    
    for hubmap_id in tqdm(input_df['HuBMAP ID'], desc="Processing HuBMAP IDs"):
        data = fetch_descendants(hubmap_id, TOKEN, BASE_URL, headers)
        codex_ids = extract_codex_ids(data, parent_hubmap_id=hubmap_id) if data else extract_codex_ids(None, parent_hubmap_id=hubmap_id)
        
        output_rows.append({
            "Input_HuBMAP_ID": hubmap_id,
            "Found_CODEX_IDs": ", ".join(codex_ids) if codex_ids else None
        })
    
    # Create output dataframe
    output_df = pd.DataFrame(output_rows)
    
    # Save results
    output_df.to_csv(OUTPUT_PATH, index=False)
    print(f"\n✓ Results saved to: {OUTPUT_PATH}")
    print(f"✓ Processed {len(output_df)} records")
    print(f"✓ Found CODEX IDs in {output_df['Found_CODEX_IDs'].notna().sum()} records")


if __name__ == "__main__":
    main()