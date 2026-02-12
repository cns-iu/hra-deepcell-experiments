# Note place this code in Ross Repo and directly run it using 'python3 getsample.py' 
import os
import pandas as pd
import zarr
from pprint import pprint

# Make sure output folder exists
output_folder = "ross_results"
os.makedirs(output_folder, exist_ok=True)

# Open the Zarr archive (update anon=False and region_name as needed)
z = zarr.open_group(
    store="s3://hubmap-mirror-demo/hubmap.zarr",
    mode="r",
    storage_options={
        "anon": False,
        "client_kwargs": dict(region_name="us-east-2")
    }
)

# List available datasets
dataset_keys = list(z.group_keys())
print(f"Number of datasets available: {len(dataset_keys)}")
print(dataset_keys[:20])  # show first 20 for reference

# Iterate through datasets
for ds_key in dataset_keys:
    print(f"Processing {ds_key}")
    try:
        ds = z[ds_key]

        # Fetch cell type predictions
        if "cell_types/predictions" not in ds:
            print(f"  ⚠ No cell_types/predictions for {ds_key}, skipping.")
            continue

        predictions_attr = ds["cell_types/predictions"].attrs.get("hubmap_dct", None)
        if predictions_attr is None:
            print(f"  ⚠ No hubmap_dct found for {ds_key}, skipping.")
            continue

        # Convert to DataFrame
        df = pd.DataFrame.from_dict(
            predictions_attr,
            orient="index",
            columns=("cell_type", "CL_id")
        )

        # Save as CSV
        csv_file = os.path.join(output_folder, f"{ds_key}_predictions.csv")
        df.to_csv(csv_file, index_label="cell_index")
        print(f"  ✅ Saved to {csv_file}")

    except KeyError:
        print(f"  ⚠ Dataset {ds_key} not found in archive. Skipping.")
    except Exception as e:
        print(f"  ✖ Failed for {ds_key}: {e}")

print("All done!")
