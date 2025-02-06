import pytsk3

class DiskParser:
    def __init__(self, image_path):
        """
        Initialize the DiskParser with the path to the disk image.
        :param image_path: Path to the disk image file (e.g., .dd, .img).
        """
        self.image_path = image_path
        try:
            # Open the disk image using pytsk3
            self.img_info = pytsk3.Img_Info(self.image_path)
        except Exception as e:
            raise ValueError(f"Failed to open disk image: {e}")

    def list_files(self, path="/"):
        """
        List files and directories in the specified path.
        :param path: Path to list files from (default is root "/").
        :return: List of dictionaries containing file metadata.
        """
        try:
            # Open the file system
            fs_info = pytsk3.FS_Info(self.img_info)

            # Open the directory at the specified path
            directory = fs_info.open_dir(path=path)

            files = []
            for entry in directory:
                if entry.info.name is None or entry.info.meta is None:
                    continue  # Skip entries without name or metadata

                try:
                    # Extract file metadata
                    file_info = {
                        "name": entry.info.name.name.decode("utf-8", errors="ignore"),
                        "type": entry.info.name.type,
                        "size": entry.info.meta.size if entry.info.meta else 0,
                        "meta": entry.info.meta,
                    }
                    files.append(file_info)
                except Exception as e:
                    print(f"Error processing file: {e}")

            return files
        except Exception as e:
            raise RuntimeError(f"Failed to list files: {e}")
