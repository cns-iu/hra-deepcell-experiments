import os
import pandas as pd

# Input and output folders
input_folder = "ross_results"
output_folder = "processed_ross"
os.makedirs(output_folder, exist_ok=True)

# List all CSV files in ross_results
csv_files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]

for file_name in csv_files:
    input_path = os.path.join(input_folder, file_name)
    
    # Read the CSV
    df = pd.read_csv(input_path)
    
    # Compute cell counts per cell_type
    counts = df['cell_type'].value_counts().reset_index()
    counts.columns = ['Cell_type', 'Cell_Count']
    
    # Compute percentages
    total_cells = counts['Cell_Count'].sum()
    counts['Percentages'] = counts['Cell_Count'] / total_cells * 100
    
    # Sort by Cell_Count descending
    counts = counts.sort_values(by='Cell_Count', ascending=False)
    
    # Rename the file: remove underscores from HBM code and change suffix
    base_name = file_name.replace("_predictions.csv", "")
    new_base = base_name.replace("_", "")  # remove underscores
    new_file_name = f"{new_base}_deepcell_population.csv"
    
    # Save the processed CSV
    output_path = os.path.join(output_folder, new_file_name)
    counts.to_csv(output_path, index=False)
    
    print(f"Processed {file_name} -> {new_file_name}")

print("All files processed and saved in 'processed_ross'")
