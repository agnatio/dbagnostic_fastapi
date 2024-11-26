import os


def list_files(
    startpath,
    remove_objects=None,
    max_levels=None,
):
    if remove_objects is None:
        remove_objects = ["_delete/", "__pycache__", "alembic", "node_modules"]

    result = []

    # Initial display for the root directory
    result.append("./")

    for root, dirs, files in os.walk(startpath):
        # Remove unwanted directories
        dirs[:] = [d for d in dirs if d not in remove_objects]

        level = root.replace(startpath, "").count(os.sep)

        # Skip levels beyond max_levels if specified
        if max_levels is not None and level > max_levels:
            continue

        # Format directory and file output
        indent = " " * 4 * level + ("├── " if level > 0 else "")
        result.append(f"{indent}{os.path.basename(root)}/")

        subindent = " " * 4 * (level + 1) + "├── "
        for f in files:
            result.append(f"{subindent}{f}")

    return "\n".join(result)


if __name__ == "__main__":
    remove_objects = ["venv", ".git"]

    # Get the list of files
    folder_structure = list_files(".", max_levels=3, remove_objects=remove_objects)

    # Print to console
    print(folder_structure)

    # Save the folder structure to folders.txt
    with open("folders.txt", "w") as f:
        f.write(folder_structure)
