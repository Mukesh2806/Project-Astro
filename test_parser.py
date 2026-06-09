import json
import os
from tree_sitter import Language, Parser
import tree_sitter_python as tsPython

# 1. Setup the exact parsing infrastructure locally
PY_LANGUAGE = Language(tsPython.language())
parser = Parser(PY_LANGUAGE)

test_target = "./astro/cli_controller.py"

print("=" * 60)
print(f"STARTING TREE-SITTER GRAMMAR INSPECTION ON: {test_target}")
print("=" * 60)

if not os.path.exists(test_target):
    print(f"ERROR: Could not find file at {test_target}")
    print("Please ensure your script is running from the project root directory.")
    exit(1)

with open(test_target, "r", encoding="utf-8") as f:
    source_code = f.read()

tree = parser.parse(bytes(source_code, "utf8"))
root_node = tree.root_node

definitions = []
dependencies = []
errors = []

print("\n--- LIVE AST TRAVERSAL LOG ---")
print("Printing every node related to imports found in your file:\n")


def traverse(node):
    # Log any node that looks like an import statement or contains errors
    if (
        "import" in node.type
        or "statement" in node.type
        or node.type in ("ERROR", "MISSING")
    ):
        line_num = node.start_point[0] + 1
        node_text = (
            source_code[node.start_byte : node.end_byte].strip().replace("\n", " ")
        )
        print(f"[Line {line_num}] Type: '{node.type}' -> Text: \"{node_text}\"")

    # Your parsing extraction logic
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
            target_node = child
            if child.type == "aliased_import":
                target_node = child.child_by_field_name("name") or child

            if target_node and target_node.type == "dotted_name":
                module_name = source_code[
                    target_node.start_byte : target_node.end_byte
                ].strip()
                if module_name not in dependencies:
                    dependencies.append(module_name)

    elif node.type == "from_import_statement":
        module_node = node.child_by_field_name("module")
        if module_node:
            module_name = source_code[
                module_node.start_byte : module_node.end_byte
            ].strip()
            if module_name not in dependencies:
                dependencies.append(module_name)

    for child in node.children:
        traverse(child)


# Run the inspection loop
traverse(root_node)

print("\n" + "=" * 60)
print("FINAL EXTRACTED JSON OUTPUT")
print("=" * 60)

final_output = {
    "file": test_target,
    "definitions": definitions,
    "dependencies": dependencies,
    "errors": errors,
}

print(json.dumps(final_output, indent=2))
