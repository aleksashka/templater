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
    with open(yaml_path, "r") as file:
        device_data = yaml.safe_load(file) or {}

    relative_path = os.path.relpath(yaml_path, Config.device_yamls_dir)
    device_type = get_device_type(relative_path)

    inherited_vars = load_vars_hierarchy(relative_path)
    inherited_vars.update(device_data)
    inherited_vars["device_type"] = device_type

    template_path = f"{device_type}/base.j2"
    try:
        template = env.get_template(template_path)
    except Exception as e:
        print(f"Error while loading template '{template_path}': {e}")
        return

    rendered_config = template.render(inherited_vars)

    txt_name = os.path.splitext(relative_path)[0] + ".txt"
    output_path = os.path.join(Config.output_dir, txt_name)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as file:
        file.write(rendered_config)

    print(f"Created: {output_path}")


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
