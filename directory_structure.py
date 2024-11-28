import os


def parse_gitignore(gitignore_path):
    """Parse .gitignore file and return list of patterns."""
    # Default patterns that should always be ignored
    patterns = [
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "*.py[cod]",
    ]

    if not os.path.exists(gitignore_path):
        return patterns

    with open(gitignore_path, "r") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                # Convert pattern to normalized form
                pattern = line.replace("\\", "/")
                patterns.append(pattern)
    return patterns


def should_ignore(path, patterns):
    """Check if path matches any gitignore pattern."""
    normalized_path = path.replace("\\", "/").rstrip("/")

    for pattern in patterns:
        pattern = pattern.rstrip("/")

        # Handle directory-specific patterns
        if pattern.endswith("/"):
            if normalized_path.endswith(pattern[:-1]) or normalized_path.startswith(
                pattern[:-1]
            ):
                return True
            continue

        # Handle glob patterns
        if "*" in pattern:
            # Convert glob pattern to parts
            parts = pattern.split("*")
            if len(parts) == 1:
                if pattern in normalized_path:
                    return True
            else:
                # Check if all parts match in order
                current_path = normalized_path
                matches = True
                for part in parts:
                    if not part:
                        continue
                    idx = current_path.find(part)
                    if idx == -1:
                        matches = False
                        break
                    current_path = current_path[idx + len(part) :]
                if matches:
                    return True
        else:
            # Direct match
            if pattern in normalized_path or normalized_path.endswith("/" + pattern):
                return True

    return False


def list_files(
    startpath,
    remove_objects=None,
    max_levels=None,
):
    if remove_objects is None:
        remove_objects = ["_delete/", "alembic", "node_modules"]

    # Parse .gitignore patterns
    gitignore_patterns = parse_gitignore(os.path.join(startpath, ".gitignore"))

    result = []
    result.append("./")

    for root, dirs, files in os.walk(startpath):
        # Get relative path for gitignore matching
        rel_path = os.path.relpath(root, startpath)
        if rel_path == ".":
            rel_path = ""

        # Filter directories
        dirs[:] = [
            d
            for d in dirs
            if d not in remove_objects
            and not should_ignore(d, gitignore_patterns)  # Check dir name
            and not should_ignore(os.path.join(rel_path, d), gitignore_patterns)
        ]  # Check full path

        level = root.replace(startpath, "").count(os.sep)

        # Skip levels beyond max_levels if specified
        if max_levels is not None and level > max_levels:
            continue

        # Only add directory to output if it's not ignored
        if not should_ignore(rel_path, gitignore_patterns):
            indent = " " * 4 * level + ("├── " if level > 0 else "")
            result.append(f"{indent}{os.path.basename(root)}/")

            # Filter and format file output
            subindent = " " * 4 * (level + 1) + "├── "
            filtered_files = [
                f
                for f in files
                if not should_ignore(f, gitignore_patterns)  # Check filename
                and not should_ignore(os.path.join(rel_path, f), gitignore_patterns)
            ]  # Check full path

            for f in filtered_files:
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
