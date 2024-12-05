import sys
import glob
import os
import fastavro
from typing import List
from datetime import datetime, timedelta
from schema import SCHEMA

def get_date_from_filename(filename: str) -> datetime:
    """
    Extract date from filename format: flights_YYYYMMDD_HHMM_to_YYYYMMDD_HHMM.avro
    Returns the date from the first timestamp in the filename.
    """
    try:
        # Extract the first date part (YYYYMMDD)
        date_str = filename.split('_')[1]
        return datetime.strptime(date_str, '%Y%m%d')
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid filename format: {filename}") from e

def get_week_bounds(date: datetime) -> tuple[datetime, datetime]:
    """
    Get the Monday and Sunday dates for the week containing the given date.
    """
    monday = date - timedelta(days=date.weekday())  # Get Monday of the week
    sunday = monday + timedelta(days=6)  # Get Sunday of the week
    return monday, sunday

def group_files_by_week(input_files: List[str]) -> dict:
    """
    Group files by week periods (Monday-Sunday).
    Returns a dictionary with week start dates as keys and lists of files as values.
    """
    weekly_files = {}
    
    for file in input_files:
        try:
            file_date = get_date_from_filename(os.path.basename(file))
            week_start, _ = get_week_bounds(file_date)
            
            if week_start not in weekly_files:
                weekly_files[week_start] = []
            weekly_files[week_start].append(file)
        except ValueError as e:
            print(f"Skipping file {file}: {str(e)}")
            continue
    
    return weekly_files

def merge_avro_files(input_path: str, output_dir: str) -> None:
    """
    Merge AVRO files into weekly output files.
    
    Args:
        input_path: Path to input directory or file
        output_dir: Path to output directory
    """
    # Get list of input files
    if os.path.isdir(input_path):
        input_files = glob.glob(os.path.join(input_path, "*.avro"))
    else:
        input_files = [input_path]
    
    if not input_files:
        print(f"No AVRO files found in {input_path}")
        return
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Group files by week
    weekly_files = group_files_by_week(input_files)
    
    for week_start, files in weekly_files.items():
        week_end = week_start + timedelta(days=6)
        output_file = os.path.join(
            output_dir,
            f"flights_weekly_{week_start.strftime('%Y%m%d')}_to_{week_end.strftime('%Y%m%d')}.avro"
        )
        
        # Collect all records first
        all_records = []
        for file in files:
            try:
                with open(file, 'rb') as f:
                    reader = fastavro.reader(f)
                    all_records.extend(list(reader))
                print(f"Read {len(all_records)} records from {file}")
            except Exception as e:
                print(f"Error reading file {file}: {str(e)}")
                continue
        
        # Write all collected records to the output file
        try:
            with open(output_file, 'wb') as out:
                fastavro.writer(out, SCHEMA, all_records)
            print(f"Successfully merged {len(files)} files ({len(all_records)} records) for week "
                  f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')} "
                  f"into {output_file}")
        except Exception as e:
            print(f"Error writing to output file {output_file}: {str(e)}")
            continue

def main():
    if len(sys.argv) != 3:
        print("Usage: python merge.py <input_path> <output_directory>")
        print("input_path can be either a directory containing AVRO files or a single AVRO file")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    if not os.path.exists(input_path):
        print(f"Input path {input_path} does not exist")
        sys.exit(1)
    
    merge_avro_files(input_path, output_dir)

if __name__ == "__main__":
    main()