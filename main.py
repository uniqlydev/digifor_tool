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

def generate_timeline(artifacts, start_epoch=None, end_epoch=None):
    timeline = []
    
    for artifact in artifacts:
        events = []
        if artifact["created"]:
            events.append(("created", artifact["created"]))
        if artifact["modified"] and artifact["modified"] != artifact["created"]:
            events.append(("modified", artifact["modified"]))
        if artifact.get("deleted"):
            events.append(("deleted", artifact["modified"]))
        
        for event_type, timestamp in events:
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
    from dfvfs.path import os_path_spec, raw_path_spec
    from dfvfs.volume import tsk_volume_system

    resolver_context = Context()

    # Step 1: OS path to the image file
    os_spec = os_path_spec.OSPathSpec(location=image_path)

    # Step 2: Wrap it in a raw path spec
    raw_spec = raw_path_spec.RawPathSpec(parent=os_spec)

    try:
        file_object = resolver.Resolver.OpenFileObject(raw_spec, resolver_context=resolver_context)
        volume_system = tsk_volume_system.TSKVolumeSystem()
        volume_system.Open(file_object)
        volume = volume_system.GetVolume(0)
        offset = volume.start_offset * volume_system.block_size
        return offset
    except Exception as e:
        print(f"Error retrieving volume offset: {e}")
        return 0



def main():
    parser = argparse.ArgumentParser(
        description="Extract file system artifacts and generate a forensic timeline using dfVFS, pytsk3, and pandas."
    )
    parser.add_argument("--path", required=True, help="Path to the disk image file")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD) to filter events")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD) to filter events")
    parser.add_argument("--output", default="forensic_timeline.json", help="Output file name")
    args = parser.parse_args()
    
    start_epoch = parse_date(args.start_date) if args.start_date else None
    end_epoch = parse_date(args.end_date) if args.end_date else None

    offset = get_volume_offset(args.path)
    print(f"Using file system offset: {offset} bytes")

    artifacts = extract_file_artifacts(args.path, offset=offset)
    timeline = generate_timeline(artifacts, start_epoch, end_epoch)

    with open(args.output, "w") as f:
        json.dump(timeline, f, indent=4)

    os.chmod(args.output, stat.S_IREAD)
    print(f"Timeline saved to {args.output}")

if __name__ == "__main__":
    main()
