import os
import copy

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import Config


env = Environment(
    loader=FileSystemLoader(Config.templates_dir),
    autoescape=select_autoescape(disabled_extensions=("j2", "txt", "yaml")),
)


def main():
    for yaml_path in find_yaml_files(Config.device_yamls_dir):
        generate_config(yaml_path)


def find_yaml_files(root_dir):
    """
    Recursively walks through the directory tree starting from `root_dir`,
    yielding paths to all `.yaml` files except those named as configured in
    `Config.vars_filename` (`vars.yaml` by default)

    Args:
        root_dir (str): Root directory to search for YAML files

    Yields:
        str: Full path to each YAML file (excluding `Config.vars_filename`)
    """
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".yaml"):
                if file != Config.vars_filename:
                    yield os.path.join(dirpath, file)


def generate_config(yaml_path):
    """
    Generates a configuration file for a network device based on a YAML
    definition

    This function:
    - Loads the device-specific YAML data
    - Merges it with inherited variables from all applicable `vars.yaml` files
    - Selects the appropriate base Jinja2 template based on device type
    - Renders the configuration
    - Writes the output to a `.txt` file in the corresponding structure

    Args:
        yaml_path (str): Full path to the device YAML file
    """

    # Compute path relative to the root of the device YAMLs directory
    relative_path = os.path.relpath(yaml_path, Config.device_yamls_dir)

    # Merge inherited and device-specific variables
    merged_vars = load_vars_hierarchy(relative_path)

    # Add device_type key
    merged_vars["device_type"] = get_device_type(relative_path)

    # Select template based on top-level device type (e.g. "cisco_ios")
    template_path = f"{merged_vars['device_type']}/base.j2"
    try:
        template = env.get_template(template_path)
    except Exception as e:
        print(f"Error while loading template '{template_path}': {e}")
        return

    # Render the final configuration using merged variables
    rendered_config = template.render(merged_vars)

    # Create the output path: same relative structure, but with .txt extension
    txt_name = os.path.splitext(relative_path)[0] + ".txt"
    output_path = os.path.join(Config.output_dir, txt_name)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the rendered configuration
    with open(output_path, "w") as file:
        file.write(rendered_config)

    print(f"Created: {output_path}")


def deep_merge_custom(base: dict, override: dict) -> dict:
    """
    Entry point function to deeply merge two dictionaries with advanced control:

    Supports:
    - Recursive merging of nested dicts
    - Full key removal via 'key: False' or 'key__remove: True'
    - Partial removal from lists via 'key__remove: [items]'
    - Nested key removal via '__delete_keys__' with dot notation

    Args:
        base (dict): Base dictionary
        override (dict): Override dictionary

    Returns:
        dict: Merged dictionary
    """
    return recursive_merge_dicts(base, override)


def recursive_merge_dicts(base: dict, override: dict) -> dict:
    """
    Recursively merge `override` dictionary into `base` dictionary with support
    for:

    - Removing keys via 'key: False' or 'key__remove: True'
    - Removing specific list items via 'key__remove: [items]'
    - Deleting nested keys via '__delete_keys__' list of dot-separated keys

    Args:
        base (dict): The base dictionary
        override (dict): The overriding dictionary

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

    # Handle keys with '__remove' suffix
    handle_remove_keys(result, override)

    # Remove keys with value False
    remove_false_values(result, override)

    # Merge other keys recursively or replace
    for key, val in override.items():
        if key == "__delete_keys__" or key.endswith("__remove") or val is False:
            # These have already been processed above
            continue

        base_val = result.get(key)

        if isinstance(base_val, dict) and isinstance(val, dict):
            # Recursive merge for nested dicts
            result[key] = recursive_merge_dicts(base_val, val)
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


def get_device_type(yaml_path):
    """
    Extracts the top-level directory name from a relative YAML path,
    which represents the base device type (e.g., 'cisco_ios', 'juniper')

    Args:
        yaml_path (str): Relative path to the device YAML file (from the root of
            device_yamls)

    Returns:
        str: Top-level directory name representing the device type
    """
    device_type = yaml_path.replace("\\", "/").split("/")[0]
    return device_type


def load_vars_hierarchy(yaml_path):
    """
    Loads and deeply merges all `vars.yaml` files found along the directory
    hierarchy leading to a specific device YAML file, including the device file
    itself at the end

    Supports advanced override features via `deep_merge_custom`

    Example hierarchy:
    - device_yamls/vars.yaml (global)
    - device_yamls/cisco_ios/vars.yaml (vendor-specific)
    - device_yamls/cisco_ios/router/vars.yaml (role-specific)
    - device_yamls/cisco_ios/router/new_york.yaml (device-specific)

    Args:
        yaml_path (str): Relative path (from device_yamls) to the device YAML

    Returns:
        dict: Fully merged variable dictionary
    """
    # Build list of all YAML files to merge
    yaml_files = []
    path_parts = os.path.dirname(yaml_path).replace("\\", "/").split("/")
    for i in range(len(path_parts) + 1):
        # Build path to vars.yaml at this level
        partial_path = os.path.join(*path_parts[:i], Config.vars_filename)
        full_path = os.path.join(Config.device_yamls_dir, partial_path)
        yaml_files.append(full_path)

    # Add the device YAML file itself at the end
    device_yaml_full_path = os.path.join(Config.device_yamls_dir, yaml_path)
    yaml_files.append(device_yaml_full_path)

    # Merge all YAML files in order
    merged_data = {}
    for path in yaml_files:
        if not os.path.exists(path):
            continue
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
            merged_data = deep_merge_custom(merged_data, data)

    return merged_data


if __name__ == "__main__":
    main()
