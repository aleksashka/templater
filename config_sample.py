import logging
from pathlib import Path

from logger import Log


class Config:
    # Root path for input/output directories (relative to `main.py`)
    base_dirname = "."

    # Names of working directories (inside `base_dirname`)
    input_data_dirname = "_input_data"
    input_templates_dirname = "_input_templates"
    output_data_dirname = "_output_data"

    vars_filename = "vars.yaml"
    output_ext = ".txt"

    # Name of variable to derive from target YAML filename (if unset)
    filename_variable = None  # Do not use this feature
    # filename_variable = "hostname"  # `GW01.yaml` will result in {"hostname": "GW01"}
    # filename_variable = "person.name"  # `Alex.yaml` -> {"person": {"name": "Alex"}}

    # Set to a string (e.g. "_") to skip YAMLs/dirs with this prefix. Does not
    # apply to the top-level directories (configured above)
    skip_prefix = None

    save_merged_yamls = False

    # Optional root directory for saving output (merged) YAML files.  If set to
    # None, YAML files will be saved in a "yamls" subdirectory inside the
    # `output_data_dir` directory where rendered output files are saved (e.g.,
    # _output_data/yamls/cisco_ios/router/my-device.yaml)
    #
    # If set to a string (e.g., "merged_yamls"), all YAML outputs will be saved
    # under this directory, preserving the same relative structure as the input
    # YAMLs
    #
    # Example when `merged_yamls_path` is None:
    #   _input_data/cisco_ios/router/my-device.yaml ->
    #   _output_data/yamls/cisco_ios/router/my-device.yaml
    #
    # Example when `merged_yamls_path` is "merged_yamls":
    #   _input_data/cisco_ios/router/my-device.yaml ->
    #   merged_yamls/cisco_ios/router/my-device.yaml
    #
    # merged_yamls_path = "merged_yamls"  # Save YAMLs in "merged_yamls/"
    merged_yamls_path = None  # Save YAMLs in "`input_data_dir`/yamls"

    # https://docs.python.org/3/library/logging.html#logging.basicConfig
    log_level = logging.WARNING  # Default
    # log_level = logging.INFO
    # log_level = logging.DEBUG
    log_style = "{"
    log_format = "[{asctime}] {levelname:<8} {message}"
    # log_format = "{message}"
    log_datefmt = "%Y-%m-%d %H:%M"

    log_lines = {
        1: "*" * 80,
        2: "=" * 60,
        3: "-" * 60,
    }

    input_data_dir = str(Path(base_dirname).joinpath(input_data_dirname))
    input_templates_dir = str(Path(base_dirname).joinpath(input_templates_dirname))
    output_data_dir = str(Path(base_dirname).joinpath(output_data_dirname))

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


Config._init_logger()
