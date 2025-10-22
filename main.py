import os
import copy
import logging
from typing import Generator

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from logger import Log
from config import Config


logging.basicConfig(
    level=Config.log_level,
    style=Config.log_style,
    format=Config.log_format,
    datefmt=Config.log_datefmt,
)


log = Log()
env = Environment(
    loader=FileSystemLoader(Config.input_templates_dir),
    autoescape=select_autoescape(disabled_extensions=("j2", "txt", "yaml")),
)


def main():
    for yaml_path in find_yaml_files(Config.input_data_dir):
        generate_config(yaml_path)


def path_should_be_skipped(path: str) -> bool:
    """
    Checks if the given path should be skipped based on the configured prefix.
    """
    if Config.skip_prefix is None:
        return False
    return path.startswith(Config.skip_prefix)


def find_yaml_files(root_dir: str) -> Generator[str, None, None]:
    """
    Recursively walks through the directory tree starting from `root_dir`,
    yielding paths to all `.yaml` files except those named as
    Config.`vars_filename`

    Args:
        root_dir (str): Root (starting) directory to search for YAML files

    Yields:
        str: Full path to each YAML file (excluding `Config.vars_filename`)
    """
    for dirpath, _, filenames in os.walk(root_dir):
        if path_should_be_skipped(os.path.basename(dirpath)):
            # Ignore dirs with configured `skip_prefix`
            continue
        for file in filenames:
            if path_should_be_skipped(file):
                # Ignore files with configured `skip_prefix`
                continue
            if not file.endswith(".yaml"):
                # Ignore non-yaml files
                continue
            if file == Config.vars_filename:
                # Ignore `vars_filename` files
                continue
            yield os.path.join(dirpath, file)


def generate_config(yaml_path: str):
    """
    Generates a configuration file for a network device based on a YAML
    definition

    This function:
    - Loads the device-specific YAML data, noting `device_type` (directory name
        inside Config.`input_data_dir`)
    - Merges it with inherited variables from all applicable
        Config.`vars_filename` files
    - Selects the appropriate base Jinja2 template based on the `device_type`
    - Renders the configuration
    - Writes the output (configuration and optinally merged YAML)

    Args:
        yaml_path (str): Full path to the device YAML file
    """

    # Compute path relative to the `input_data_dir`
    relative_path = os.path.relpath(yaml_path, Config.input_data_dir)

    # Merge all inherited and device-specific variables
    merged_vars = load_vars_hierarchy(relative_path)
    if merged_vars is None:
        return

    # Add "device_type" key
    merged_vars["device_type"] = get_device_type(relative_path)

    # Select template based on top-level device type (e.g. "cisco_ios")
    template_path = f"{merged_vars['device_type']}/base.j2"
    try:
        template = env.get_template(template_path)
    except Exception as error:
        log.error(f"Error while loading template '{template_path}': {error}")
        return

    # Render the final configuration
    rendered_config = template.render(merged_vars)

    # Save configuration (and optionally merged YAML)
    config_path = save_output_files(relative_path, rendered_config, merged_vars)
    log.info(f"Created: {config_path}")


def save_output_files(
    relative_path: str,
    rendered_config: str,
    merged_vars: dict,
) -> str:
    """
    Save the rendered device configuration and optionally the merged YAML
    variables

    Behavior:
    - The rendered configuration is always saved in the `output_data_dir`,
        preserving the relative structure, but with a ".txt" extension
    - If Config.`save_merged_yamls` is True, the merged YAML variables are saved
        as well:
        * If Config.`merged_yamls_path` is None, then YAML files are saved in a
            "yamls" subdirectory inside the `output_data_dir`, preserving
            relative paths
        * If Config.`merged_yamls_path` is a string, then YAML files are saved
            under that directory, preserving relative paths

    Args:
        relative_path (str): Relative path to the device YAML file (relative to
            the Config.`input_data_dir`)
        merged_vars (dict): Fully merged variables dictionary to save as YAML
        rendered_config (str): Rendered device configuration string to save as
            .txt file

    Returns:
        str: The full path to the saved rendered configuration (.txt) file
    """
    # Prepare path and save rendered configuration (.txt)
    txt_name = os.path.splitext(relative_path)[0] + ".txt"
    config_path = os.path.join(Config.output_data_dir, txt_name)
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Save the rendered configuration file
    with open(config_path, "w") as txt_file:
        txt_file.write(rendered_config)

    # Save merged YAML variables if enabled
    if Config.save_merged_yamls:
        # Determine YAML output path according to Config.`merged_yamls_path`
        yaml_name = os.path.splitext(relative_path)[0] + ".yaml"
        if Config.merged_yamls_path:
            merged_yaml_path = os.path.join(Config.merged_yamls_path, yaml_name)
        else:
            merged_yaml_path = os.path.join(Config.output_data_dir, "yamls", yaml_name)

        os.makedirs(os.path.dirname(merged_yaml_path), exist_ok=True)
        with open(merged_yaml_path, "w") as yaml_file:
            yaml.dump(merged_vars, yaml_file)

    return config_path


def merge_dicts_deep(base: dict, override: dict) -> dict:
    """
    Recursively merges two dictionaries with support for advanced override logic

    The `override` dictionary can:
    - Add or replace values at any depth
    - Remove entire keys using `key: false` or `key__remove: true`
    - Remove specific list items using `key__remove: [items]`
    - Append items to lists using `key__append: [items]`
    - Delete nested keys using `__delete_keys__` and dot notation

    This function returns a new merged dictionary without modifying the original

    Args:
        base (dict): The base dictionary to be merged into
        override (dict): The dictionary with overrides or modifications

    Returns:
        dict: A new dictionary representing the merged result
    """
    if not isinstance(base, dict) or not isinstance(override, dict):
        # Non-dict types are fully replaced
        return copy.deepcopy(override)

    result = copy.deepcopy(base)

    # Delete nested keys specified by '__delete_keys__'
    delete_keys = override.get("__delete_keys__", [])
    if delete_keys:
        delete_keys_with_dot_notation(result, delete_keys)

    # Handle keys with '__remove' and '__append' suffixes
    handle_remove_keys(result, override)
    handle_append_keys(result, override)

    # Remove keys with value False
    remove_false_values(result, override)

    # Merge other keys recursively or replace
    for key, val in override.items():
        if (
            key == "__delete_keys__"
            or key.endswith("__remove")
            or key.endswith("__append")
            or val is False
        ):
            # These have already been processed above
            continue

        base_val = result.get(key)

        if isinstance(base_val, dict) and isinstance(val, dict):
            # Recursive merge for nested dicts
            result[key] = merge_dicts_deep(base_val, val)
        elif isinstance(base_val, list) and isinstance(val, list):
            # Replace lists entirely
            result[key] = copy.deepcopy(val)
        else:
            # Override scalar or non-dict types
            result[key] = copy.deepcopy(val)

    return result


def delete_keys_with_dot_notation(target: dict, keys: list):
    """
    Delete nested keys in `target` dictionary using dot-separated key paths

    Args:
        target (dict): The dictionary to delete keys from
        keys (list): List of dotted key strings, e.g. ['bgp.neighbors.10.1.1.1']
    """
    for dotted_key in keys:
        parts = dotted_key.split(".")
        cur = target
        for i, part in enumerate(parts):
            if isinstance(cur, dict) and part in cur:
                if i == len(parts) - 1:
                    del cur[part]
                else:
                    cur = cur[part]
            else:
                break  # Key path does not exist; nothing to delete


def handle_remove_keys(target: dict, override: dict):
    """
    Process keys ending with '__remove' in the override dictionary

    - If override[key] is True, remove the whole base key
    - If override[key] is a list and base key is a list, remove listed items from base list

    Args:
        target (dict): The base dictionary to modify
        override (dict): The override dictionary containing removal instructions
    """
    for key in list(override.keys()):
        if not key.endswith("__remove"):
            continue

        base_key = key.removesuffix("__remove")
        val = override[key]

        if val is True:
            target.pop(base_key, None)
        elif isinstance(val, list) and isinstance(target.get(base_key), list):
            target[base_key] = [item for item in target[base_key] if item not in val]


def handle_append_keys(target: dict, override: dict):
    """
    Process keys ending with '__append' in the override dictionary

    - If base key is a list, append the new items
    - If base key is missing, create it as a new list
    - If base key exists but is not a list, show text and exit

    Args:
        target (dict): The base dictionary to modify
        override (dict): The override dictionary containing append instructions
    """
    for key in list(override.keys()):
        if not key.endswith("__append"):
            continue

        base_key = key.removesuffix("__append")
        val = override[key]

        if not isinstance(val, list):
            text = f"Error occured while parsing {key!r} with value {val!r}\n"
            text += f"Only lists can be appended, not {type(val).__name__}"
            log.critical(text)
            exit()

        if base_key not in target:
            target[base_key] = val.copy()
        elif isinstance(target[base_key], list):
            target[base_key].extend(val)
        else:
            text = f"Error occured while parsing {key!r} with value {val!r}\n"
            text += f"Can append to lists only, not {type(target[base_key]).__name__}"
            log.critical(text)
            exit()


def remove_false_values(target: dict, override: dict):
    """
    Remove keys from `target` where override[key] is exactly False

    Args:
        target (dict): The base dictionary to modify
        override (dict): The override dictionary
    """
    for key, val in override.items():
        if val is False:
            target.pop(key, None)


def get_device_type(yaml_path: str) -> str:
    """
    Extracts the top-level directory name from a relative YAML path,
    which represents the base device type (e.g., 'cisco_ios', 'juniper')

    Args:
        yaml_path (str): Relative path to the YAML file of the device (relative
            from the root of Config.`input_data_dir`)

    Returns:
        str: Top-level directory name representing the device type
    """
    device_type = yaml_path.replace("\\", "/").split("/")[0]
    return device_type


def load_vars_hierarchy(yaml_path: str) -> dict | None:
    """
    Loads and deeply merges all Config.`vars_filename` files found along the
    directory hierarchy leading to a specific device YAML file, including the
    device file itself at the end

    Supports advanced override features via `deep_merge_custom`

    Example hierarchy:
    - `input_data_dir`/vars.yaml (global)
    - `input_data_dir`/cisco_ios/vars.yaml (vendor-specific)
    - `input_data_dir`/cisco_ios/router/vars.yaml (role-specific)
    - `input_data_dir`/cisco_ios/router/new_york.yaml (device-specific)

    Args:
        yaml_path (str): Relative path (starting from Config.`input_data_dir`)
            to the device YAML

    Returns:
        dict: Fully merged variable dictionary
    """
    # Build a list of all YAML files to merge
    yaml_files = []
    path_parts = os.path.dirname(yaml_path).replace("\\", "/").split("/")
    for i in range(len(path_parts) + 1):
        # Build path to Config.`vars_filename` at this level
        partial_path = os.path.join(*path_parts[:i], Config.vars_filename)
        full_path = os.path.join(Config.input_data_dir, partial_path)
        yaml_files.append(full_path)

    # Add the device YAML file itself at the end
    device_yaml_full_path = os.path.join(Config.input_data_dir, yaml_path)
    yaml_files.append(device_yaml_full_path)

    # Merge all YAML files in order
    log.debug(device_yaml_full_path, b=1)
    merged_data = {}
    for path in yaml_files:
        if not os.path.exists(path):
            continue
        with open(path, "r") as file:
            try:
                data = yaml.safe_load(file) or {}
            except yaml.scanner.ScannerError as error:
                log.error(f"YAML ScannerError: {error}")
                return
            log.debug(path, b=2, a=3)
            log.debug("old data", yaml.dump(merged_data), a=3)
            log.debug("new data", yaml.dump(data), a=3)
            merged_data = merge_dicts_deep(merged_data, data)
            log.debug("merged data", yaml.dump(merged_data), path)
    log.info(a=3)
    log.info(f"Processed: {device_yaml_full_path}")

    return merged_data


if __name__ == "__main__":
    main()
