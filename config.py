import logging
from pathlib import Path

import yaml

from utils import Log


class Config:
    # Default configuration settings
    # May be overridden by `my_config.yaml` (globally and/or per-project)

    projects_dir = "my_projects"
    project_name = "demo"
    project_name_locked = False  # Disable project name overwrites

    input_dirname = "input"
    templates_dirname = None  # The same as `input_dirname`
    output_dirname = "output"

    config_filename = "my_config.yaml"
    vars_filename = "vars.yaml"
    output_ext = ".txt"

    filename_variable = None
    template_subdir = "."  # No additional subdirectory
    template_name = "base"

    skip_prefix = None

    save_merged_yamls = False
    merged_yamls_path = None

    log_level = logging.WARNING  # 30
    log_style = "{"
    log_format = "[{asctime}] {levelname:<8} {message}"
    # log_format = "{message}"  # Useful for debugging
    log_datefmt = "%Y-%m-%d %H:%M:%S"  # For {asctime} variable
    log_lines = {
        1: "*" * 80,
        2: "=" * 60,
        3: "-" * 60,
    }

    _pending_logs: list[str] = []  # Store `cls` logs until logger is initialized
    log: Log | None = None  # Will be initialized later

    @classmethod
    def _init_logger(cls):
        """
        Initialize the global Log instance (once)
        """
        if cls.log is not None:
            return  # Already initialized

        logging.basicConfig(
            level=cls.log_level,
            style=cls.log_style,
            format=cls.log_format,
            datefmt=cls.log_datefmt,
        )
        cls.log = Log(log_lines=cls.log_lines)
        for msg in cls._pending_logs:
            cls.log.debug(msg)
        cls._pending_logs.clear()

    @classmethod
    def _load_yaml(cls, path: Path):
        if not path.exists():
            cls._pending_logs.append(f"Skipping {path}: Not found")
            return

        try:
            data = yaml.safe_load(path.read_text()) or {}
        except Exception as e:
            cls._pending_logs.append(f"Skipping {path}: {e}")
            return

        if not isinstance(data, dict):
            cls._pending_logs.append(f"Skipping {path}: expect mapping (like dict)")
            return

        cls._pending_logs.append(f"Start processing {path}")
        for key, value in data.items():
            if hasattr(cls, key):
                # Do not overwrite the `project_name` if locked
                if key == "project_name" and cls.project_name_locked:
                    continue

                old = getattr(cls, key)
                if old == value:
                    continue
                setattr(cls, key, value)
                cls._pending_logs.append(f"  override {key}: {old!r} -> {value!r}")
        cls._pending_logs.append(f"Done processing {path}")

    @classmethod
    def load_config(
        cls,
        project_name: str | None = None,
    ):
        """
        Load configuration from YAML files and initialize project paths and
        logger

        If `project_name` is provided, it is set and locked to prevent
        overwriting from YAML. The method loads the global and (if present)
        project-specific configurations, updates input/output/template
        directories, and initializes the logger

        Args:
            project_name (str | None): Optional fixed project name
        """
        # Lock the project_name if provided
        if project_name:
            cls.project_name = project_name
            cls.project_name_locked = True
            cls._pending_logs.append(f"Lock project_name as {project_name!r}")

        # Override defaults with global config
        cls._load_yaml(Path(cls.config_filename))

        # Construct project path from it's dir and name
        cls.project_path = str(Path(cls.projects_dir) / cls.project_name)

        # Load project's configuration
        if cls.project_path != ".":
            local_config_path = Path(cls.project_path) / cls.config_filename
            cls._load_yaml(local_config_path)

        cls.input_dir = str(Path(cls.project_path) / cls.input_dirname)
        if cls.templates_dirname:
            cls.templates_dir = str(Path(cls.project_path) / cls.templates_dirname)
        else:
            cls.templates_dir = cls.input_dir
        cls.output_dir = str(Path(cls.project_path) / cls.output_dirname)
        cls._init_logger()
