import os

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

    with open(yaml_path, "r") as file:
        device_data = yaml.safe_load(file) or {}

    # Compute path relative to the root of the device YAMLs directory
    relative_path = os.path.relpath(yaml_path, Config.device_yamls_dir)

    # Merge inherited and device-specific variables
    merged_vars = build_merged_vars(relative_path, device_data)

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


def build_merged_vars(relative_path, device_data):
    """
    Combines all inherited vars from the vars.yaml hierarchy with
    device-specific data

    Args:
        relative_path (str): Path to the device YAML file relative to
            device_yamls root
        device_data (dict): The YAML data specific to the device

    Returns:
        dict: Final merged variables with deeper/explicit values overriding
            general ones
    """
    merged_vars = load_vars_hierarchy(relative_path)
    merged_vars.update(device_data)
    device_type = get_device_type(relative_path)
    merged_vars["device_type"] = device_type
    return merged_vars


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
    Loads and merges all `vars.yaml` files found along the directory hierarchy
    leading to a specific device YAML file. Each deeper level overrides keys
    from higher (more general) levels

    For example:
    - device_yamls/vars.yaml (global)
    - device_yamls/cisco_ios/vars.yaml (vendor-specific)
    - device_yamls/cisco_ios/router/vars.yaml (role-specific)

    Args:
        yaml_path (str): Relative path (from device_yamls) to the device YAML
            file

    Returns:
        dict: Merged dictionary of variables with deeper levels overriding
            higher ones
    """
    merged_data = {}

    # Normalize path and split into a list of directories
    path_parts = os.path.dirname(yaml_path).replace("\\", "/").split("/")

    # Walk from root to deepest subdirectory, merging vars.yaml at each level
    for i in range(len(path_parts) + 1):
        # Build path to vars.yaml at this level
        partial_path = os.path.join(*path_parts[:i], Config.vars_filename)
        full_path = os.path.join(Config.device_yamls_dir, partial_path)

        if os.path.exists(full_path):
            # Load and merge if exists (deeper levels override higher ones)
            with open(full_path, "r") as f:
                data = yaml.safe_load(f) or {}
                merged_data.update(data)
    return merged_data


if __name__ == "__main__":
    main()
