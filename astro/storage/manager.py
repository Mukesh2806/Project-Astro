import os
import json


# initiation of storage module
def init_astro_storage(project_path="."):
    # Keep the core hidden directory named after your tool: .astro/
    folder = os.path.join(project_path, ".astro")

    # This is our raw source-of-truth metadata file cache
    file_json = "files_metadata.json"
    file_astro = "graph.astro"

    full_path_json = os.path.join(folder, file_json)
    full_path_astro = os.path.join(folder, file_astro)

    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"created hidden metadata directory : {folder}/")

    if not os.path.exists(full_path_json):
        with open(full_path_json, "w") as f:
            f.write("{}")  # empty json
        print(f"initialized custom tracking file : {full_path_json}")

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
