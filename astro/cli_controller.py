from astro.storage.manager import init_astro_storage, save_codebase_map
from astro.parser.code_parser import get_all_py_files, parse_file_structure


def run_add(path):
    print(f"Astro ADD: scanning '{path}'")

    # create astro repository
    init_astro_storage(path)

    files = get_all_py_files(path)
    print(f"found {len(files)} files to index.")

    for file in files:
        print(f" - {file}")

    codebase_resgitry = {}
    for f in files:
        print(f"parsing structural symbols -> {f}")
        file_metadata = parse_file_structure(f)

        codebase_resgitry[f] = file_metadata

    save_codebase_map(path, codebase_resgitry)
    print("Files indexed and ready for graph mapping")


def run_check(path):
    print(f"Astro CHECK : Analyzing {path} for mutations...")
