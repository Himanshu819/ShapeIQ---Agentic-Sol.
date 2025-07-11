# pipeline.py
import csv
import os
import logging
# Import the single MPN processing function
from src.tools.process_single import process_single_mpn_full_pipeline 

# Configure logging for better visibility in pipeline
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_pipeline(input_csv_path: str, output_csv_path: str):
    """
    Reads MPNs from an input CSV, processes each, and writes all results to an output CSV.
    """
    input_mpns = []
    try:
        with open(input_csv_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                if 'MPN' in row and row['MPN'].strip(): # Assuming MPN column name
                    input_mpns.append(row['MPN'].strip())
                else:
                    logging.warning(f"Skipping row due to missing or empty 'MPN' field: {row}")
    except FileNotFoundError:
        logging.error(f"Input CSV file not found: {input_csv_path}")
        return
    except Exception as e:
        logging.error(f"Error reading input CSV {input_csv_path}: {e}")
        return

    if not input_mpns:
        logging.warning("No MPNs found in the input CSV. Pipeline aborted.")
        return

    # Define the exact fieldnames for your output CSV, including all possible fields
    # These must match the keys returned by process_single_mpn_full_pipeline
    output_fieldnames = [
        "mpn",
        "length", "width", "thickness",
        "pin_length", "pin_width", "pin_pitch", "pin_count",
        "shape_name",
        "package_code",
        "pitch",        
        "packaging",
        # Add 'NAPINO PART NO.' and 'COMPONENTS DESCRIPTION' here if you will read them from the input BOM CSV
    ]

    # Create/overwrite the output CSV with headers
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
        writer.writeheader()

        for mpn in input_mpns:
            single_mpn_data = process_single_mpn_full_pipeline(mpn) # Call the single MPN processing function
            writer.writerow(single_mpn_data) # Write the result to the output CSV

    logging.info(f"\n--- Batch processing complete. Results saved to {output_csv_path} ---")


if __name__ == "__main__":
    # Create the input_boms directory if it doesn't exist
    os.makedirs("input_boms", exist_ok=True)
    
    # Create a dummy input CSV for testing
    dummy_input_csv_path = "input_boms/murata_boms.csv"
    if not os.path.exists(dummy_input_csv_path):
        with open(dummy_input_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['MPN'])
            writer.writerow(['GRM155R61A475MEAAD'])
            writer.writerow(['GCM1555C1H221JA16D'])
            writer.writerow(['GRT033C81A104KE01J'])
            writer.writerow(['GCJ0335C1H101JA16D']) # Example GCJ part
            writer.writerow(['RMCH10K100FTH']) # Example Vishay part (will likely fail with current simple fetcher)
        logging.info(f"Created a dummy input CSV: {dummy_input_csv_path}")

    # Set the output CSV path
    output_csv_path = "output/mechanical_data.csv"
    
    # This is the line that actually runs the batch pipeline
    run_pipeline(dummy_input_csv_path, output_csv_path)