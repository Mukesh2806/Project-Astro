import os
import json

# find true project root
def find_workspace_root(start_path = "."):
    # Traces upward from target path until it finds root anchor files
    curr_dir = os.path.abspath(start_path)

    root_anchors = {"main.py", ".git", ".astro", "requirements.txt", "pyproject.toml"}

    while True:
        curr_content = set(os.listdir(curr_dir))
        if curr_content.intersection(root_anchors):
            return curr_dir
        
        parent_dir = os.path.dirname(curr_dir)

        if parent_dir == curr_dir:
            return os.path.abspath(start_path)
        
        curr_dir = parent_dir

# initiation of storage module
def init_astro_storage(project_path="."):
    # Keep the core hidden directory named after your tool: .astro/
    folder = os.path.join(project_path, ".astro")

    # This is our raw source-of-truth metadata file cache
    file_json = "files_metadata.json"
    graphs = ["file_graph.astro", "symbol_graph.astro", "unified_graph.astro"]


    full_path_json = os.path.join(folder, file_json)

    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"created hidden metadata directory : {folder}/")

    if not os.path.exists(full_path_json):
        with open(full_path_json, "w") as f:
            f.write("{}")  # empty json
        print(f"initialized custom tracking file : {full_path_json}")

    for f in graphs:
        full_path_astro = os.path.join(folder, f)

        if not os.path.exists(full_path_astro):
            with open(full_path_astro, "w") as f:
                f.write("{}")  # empty json
            print(f"initialized custom tracking file : {full_path_astro}")


# saving codebase to files_metadata.json
# codebase_data: dictionary
def save_codebase_map(project_path, codebase_data):
    full_path = os.path.join(project_path, ".astro", "files_metadata.json")

    with open(full_path, "w") as f:
        json.dump(codebase_data, f, indent=2)

    print(f"Codebase raw metadata architecture successfully cached inside {full_path}.")
