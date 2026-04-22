"""Load continuous baseline task templates from YAML.

Called by people_tasks_service.instantiate_baseline() — not at startup.
Templates are loaded into memory, not the DB. The service uses them to
create PeopleTask rows per-org.
"""

import os

import yaml

_YAML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "continuous_baseline_tasks.yaml",
)

_cache: list[dict] | None = None


def get_baseline_templates() -> list[dict]:
    global _cache
    if _cache is None:
        with open(_YAML_PATH) as f:
            _cache = yaml.safe_load(f)
    return _cache
