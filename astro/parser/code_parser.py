from tree_sitter import Language, Parser
import tree_sitter_python as tsPython
import os
import hashlib


def calculate_file_hash(file_path):
    # Generates a unique MD5 fingerprint based on the file's text content.
    hasher = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception:
        return None


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
    dependencies = {}
    calls = {}
    errors = []

    current_definition = [None]
    file_hash = calculate_file_hash(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {"file": file_path, "definitions": [], "dependencies": {}, "errors": []}

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
                if symbol_name not in definitions:
                    definitions.append(symbol_name)
                # ***
                old_scope = current_definition[0]
                current_definition[0] = symbol_name

                for child in node.children:
                    traverse(child)

                current_definition[0] = old_scope
                return

        elif node.type == "import_statement":
            for child in node.children:
                target_node = child
                if child.type == "aliased_import":
                    target_node = child.child_by_field_name("name") or child

                if target_node and target_node.type == "dotted_name":
                    module_name = source_code[
                        target_node.start_byte : target_node.end_byte
                    ].strip()
                    if module_name not in dependencies:
                        dependencies[module_name] = []

        elif node.type == "import_from_statement":
            module_name = None
            for child in node.children:
                if child.type == "dotted_name":
                    module_name = source_code[child.start_byte : child.end_byte].strip()
                    break

            if module_name:
                full_line_text = source_code[node.start_byte : node.end_byte]

                cleaned_text = full_line_text.replace("\n", " ").replace("\r", " ")
                cleaned_text = cleaned_text.replace("(", "").replace(")", "")

                if " import " in cleaned_text:
                    parts = cleaned_text.split(" import ")
                    raw_symbols = parts[
                        1
                    ]  # This is "init_astro_storage, save_codebase_map"

                    imported_symbols = [
                        s.strip() for s in raw_symbols.split(",") if s.strip()
                    ]

                    clean_symbols = []
                    for sym in imported_symbols:
                        if " as " in sym:
                            clean_symbols.append(sym.split(" as ")[0].strip())
                        else:
                            clean_symbols.append(sym)

                    if module_name in dependencies:
                        dependencies[module_name] = list(
                            set(dependencies[module_name] + clean_symbols)
                        )
                    else:
                        dependencies[module_name] = clean_symbols

                else:
                    if module_name not in dependencies:
                        dependencies[module_name] = []

        for child in node.children:
            traverse(child)

    traverse(root_node)

    return {
        "file": file_path,
        "definitions": definitions,
        "dependencies": dependencies,
        "errors": errors,
        "hash": file_hash,
    }


"""
{

  "definitions": [

    "calculate_file_hash",

    "get_all_py_files",

    "parse_file_structure",

    "traverse"

  ],
  "calls": {

    "parse_file_structure": [

      "calculate_file_hash",

      "traverse"

    ],
    "traverse": []

  }

}
"""
