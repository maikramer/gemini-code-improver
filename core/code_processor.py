import re

def extract_classes(filepath):
    """
    Extracts class definitions from a C++ source file.

    Args:
        filepath (str): The path to the C++ source file.

    Returns:
        list: A list of class names found in the file.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    class_regex = re.compile(r"\bclass\s+(\w+)\s*\{")
    return class_regex.findall(content)