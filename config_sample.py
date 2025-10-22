import logging


class Config:
    input_data_dir = "_input_data"
    input_templates_dir = "_input_templates"
    output_data_dir = "_output_data"
    vars_filename = "vars.yaml"

    # Set to a string (e.g. "_") to skip YAMLs/dirs with this prefix
    skip_prefix = None

    save_merged_yamls = False

    # Optional root directory for saving output (merged) YAML files.  If set to
    # None, YAML files will be saved in a "yamls" subdirectory inside the
    # `output_data_dir` directory where rendered .txt configs are saved (e.g.,
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
        1: "=" * 80,
        2: "=" * 60,
        3: "-" * 60,
    }
