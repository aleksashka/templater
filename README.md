# YAML/Jinja Text Generator

This is a flexible Jinja2-based text generator (was initially created for network devices) which uses multilevel YAML files hierarchy

## Features

- **Layered YAML hierarchy** with support for inheritance:
  - `vars.yaml` (configurable) files in parent directories define default values
  - deeper directories replace, update and extend values
- **Advanced merge logic**:
  - Remove keys via `key: false` or `key__remove: true`
  - Remove list items: `key__remove: [item1, item2]`
  - Add list items: `key__append: [item3, item4]`
  - Delete nested keys via `__delete_keys__` (using dot notation)
- **Jinja2 templating** based on the target type (e.g., `cisco_ios/base.j2`)
- **Creates**:
  - rendered `.txt` (configurable) text files
  - final merged `.yaml` variable files (optional)
- Optionally exclude dirs and files from processing via `skip_prefix` (configurable)
- Optionally set configurable variable from target YAML filename (`Config.filename_variable`)

## Directory Structure Example

```text
_input_data/
├── vars.yaml  # global defaults
├── cisco_ios/
│   ├── vars.yaml  # Cisco-specific overrides
│   ├── router/
│   │   ├── vars.yaml  # role-specific overrides
│   │   └── my-target.yaml  # target-specific YAML
```

## Output Example

In case of:
- `save_merged_yamls = True`
- `merged_yamls_path = None` (default)

```text
_output_data/
├── cisco_ios/
│   └── router/
│       └── my-target.txt
├── yamls/
│   └── cisco_ios/
│       └── router/
│           └── my-target.yaml
```

In case of:
- `save_merged_yamls = True`
- `merged_yamls_path = "merged_yamls"`

```text
_output_data/
├── cisco_ios/
│   └── router/
│       └── my-target.txt
merged_yamls/
├── cisco_ios/
│   └── router/
│       └── my-target.yaml
```

## Usage

To create `some_text.txt` based on `some_name` template (e.g. `cisco`, `juniper`, whatever):
1. Copy `config_sample.py` to `config.py` to create default configuration (or use provided `init_project.py` to automatically create `config.py` and after timeout create necessary directories)
1. Working directories (with input/output files) can be placed in some `Config.base_dirname` (by default "." - next to `main.py`)
1. Define your optional `vars.yaml` (will be merged) files under `_input_data/` (any number of levels deep)
1. Define your `some_text.yaml` file somewhere under `_input_data/some_name/`
1. Create your Jinja2 template `_input_templates/some_name/base.j2` (other templates may be added)
1. Run the main script: `python main.py`

## Configuration

Edit the `Config` class in `config.py`
