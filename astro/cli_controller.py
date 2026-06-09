from astro.storage.manager import init_astro_storage, save_codebase_map
from astro.parser.code_parser import (
    get_all_py_files,
    parse_file_structure,
    calculate_file_hash,
)
import os
import json


def run_add(project_path="."):
    print(f"Astro ADD: scanning '{project_path}'")

    # create astro repository
    init_astro_storage(project_path)

    # old record
    cache_path = os.path.join(project_path, ".astro", "files_metadata.json")
    existing_records = {}

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                existing_records = json.load(f)
        except Exception:
            existing_records = {}

    updated_record = {}
    parsed_counter = 0

    files = get_all_py_files(project_path)
    print(f"found {len(files)} files to index.")

    for file in files:
        print(f" - {file}")

    for file_path in files:
        live_hash = calculate_file_hash(file_path)

        if not live_hash:
            continue

        if (
            file_path in existing_records
            and existing_records[file_path].get("hash") == live_hash
        ): #
            updated_record[file_path] = existing_records[file_path]
        else:
            print(f"File modified or new -> parsing: {file_path}")
            metadata = parse_file_structure(file_path)
            updated_record[file_path] = metadata
            parsed_counter += 1

    save_codebase_map(project_path, updated_record)

    if parsed_counter == 0:
        print("Everything is up to date. No changes detected.")
    else:
        print(f"Sync complete. {parsed_counter} files affected.")


def run_check(path):
    print(f"Astro CHECK : Analyzing {path} for mutations...")
