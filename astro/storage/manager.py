import os
import json


# initiation of storage module
def init_astro_storage(project_path="."):
    # hidden storage dir as .astro extension
    folder = os.path.join(project_path, ".astro")
    file = "graph.astro"

    full_path = os.path.join(folder, file)

    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"created hidden metadata directory : {folder}/")

    if not os.path.exists(full_path):
        with open(full_path, "w") as f:
            f.write("{}")  # empty json
        print(f"initialized custom tracking file : {full_path}")


# saving codebase to graph.astro
# codebase_data: directionary
def save_codebase_map(project_path, codebase_data):
    full_path = os.path.join(project_path, ".astro", "graph.astro")

    with open(full_path, "w") as f:
        json.dump(codebase_data, f, indent=2)

    print(
        f"Codebase architecture mapping is successfully sychronized with {project_path}."
    )
