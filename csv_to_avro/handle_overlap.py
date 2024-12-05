import os
import shutil
import re
from datetime import datetime
from pathlib import Path

def extract_time_range(file_name):
    """
    Extracts start and end time from a file name with the format:
    'flights_YYYYMMDD_HHMM_to_YYYYMMDD_HHMM.ext'

    Parameters:
        file_name (str): Name of the file.

    Returns:
        tuple: (start_time, end_time) as datetime objects.
               Returns (None, None) if the format is invalid.
    """
    pattern = r"flights_(\d{8})_(\d{4})_to_(\d{8})_(\d{4})"
    match = re.search(pattern, file_name)

    if match:
        start_date = match.group(1)  
        start_time = match.group(2)  
        end_date = match.group(3)    
        end_time = match.group(4)    

        try:
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y%m%d %H%M")
            end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y%m%d %H%M")
            return start_datetime, end_datetime
        except ValueError:
            return None, None
    return None, None

def handle_overlaps_latest(path):
    input_path = Path(path)
    if not input_path.is_dir():
        raise ValueError(f"Provided path '{path}' is not a valid directory.")

    output_path = input_path / "no_overlap"
    output_path.mkdir(exist_ok=True)

    files = list(input_path.iterdir())
    file_times = []
    
    for file in files:
        if file.is_file(): 
            start_time, end_time = extract_time_range(str(file))
            if start_time and end_time:
                file_times.append((file, start_time, end_time))

    file_times.sort(key=lambda x: x[2], reverse=True)

    selected_files = []
    covered_periods = []

    for file, start, end in file_times:
        overlaps = False
        for covered_start, covered_end in covered_periods:
            if start <= covered_end and end >= covered_start:
                if (end - start) <= (covered_end - covered_start):
                    overlaps = True
                    break

        if not overlaps:
            selected_files.append(file)
            covered_periods.append((start, end))

    for selected_file in selected_files:
        shutil.copy(selected_file, output_path)

    return [str(file) for file in selected_files]

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python handle_overlaps.py <input_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    handle_overlaps_latest(input_path) 
    print(f"Overlap handling completed. Output files are in '{input_path}/no_overlap'")