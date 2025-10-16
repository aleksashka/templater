import logging


class Config:
    device_yamls_dir = "device_yamls"
    output_dir = "device_configs"
    templates_dir = "templates"
    vars_filename = "vars.yaml"

    # https://docs.python.org/3/library/logging.html#logging.basicConfig
    log_level = logging.WARNING
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
