# YAML/Jinja Text Generator

This is a flexible Jinja2-based text generator (originally designed for network device configurations) that uses a multilevel hierarchy of YAML files

## Features

- **Layered YAML variable hierarchy** with support for inheritance:
  - Global `my_config.yaml` (in the root directory, next to `main.py`) defines global settings
  - Optional per-project `my_config.yaml` (inside the directory defined by `base_dirname` in global settings) overrides global settings such as working directories, output extension, logging, etc
  - `vars.yaml` (name is configurable) files in working directories define default values
  - Same files in deeper directories flexibly update, extend, or override previous values
  - Final (target) YAML files contain the most specific, fully resolved values

- **Advanced merge logic (applies to both `vars.yaml` and target YAML files)**:
  - Remove keys using `key: false` or `key__remove: true`
  - Remove list items: `key__remove: [item1, item2]`
  - Add list items: `key__append: [item3, item4]`
  - Delete nested keys using `__delete_keys__` (with dot notation)

- **Jinja2 templating** based on the target type inside the project's input directory (e.g., `cisco_ios`, `juniper`, etc)

- **Creates**:
  - Rendered text files (`.txt` by default, configurable)
  - Final merged `.yaml` files that contain the resolved variables (optional, useful for validation and debugging)

- **Options**:
  - Exclude directories or files from processing using `skip_prefix` (configurable)
  - Set a custom variable (if not already defined) based on the filename of the target YAML file (configured by `filename_variable`)

## Full Directory Structure for `demo` project

Assuming the default `base_dirname` (`my_projects/demo`)
```text
├── main.py  # entry point
├── my_config.yaml  # global configuration settings, e.g. {log_level: 20}
└── my_projects
    ├── demo  # current project, selected by `base_dirname` from global configuration
    │   ├── my_config.yaml  # project's config {filename_variable: name, save_merged_yamls: true}
    │   ├── input_data
    │   │   └── animals  # saved as `target_type` variable for later template selection
    │   │       ├── vars.yaml  # {kingdom: Animalia, abilities: [breathes]} - for all animals
    │   │       ├── aves
    │   │       │   ├── vars.yaml  # {class: Aves, abilities__append: [flies]} - for all birds
    │   │       │   └── Bald eagle.yaml
    │   │       └── mammals
    │   │           ├── vars.yaml  # {class: Mammalia} - for all mammals
    │   │           ├── Dolphin.yaml  # {species: Delphinus delphis, abilities__remove: [walks]}
    │   │           └── Lion.yaml  # {species: Panthera leo, abilities__append: [roars]}
    │   ├── input_templates
    │   │   └── animals  # this name should match `target_type` above
    │   │       └── base.j2  # render using `kingdom`, `class`, `species`, `abilities` variables
    │   └── output_data  # can be safely deleted (recreate by running `main.py`)
    │       ├── animals
    │       │   ├── aves
    │       │   │   └── Bald eagle.txt
    │       │   └── mammals
    │       │       ├── Dolphin.txt
    │       │       └── Lion.txt
    │       └── yamls  # created since `save_merged_yamls` is `true`
    │           └── animals
    │               ├── aves
    │               │   └── Bald eagle.yaml
    │               └── mammals
    │                   ├── Dolphin.yaml
    │                   └── Lion.yaml  # see below
    └── work  # create many other projects (update global `base_dirname` to render it)
        ├── my_config.yaml  # similar per-project structure
        ├── input_data
        ├── input_templates
        └── output_data
```

Below is the resulting `Dolphin.yaml` (`output_data/yamls/animals/mammals/Dolphin.yaml`):
```text
abilities:
- breathes                  # taken from #1 vars.yaml (demo/input_data/animals/vars.yaml)
- produces milk             # taken from #2 vars.yaml (demo/input_data/animals/mammals/vars.yaml)
- swims                     # taken from the target (Dolphin.yaml)
                            # walks - removed by the target (Dolphin.yaml)
class: Mammalia             # taken from #2 vars.yaml (demo/input_data/animals/mammals/vars.yaml)
kingdom: Animalia           # taken from #1 vars.yaml (demo/input_data/animals/vars.yaml)
name: Dolphin               # variable name taken from the project's config (my_config.yaml)
                            # value taken from target filename (Dolphin.yaml)
species: Delphinus delphis  # taken from the target (Dolphin.yaml)
target_type: animals        # taken from dirname animals (demo/input_data/animals)
```

## Input/Output Directories/Files Examples

Suppose this is the input structure (inside any project or even globally):
```text
├── input_data
│   ├── vars.yaml  # global defaults
│   └── cisco_ios
│       ├── vars.yaml  # Cisco-specific overrides
│       └── router
│           ├── vars.yaml  # role-specific overrides
│           └── my-target.yaml  # target-specific variables
```

Below is the output in case of the following `my_config.yaml`:
```yaml
save_merged_yamls: true
merged_yamls_path: null
```

```text
└── output_data
    ├── cisco_ios
    │   └── router
    │       └── my-target.txt
    └── yamls
        └── cisco_ios
            └── router
                └── my-target.yaml
```

This is the output in case of the following `my_config.yaml`:
```yaml
save_merged_yamls: true
merged_yamls_path: merged_yamls
```

```text
├── output_data
│   └── cisco_ios
│       └── router
│           └── my-target.txt
└── merged_yamls
    └── cisco_ios
        └── router
            └── my-target.yaml
```

## Installation copy/paste scripts

<details>
<summary>for Windows using <code>py</code></summary>

```text
git clone https://github.com/aleksashka/templater.git
cd templater
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
</details>

<details>
<summary>for Windows using <code>python</code></summary>

```text
git clone https://github.com/aleksashka/templater.git
cd templater
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
</details>

<details>
<summary>for *nix using <code>python</code></summary>

```text
git clone https://github.com/aleksashka/templater.git
cd templater
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
</details>

<details>
<summary>for *nix using <code>python3</code></summary>

```text
git clone https://github.com/aleksashka/templater.git
cd templater
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
</details>

## Usage

To create `some_text.txt` based on `some_name` template (e.g. `cisco`, `juniper`, whatever):
1. Copy `my_config_sample.yaml` to `my_config.yaml` to change the default configuration (or use the provided `init_project.py` script to do it automatically and, after a short timeout, create all necessary directories)
1. Working directories (with input/output files) can be placed in a project directory defined by `base_dirname`, which defaults to "my_projects/demo" (relative to `main.py`)
1. Define your optional `vars.yaml` (will be merged) files under `input_data/` (any number of levels deep)
1. Define your `some_text.yaml` file somewhere under `input_data/some_name/` (`some_name` part becomes the `target_type` variable and is used for template selection)
1. Create your Jinja2 template `input_templates/some_name/base.j2` (child templates may be added to be included in the base one)
1. Run the main script: `python main.py`
