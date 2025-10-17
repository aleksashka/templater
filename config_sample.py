import logging


class Config:
    device_yamls_dir = "device_yamls"
    output_dir = "device_configs"
    templates_dir = "templates"
    vars_filename = "vars.yaml"
    skip_prefix = "_"

    save_device_yamls = False

    # Optional root directory for saving final merged YAML files. If set to a
    # string (e.g., "merged_yamls"), all YAML outputs will be saved under this
    # directory, preserving the same relative structure as the input YAMLs. If
    # set to None, YAML files will be saved in a "yamls" subdirectory inside the
    # output directory where rendered .txt configs are saved (e.g.,
    # device_configs/yamls/cisco_ios/router/my-device.yaml).
    #
    # Example when device_yamls_path is set to "merged_yamls":
    #   device_yamls/cisco_ios/router/my-device.yaml ->
    #   merged_yamls/cisco_ios/router/my-device.yaml
    #
    # Example when device_yamls_path is None:
    #   device_yamls/cisco_ios/router/my-device.yaml ->
    #   device_configs/yamls/cisco_ios/router/my-device.yaml
    # device_yamls_path = None
    device_yamls_path = "merged_yamls"

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
