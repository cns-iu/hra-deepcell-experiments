#!/usr/bin/env python3
"""
HuBMAP CODEX Data Processor
Processes CODEX datasets by extracting metadata and creating YAML configuration files
"""

import os
import json
import yaml
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from tifffile import TiffFile


def get_hubmap_id(dir_name):
    """Extract HuBMAP ID from directory name and remove dots"""
    # Extract HBM###.XXXX.### part and remove dots
    parts = dir_name.split('-')[0]
    return parts.replace('.', '')


def extract_mpp(tiff_path):
    """Extract microns per pixel from TIFF metadata"""
    with TiffFile(tiff_path) as tif:
        ome_xml = tif.ome_metadata
        
        # Parse PhysicalSizeX and unit
        if 'PhysicalSizeX="' in ome_xml:
            start = ome_xml.find('PhysicalSizeX="') + 15
            end = ome_xml.find('"', start)
            physical_size_x = float(ome_xml[start:end])
            
            start = ome_xml.find('PhysicalSizeXUnit="') + 19
            end = ome_xml.find('"', start)
            unit = ome_xml[start:end]
            
            # Convert to microns
            if unit == 'nm':
                mpp = physical_size_x / 1000
            elif unit == 'µm' or unit == 'um':
                mpp = physical_size_x
            elif unit == 'mm':
                mpp = physical_size_x * 1000
            elif unit == 'm':
                mpp = physical_size_x * 1000000
            else:
                mpp = physical_size_x
                
            return round(mpp, 5)
    return None


def extract_channels_from_tiff(tiff_path):
    """Extract channel names from TIFF OME-XML metadata"""
    with TiffFile(tiff_path) as tif:
        ome_xml = tif.ome_metadata
        
        # Parse OME-XML to extract channels
        root = ET.fromstring(ome_xml)
        ns = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}
        channels = [c.attrib.get("Name") for c in root.findall(".//ome:Channel", ns)]
        
        return channels


def create_yaml_config(json_path, tiff_path, hubmap_id):
    """Create YAML configuration from JSON config and TIFF metadata"""
    with open(json_path, 'r') as f:
        config = json.load(f)
    
    # Extract nucleus and cell channel names from JSON
    nucleus_channel = config['report']['reg1']['nucleus_channel']
    cell_channel = config['report']['reg1']['cell_channel']
    
    # Extract channel names directly from TIFF
    channel_names = extract_channels_from_tiff(tiff_path)
    
    # Get channel indices from the actual TIFF channels
    try:
        nucleus_idx = channel_names.index(nucleus_channel)
    except ValueError:
        raise ValueError(f"Nucleus channel '{nucleus_channel}' not found in TIFF channels")
    
    try:
        cell_idx = channel_names.index(cell_channel)
    except ValueError:
        raise ValueError(f"Cell channel '{cell_channel}' not found in TIFF channels")
    
    # Extract MPP
    mpp = extract_mpp(tiff_path)
    
    # Build YAML structure
    yaml_data = {
        'image_path': f'{hubmap_id}.ome.tiff',
        'use_wsi': True,
        'MPP': mpp,
        'channels': [
            {'name': nucleus_channel, 'number': nucleus_idx},
            {'name': cell_channel, 'number': cell_idx}
        ],
        'markers': [
            {'name': name, 'number': idx} 
            for idx, name in enumerate(channel_names)
        ]
    }
    
    return yaml_data


def main():
    """Main execution function"""
    # Configuration
    INPUT_ROOT = "/teradata/hra_data/deepcell-experiments-data/spleen-codex-ufl/data-original/"
    OUTPUT_ROOT = "/teradata/hra_data/deepcell-experiments-data/spleen-codex-ufl/input-data/"
    
    print(f"Input directory: {INPUT_ROOT}")
    print(f"Output directory: {OUTPUT_ROOT}")
    print()
    
    # Create output root if it doesn't exist
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    print(f"✓ Output directory ready: {OUTPUT_ROOT}\n")
    
    # Process each directory
    input_dirs = [d for d in os.listdir(INPUT_ROOT) if os.path.isdir(os.path.join(INPUT_ROOT, d))]
    
    print(f"Found {len(input_dirs)} directories to process\n")
    print("-" * 60)
    
    success_count = 0
    error_count = 0
    
    for dir_name in input_dirs:
        print(f"Processing: {dir_name}")
        
        # Get HubMAP ID
        hubmap_id = get_hubmap_id(dir_name)
        
        # Define paths
        input_dir = os.path.join(INPUT_ROOT, dir_name)
        json_path = os.path.join(input_dir, 'pipelineConfig.json')
        tiff_path = os.path.join(input_dir, 'reg001_expr.ome.tiff')
        
        # Create output directory
        output_dir = os.path.join(OUTPUT_ROOT, hubmap_id[:13])
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Create YAML config
            yaml_data = create_yaml_config(json_path, tiff_path, hubmap_id)
            
            # Write YAML file
            yaml_path = os.path.join(output_dir, f'{hubmap_id}_config.yaml')
            with open(yaml_path, 'w') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
            
            # Copy TIFF file with new name
            new_tiff_path = os.path.join(output_dir, f'{hubmap_id}.ome.tiff')
            shutil.copy2(tiff_path, new_tiff_path)
            
            print(f"  ✓ Created: {hubmap_id}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            error_count += 1
    
    print("-" * 60)
    print("\n✓ Processing complete!")
    print(f"  Successful: {success_count}")
    print(f"  Errors: {error_count}")
    
    # List created directories
    output_dirs = sorted([d for d in os.listdir(OUTPUT_ROOT) if os.path.isdir(os.path.join(OUTPUT_ROOT, d))])
    print(f"\nTotal directories created: {len(output_dirs)}")
    
    if output_dirs:
        print("\nFirst 5 directories:")
        for d in output_dirs[:5]:
            files = os.listdir(os.path.join(OUTPUT_ROOT, d))
            print(f"  {d}: {files}")


if __name__ == "__main__":
    main()