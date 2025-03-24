import os
import json
import stat
import argparse
from datetime import datetime
import pandas as pd

from core.extractor import extract_file_artifacts

def epoch_to_str(epoch):
    try:
        return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"

def generate_timeline(artifacts, start_epoch=None, end_epoch=None, file_type=None, dir_filter=None):
    timeline = []
    
    for artifact in artifacts:
        # Filter by file type if specified.
        if file_type:
            if not artifact["name"].lower().endswith(file_type.lower()):
                continue
        # Filter by directory if specified.
        if dir_filter:
            if dir_filter not in artifact["path"]:
                continue
        
        events = []
        if artifact["created"]:
            events.append(("created", artifact["created"]))
        if artifact["modified"] and artifact["modified"] != artifact["created"]:
            events.append(("modified", artifact["modified"]))
        if artifact.get("deleted"):
            events.append(("deleted", artifact["modified"]))
        
        for event_type, timestamp in events:
            # Apply date range filtering if specified.
            if start_epoch and timestamp < start_epoch:
                continue
            if end_epoch and timestamp > end_epoch:
                continue
            timeline.append({
                "file": artifact["path"],
                "event": event_type,
                "timestamp": epoch_to_str(timestamp)
            })
    return timeline

def parse_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    except Exception:
        raise argparse.ArgumentTypeError("Date must be in YYYY-MM-DD format.")

def get_volume_offset(image_path):
    from dfvfs.resolver.context import Context
    from dfvfs.resolver import resolver
    from dfvfs.path import os_path_spec

    resolver_context = Context()
    path_spec = os_path_spec.OSPathSpec(location=image_path)
    
    try:
        file_entry = resolver.Resolver.OpenFileEntry(path_spec, resolver_context=resolver_context)
    except Exception as e:
        print(f"Error opening file entry: {e}")
        return 0

    try:
        from dfvfs.volume import tsk_volume_system
        volume_system = tsk_volume_system.TSKVolumeSystem()
        volume_system.Open(file_entry)
        volume = volume_system.GetVolume(0)
        offset = volume.start_offset * volume_system.block_size
        return offset
    except Exception as e:
        print(f"Error retrieving volume offset: {e}")
        # If a volume system isn’t found, assume offset 0.
        return 0

def main():
    parser = argparse.ArgumentParser(
        description="Extract file system artifacts and generate a forensic timeline using dfVFS, pytsk3, and pandas."
    )
    parser.add_argument("--path", required=True, help="Path to the disk image file")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD) to filter events")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD) to filter events")
    parser.add_argument("--file-type", help="Filter by file extension (e.g., .txt)")
    parser.add_argument("--directory", help="Filter by directory path (substring match)")
    parser.add_argument("--output", default="forensic_timeline.json", help="Output file name")    
    args = parser.parse_args()
    
    # Convert start and end dates to epoch timestamps if provided.
    start_epoch = parse_date(args.start_date) if args.start_date else None
    end_epoch = parse_date(args.end_date) if args.end_date else None
    
    # Use dfVFS to get the file system offset from the disk image.
    offset = get_volume_offset(args.path)
    print(f"Using file system offset: {offset} bytes")
    
    # Extract file artifacts from the disk image using pytsk3 with the provided offset.
    artifacts = extract_file_artifacts(args.path, offset=offset)
    
    # Generate the forensic timeline with applied filters.
    timeline = generate_timeline(artifacts, start_epoch, end_epoch, args.file_type, args.directory)
    
    # Output the timeline in JSON format.
    with open(args.output, "w") as f:
        json.dump(timeline, f, indent=4)
    
    # Mark the output file as read-only.
    os.chmod(args.output, stat.S_IREAD)
    print(f"Timeline saved to {args.output}")

if __name__ == "__main__":
    main()
