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
        self.definitions = []
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
                if symbol_name not in self.definitions:
                    self.definitions.append(symbol_name)

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

                if called_node.type in ("identifier", "attribute"):
                    call_name = self.source_code[
                        called_node.start_byte : called_node.end_byte
                    ].strip()

                if call_name:
                    if self._current_definition not in self.calls:
                        self.calls[self._current_definition] = []
                    if call_name not in self.calls[self._current_definition]:
                        self.calls[self._current_definition].append(call_name)

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
