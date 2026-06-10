from astro.storage.manager import (
    init_astro_storage,
    save_codebase_map,
    find_workspace_root,
)
from astro.parser.code_parser import (
    get_all_py_files,
    parse_file_structure,
    calculate_file_hash,
)
import os
import json


# text formatting
class Color:
    # Text Style Codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    # Foreground Color Codes
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


def run_add(project_path="."):
    print(f"{Color.GREEN}{Color.BOLD}Astro ADD: scanning '{project_path}'{Color.RESET}")
    workspace_root = find_workspace_root(project_path)

    # create astro repository
    init_astro_storage(workspace_root)

    # old record
    cache_path = os.path.join(workspace_root, ".astro", "files_metadata.json")
    existing_records = {}

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                existing_records = json.load(f)
        except Exception:
            existing_records = {}

    updated_record = dict(existing_records)
    parsed_counter = 0

    files = get_all_py_files(project_path)
    print(f"{Color.BOLD}{Color.YELLOW}found {len(files)} files to index.{Color.RESET}")

    for file in files:
        print(f" - {file}")

    for file_path in files:
        abs_live_path = os.path.abspath(file_path)
        live_hash = calculate_file_hash(abs_live_path)

        if not live_hash:
            continue

        # FIX: Check and write consistently using absolute keys
        if (
            abs_live_path in existing_records
            and existing_records[abs_live_path].get("hash") == live_hash
        ):
            # Cache hit -> maintain the pristine absolute key entry
            updated_record[abs_live_path] = existing_records[abs_live_path]
        else:
            print(
                f"{Color.BOLD}{Color.YELLOW}File modified or new -> parsing: {file_path}{Color.RESET}"
            )
            metadata = parse_file_structure(abs_live_path)

            # Ensure internal metadata matches the absolute tracking standard
            metadata["file"] = abs_live_path
            updated_record[abs_live_path] = metadata
            parsed_counter += 1

    save_codebase_map(workspace_root, updated_record)

    # Track modified and deleted files accurately
    deleted_counter = max(0, len(existing_records) - len(updated_record))

    if parsed_counter == 0 and deleted_counter == 0:
        print(
            f"{Color.BOLD}{Color.GREEN}Everything is up to date. No changes detected.{Color.RESET}"
        )
    else:
        print(
            f"{Color.BOLD}{Color.GREEN}Sync complete. {parsed_counter} files modified, {deleted_counter} files deleted.{Color.RESET}"
        )


def run_check(path):
    print(f"Astro CHECK : Analyzing {path} for mutations...")
