import argparse
from core.disk_parser import DiskParser

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Forensic Timeline Tool")
    parser.add_argument("image", help="Path to the disk image (e.g., .dd, .img)")
    parser.add_argument("--list", action="store_true", help="List files in the root directory")
    args = parser.parse_args()

    try:
        # Initialize DiskParser
        disk_parser = DiskParser(args.image)

        if args.list:
            # List files in the root directory
            print("Listing files in the root directory...")
            files = disk_parser.list_files()

            # Print file information
            for file in files:
                print(f"Name: {file['name']}, Size: {file['size']} bytes")
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
