import sys
import os
import fastavro
from typing import List
from datetime import datetime, timedelta
from google.cloud import storage
from schema import SCHEMA
import io

def get_date_from_filename(filename: str) -> datetime:
    """Extract date from filename format: flights_YYYYMMDD_HHMM_to_YYYYMMDD_HHMM.avro"""
    try:
        date_str = filename.split('_')[1]
        return datetime.strptime(date_str, '%Y%m%d')
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid filename format: {filename}") from e

def get_week_bounds(date: datetime) -> tuple[datetime, datetime]:
    """Get the Monday and Sunday dates for the week containing the given date."""
    monday = date - timedelta(days=date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday

def group_files_by_week(blobs: List[storage.Blob]) -> dict:
    """Group files by week periods (Monday-Sunday)."""
    weekly_files = {}
    
    for blob in blobs:
        try:
            file_date = get_date_from_filename(blob.name)
            week_start, _ = get_week_bounds(file_date)
            
            if week_start not in weekly_files:
                weekly_files[week_start] = []
            weekly_files[week_start].append(blob)
        except ValueError as e:
            print(f"Skipping file {blob.name}: {str(e)}")
            continue
    
    return weekly_files

def merge_avro_files(bucket_name: str, output_bucket_name: str) -> None:
    """
    Merge AVRO files from GCS bucket into weekly files.
    
    Args:
        bucket_name: Source bucket name
        output_bucket_name: Destination bucket name
    """
    client = storage.Client()
    source_bucket = client.bucket(bucket_name)
    output_bucket = client.bucket(output_bucket_name)
    
    # List all AVRO files in bucket
    blobs = list(source_bucket.list_blobs(prefix='', delimiter='/'))
    avro_blobs = [blob for blob in blobs if blob.name.endswith('.avro')]
    
    if not avro_blobs:
        print(f"No AVRO files found in bucket {bucket_name}")
        return
    
    # Group files by week
    weekly_files = group_files_by_week(avro_blobs)
    
    for week_start, blobs in weekly_files.items():
        week_end = week_start + timedelta(days=6)
        output_name = f"flights_weekly_{week_start.strftime('%Y%m%d')}_to_{week_end.strftime('%Y%m%d')}.avro"
        
        # Collect all records
        all_records = []
        for blob in blobs:
            try:
                content = blob.download_as_bytes()
                reader = fastavro.reader(io.BytesIO(content))
                all_records.extend(list(reader))
                print(f"Read {len(all_records)} records from {blob.name}")
            except Exception as e:
                print(f"Error reading blob {blob.name}: {str(e)}")
                continue
        
        # Write merged records to output bucket
        try:
            output_blob = output_bucket.blob(output_name)
            with io.BytesIO() as buffer:
                fastavro.writer(buffer, SCHEMA, all_records)
                buffer.seek(0)
                output_blob.upload_from_file(buffer)
                
            print(f"Successfully merged {len(blobs)} files ({len(all_records)} records) for week "
                  f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
        except Exception as e:
            print(f"Error writing output blob {output_name}: {str(e)}")
            continue

def main():
    if len(sys.argv) != 4:
        print("Usage: python merge.py <credentials_path> <source_bucket> <output_bucket>")
        sys.exit(1)
    
    credentials_path = sys.argv[1]
    source_bucket = sys.argv[2]
    output_bucket = sys.argv[3]
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    merge_avro_files(source_bucket, output_bucket)

if __name__ == "__main__":
    main()