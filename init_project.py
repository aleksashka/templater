import sys
import time
import shutil
from pathlib import Path

from utils import make_parser


args = make_parser("Initialize the project").parse_args()


def main():
    required_files = {
        "my_config.yaml": "my_config_sample.yaml",
    }
    make_sure_required_files_are_present(required_files)

    from config import Config

    Config.load_config(project_name=args.project_name)

    required_dirs = [
        Path(Config.input_dir),
        Path(Config.templates_dir),
        Path(Config.output_dir),
        Path(Config.output_yamls_dir),
    ]
    create_working_directories(required_dirs, timeout=10)


def make_sure_required_files_are_present(required_files: dict[str, str]):
    ok_to_continue = True

    for target, source in required_files.items():
        target_path = Path(target)
        source_path = Path(source)

        if target_path.exists():
            print(f"[.] Already exists: {target!r}")
        else:  # No `target` -> create a copy
            if source_path.exists():
                shutil.copy(source_path, target_path)
                print(f"[+] Created a copy: {target!r} from {source!r}")
            else:  # No `source`
                print(f"[!] Not found: {source!r} (skipping {target!r})")
                ok_to_continue = False

    if not ok_to_continue:
        print(
            "[!] Exiting the script since some required files (see above) are "
            "missing (check the git repository for them)"
        )
        sys.exit()


def create_working_directories(required_dirs: list[Path], timeout=10):
    print(
        f"[!] In {timeout} seconds I will create the following directories:",
        *(f"  {item}" for item in required_dirs),
        "[!] Press Ctrl+C to abort",
        sep="\n",
    )

    try:
        for i in range(timeout, 0, -1):
            print(f"[i] Continuing in {i} seconds...", end="\r", flush=True)
            time.sleep(1)
            print(" " * 40, end="\r")  # clear line
    except KeyboardInterrupt:
        print("\n[i] You may want to update config.py and run again")
        print("[i] Exiting...")
        sys.exit()

    for path in required_dirs:
        if path.exists():
            print(f"[.] Already exists: {str(path)!r}")
            continue
        path.mkdir(parents=True, exist_ok=True)
        print(f"[+] Created dir: {str(path)!r}")


if __name__ == "__main__":
    main()
