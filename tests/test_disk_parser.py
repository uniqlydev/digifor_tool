from forensic_tool.core.disk_parser import DiskParser

def main():
    # Path to your disk image
    image_path = "disk_images/sample.dd"

    # Create DiskParser instance
    parser = DiskParser(image_path)

    # List files in the root directory
    files = parser.list_files()

    # Print file information
    for file in files:
        print(f"Name: {file['name']}, Size: {file['size']} bytes")

if __name__ == "__main__":
    main()
