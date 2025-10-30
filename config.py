import logging
from pathlib import Path

import yaml

from logger import Log


class Config:
    # Default configuration settings
    # May be overridden by `my_config.yaml` (globally and/or per-project)

    base_dirname = "my_projects/demo"

    input_data_dirname = "input_data"
    input_templates_dirname = "input_templates"
    output_data_dirname = "output_data"

    config_override_filename = "my_config.yaml"
    vars_filename = "vars.yaml"
    output_ext = ".txt"

    filename_variable = None

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
                old = getattr(cls, key)
                setattr(cls, key, value)
                cls._pending_logs.append(f"  override {key}: {old!r} -> {value!r}")
        cls._pending_logs.append(f"Done processing {path}")

    @classmethod
    def apply_overrides(cls):
        """
        Load global and optional local `cls.config_override_filename`
        """
        # Global override
        cls._load_yaml(Path(cls.config_override_filename))

        # Local override if base_dirname != "."
        if cls.base_dirname != ".":
            local_path = Path(cls.base_dirname) / cls.config_override_filename
            cls._load_yaml(local_path)

        cls.input_data_dir = str(Path(cls.base_dirname) / cls.input_data_dirname)
        cls.input_templates_dir = str(
            Path(cls.base_dirname) / cls.input_templates_dirname
        )
        cls.output_data_dir = str(Path(cls.base_dirname) / cls.output_data_dirname)


Config.apply_overrides()
Config._init_logger()
