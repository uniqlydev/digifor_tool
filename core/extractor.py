import pytsk3
import os

# Define the flag for unallocated (deleted) files.
TSK_FS_META_FLAG_UNALLOC = 0x01 # first bit is used to indicate that a file entry is unallocated

def traverse_directory(fs_info, directory, parent_path=""):
    artifacts = []
    for entry in directory:
        # Skip special entries.
        if entry.info.name.name in [b'.', b'..']:
            continue

        try:
            entry_name = entry.info.name.name.decode("utf-8", errors="replace")
        except Exception:
            entry_name = str(entry.info.name.name)

        # Build the full path.
        full_path = os.path.join(parent_path, entry_name)

        # Verify metadata is available.
        if not hasattr(entry, "info") or not hasattr(entry.info, "meta"):
            continue

        meta = entry.info.meta
        if meta is None:
            continue

        # Check if the file is deleted (unallocated).
        deleted = bool(meta.flags & TSK_FS_META_FLAG_UNALLOC)

        artifact = {
            "path": full_path,
            "name": entry_name,
            "modified": meta.mtime,  # Modification time (epoch)
            "accessed": meta.atime,  # Access time (epoch)
            "created": meta.crtime,  # Creation time (epoch)
            "deleted": deleted       # True if file is marked as deleted
        }
        artifacts.append(artifact)

        # If the entry is a directory, recursively traverse it.
        if meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
            try:
                sub_directory = fs_info.open_dir(inode=meta.addr)
                artifacts.extend(traverse_directory(fs_info, sub_directory, full_path))
            except Exception as e:
                print(f"Error opening subdirectory {full_path}: {e}")
    return artifacts

def extract_file_artifacts(image_path, offset=0):
    artifacts = []
    try:
        # Open the disk image.
        img_info = pytsk3.Img_Info(image_path)
        # Open the file system with the provided offset.
        fs_info = pytsk3.FS_Info(img_info, offset=offset)
        # Start at the root directory.
        root_dir = fs_info.open_dir(path="/")
        artifacts = traverse_directory(fs_info, root_dir, "/")
    except Exception as e:
        print(f"Error opening disk image {image_path}: {e}")
    return artifacts
