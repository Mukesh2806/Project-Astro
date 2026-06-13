from tree_sitter import Language, Parser
import tree_sitter_python as tsPython
import os
import hashlib

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


class CodeParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.definitions = {"class_definition": {}, "function_definition": {}}
        self.dependencies = {}
        self.calls = {}
        self.errors = []
        self.file_hash = self._calculate_file_hash()
        self.source_code = ""

        self._current_definition = None

    def _calculate_file_hash(self) -> str:
        # Generates a unique MD5 fingerprint based on the file's text content.
        hasher = hashlib.md5()
        try:
            with open(self.file_path, "rb") as f:
                buf = f.read()
                hasher.update(buf)
            return hasher.hexdigest()
        except Exception:
            return ""

    def _read_file(self) -> bool:
        # to read file source text safely into memory
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.source_code = f.read()
            return True
        except Exception as e:
            self.errors.append({"type": "READ_ERROR", "message": str(e)})
            return False

    def _clean_import_symbols(self, raw_symbols_str: str) -> list[str]:
        # cleans from import statements string as strip alias like symbols to
        cleaned_sym = (
            raw_symbols_str.replace("\n", " ")
            .replace("\r", " ")
            .replace("(", "")
            .replace(")", "")
        )

        parts = [s.strip() for s in cleaned_sym.split(",") if s.strip()]

        final_symbols = [
            part.split(" as ")[0].strip() if " as " in part else part for part in parts
        ]

        return final_symbols

    def _traverse(self, node):
        # internal recursive AST walker

        # Layer 1: catch syntax errors
        if node.type in ("ERROR", "MISSING"):
            line_num = node.start_point[0] + 1
            col_num = node.start_point[1]
            self.errors.append({"type": node.type, "line": line_num, "column": col_num})

        # Layer 2: symbol definitions
        elif node.type in ("function_definition", "class_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                symbol_name = self.source_code[
                    name_node.start_byte : name_node.end_byte
                ].strip()

                target_registry = self.definitions.get(node.type)

                # 1. Ensure the structure entry exists in our primary storage
                if symbol_name not in target_registry:
                    target_registry[symbol_name] = {"parameters": []}

                # 2. Extract and populate parameters if it's a function and array is empty
                if (
                    node.type == "function_definition"
                    and not target_registry[symbol_name]["parameters"]
                ):
                    # Look for the parameter list block directly by its node type
                    parameter_node = None
                    for child in node.children:
                        if child.type == "parameters":
                            parameter_node = child
                            break

                    if parameter_node:
                        for param_child in parameter_node.children:
                            if param_child.type not in ("(", ")", ","):
                                # Case A: The parameter has an explicit type hint (e.g., path: str)
                                if param_child.type == "typed_parameter":
                                    p_name_node = param_child.child_by_field_name(
                                        "name"
                                    )
                                    p_type_node = param_child.child_by_field_name(
                                        "type"
                                    )

                                    p_name = "unknown"
                                    p_type = "Any"

                                    if p_name_node and p_type_node:
                                        p_name = self.source_code[
                                            p_name_node.start_byte : p_name_node.end_byte
                                        ].strip()
                                        p_type = self.source_code[
                                            p_type_node.start_byte : p_type_node.end_byte
                                        ].strip()
                                    else:
                                        if hasattr(param_child, "text"):
                                            try:
                                                p_full_text = param_child.text.decode(
                                                    "utf-8"
                                                ).split(": ")
                                                if len(p_full_text) == 2:
                                                    p_name = p_full_text[0].strip()
                                                    p_type = p_full_text[1].strip()
                                                else:
                                                    p_name = p_full_text[0].strip()
                                            except Exception:
                                                pass

                                    target_registry[symbol_name]["parameters"].append(
                                        {"name": p_name, "type": p_type}
                                    )

                                # Case B: The parameter has a default value assignment (e.g., project_path=".")
                                elif param_child.type == "default_parameter":
                                    p_name_node = param_child.child_by_field_name(
                                        "name"
                                    )
                                    p_name = "unknown"
                                    p_type = "Any"

                                    # Check if the parameter name itself contains an inner type hint
                                    if p_name_node:
                                        if p_name_node.type == "typed_parameter":
                                            inner_name = (
                                                p_name_node.child_by_field_name("name")
                                            )
                                            inner_type = (
                                                p_name_node.child_by_field_name("type")
                                            )
                                            if inner_name:
                                                p_name = self.source_code[
                                                    inner_name.start_byte : inner_name.end_byte
                                                ].strip()
                                            if inner_type:
                                                p_type = self.source_code[
                                                    inner_type.start_byte : inner_type.end_byte
                                                ].strip()
                                        else:
                                            p_name = self.source_code[
                                                p_name_node.start_byte : p_name_node.end_byte
                                            ].strip()

                                    target_registry[symbol_name]["parameters"].append(
                                        {"name": p_name, "type": p_type}
                                    )

                                # Case C: The parameter is a raw identifier with no hint or assignment (e.g., self)
                                elif param_child.type == "identifier":
                                    p_name = self.source_code[
                                        param_child.start_byte : param_child.end_byte
                                    ].strip()

                                    target_registry[symbol_name]["parameters"].append(
                                        {"name": p_name, "type": "Any"}
                                    )

                # Maintain your scope state machine tracker for recursive depth mapping
                old_scope = self._current_definition
                self._current_definition = symbol_name

                for child in node.children:
                    self._traverse(child)

                self._current_definition = old_scope
                return

        # layer 3: local call-graph linker
        elif node.type == "call":
            if self._current_definition is not None:
                called_node = node.children[0]
                call_name = None

                if called_node.type == "identifier":
                    call_name = self.source_code[
                        called_node.start_byte : called_node.end_byte
                    ].strip()

                elif called_node.type == "attribute":
                    attribute_node = called_node.child_by_field_name("attribute")
                    if attribute_node:
                        call_name = self.source_code[
                            attribute_node.start_byte : attribute_node.end_byte
                        ].strip()
                    else:
                        call_name = self.source_code[
                            called_node.start_byte : called_node.end_byte
                        ].strip()

                if call_name:
                    line_num = node.start_point[0] + 1
                    col_num = node.start_point[1]

                    extracted_arguments = []

                    arg_list_node = None
                    for child in node.children:
                        if child.type == "argument_list":
                            arg_list_node = child
                            break

                    if arg_list_node:
                        for arg_child in arg_list_node.children:
                            if arg_child.type not in ("(", ")", ","):
                                arg_value = self.source_code[
                                    arg_child.start_byte : arg_child.end_byte
                                ].strip()

                                extracted_arguments.append(
                                    {"value": arg_value, "node_type": arg_child.type}
                                )

                    call_meta = {
                        "name": call_name,
                        "arguments": extracted_arguments,
                        "line": line_num,
                        "column": col_num,
                    }

                    if self._current_definition not in self.calls:
                        self.calls[self._current_definition] = []

                    self.calls[self._current_definition].append(call_meta)

        # layer 4 : standard imports
        elif node.type == "import_statement":
            for child in node.children:
                target_node = child
                if child.type == "aliased_import":
                    target_node = child.child_by_field_name("name")

                if target_node and target_node.type == "dotted_name":
                    module_name = self.source_code[
                        target_node.start_byte : target_node.end_byte
                    ]
                    if module_name not in self.dependencies:
                        self.dependencies[module_name] = []

        # layer 5 : From-Imports
        elif node.type == "import_from_statement":
            module_node = node.child_by_field_name("module")
            if module_node:
                module_name = self.source_code[
                    module_node.start_byte : module_node.end_byte
                ]
                full_line_text = self.source_code[node.start_byte : node.end_byte]

                if " import " in full_line_text:
                    raw_symbols = full_line_text.split(" import ")[1]
                    clean_symbols = self._clean_import_symbols(raw_symbols)

                    if module_name in self.dependencies:
                        self.dependencies[module_name] = list(
                            set(self.dependencies[module_name] + clean_symbols)
                        )
                    else:
                        self.dependencies[module_name] = clean_symbols
                else:
                    if module_name not in self.dependencies:
                        self.dependencies[module_name] = []

        # default fallthrough sweep
        for child in node.children:
            self._traverse(child)

    def get_manifest(self) -> dict:
        # format collected metadata into standard structural database schema

        return {
            "file": self.file_path,
            "hash": self.file_hash,
            "definitions": self.definitions,
            "calls": self.calls,
            "dependencies": self.dependencies,
            "errors": self.errors,
        }

    def parse(self) -> dict:
        # starts parse engine and returns complied file with dict

        if not self._read_file():
            return self.get_manifest()

        parser = Parser(PY_LANGUAGE)
        tree = parser.parse(bytes(self.source_code, "utf8"))

        self._traverse(tree.root_node)
        return self.get_manifest()


"""
"definitions": {
  "function_definition": {
    "run_add": {
      "parameters": [
        { "name": "self", "type": "Any" },
        { "name": "workspace_path", "type": "str" }
      ]
    }
  }
}

"calls": {
  "run_add": [
    { "name": "print", "line": 12, "column": 8 },
    { "name": "find_workspace_root", "line": 14, "column": 21 },
    { "name": "print", "line": 25, "column": 8 }
  ]
}



{
  "file": "astro/storage/manager.py",
  "hash": "b10a8db164e0754105b7a99be72e3fe5",
  
  "definitions": [
    "init_astro_storage",
    "save_codebase_map"
  ],

  "calls": {
    "init_astro_storage": [
      "os.path.exists",
      "os.makedirs"
    ],
    "save_codebase_map": [
      "calculate_file_hash",
      "print"
    ]
  },

  "dependencies": {
    "os": [],
    "hashlib": [],
    "astro.parser.code_parser": [
      "calculate_file_hash"
    ]
  },

  "errors": [
    {
      "type": "MISSING",
      "line": 13,
      "column": 20
    }
  ]
}
"""
