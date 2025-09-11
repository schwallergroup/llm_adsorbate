def read_file(file_path: str) -> str:
    """Read the content of a file and return it as a string."""
    with open(file_path, 'r') as file:
        content = file.read()
    return content

registered_tools = {
    "read_file": read_file,
}