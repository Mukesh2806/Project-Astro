from tree_sitter import Language, Parser
import tree_sitter_python as tsPython
import os

# pre-build language object
PY_LANGUAGE = Language(tsPython.language())


# get all .py files
def get_all_py_files(root_path):
    py_files = []

    ignored_directories = {
        ".astro",
        ".git",
        "astroEnv",
        "venv",
        "env",
        "__pycache__",
        "lib",
        "Lib",
    }

    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in ignored_directories]
        for file in filenames:
            if file.endswith(".py") and file != "main.py":
                full_path = os.path.join(dirpath, file)
                py_files.append(full_path)

    return py_files


# tree-sitter-parser logic
def parse_file_structure(file_path):
    """
    Reads a real python source file and uses tree-sitter to extract real metadata
    """
    definitions = []
    dependencies = []
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {"file": file_path, "definitions": [], "dependencies": [], "errors": []}

    parser = Parser(PY_LANGUAGE)
    tree = parser.parse(bytes(source_code, "utf8"))
    root_node = tree.root_node

    # dfs tree traversal
    def traverse(node):
        if node.type in ("ERROR", "MISSING"):
            line_num = node.start_point[0] + 1
            col_num = node.start_point[1]

            errors.append({"type": node.type, "line": line_num, "column": col_num})

        elif node.type in ("function_definition", "class_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                symbol_name = source_code[name_node.start_byte : name_node.end_byte]
                definitions.append(symbol_name)
        elif node.type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    module_name = source_code[child.start_byte : child.end_byte]
                    dependencies.append(module_name)
        elif node.type == "import_from_statement":
            module_node = node.child_by_field_name("module")
            if module_node:
                module_name = source_code[module_node.start_byte : module_node.end_byte]
                dependencies.append(module_name)

        for child in node.children:
            traverse(child)

    traverse(root_node)

    return {
        "file": file_path,
        "definitions": definitions,
        "dependencies": dependencies,
        "errors": errors,
    }
