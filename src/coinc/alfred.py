"""Utilities functions for Alfred"""
import json
import os
from pathlib import Path
from typing import Union

PERSISTED_DATA_DIR = os.getenv("alfred_workflow_data")
if not PERSISTED_DATA_DIR:
    raise RuntimeError("Alfred data directory not found")
PERSISTED_DATA_FILE = Path(PERSISTED_DATA_DIR) / "settings.json"


def persisted_data(key: str, content: Union[dict, None] = None) -> dict:
    """Read or write data to a file in the workflow's data directory"""

    # Read content
    if not PERSISTED_DATA_FILE.exists():
        settings = dict()
    else:
        with open(PERSISTED_DATA_FILE, "r") as file:
            settings = json.load(file)

    # Write content
    if content is not None:
        settings[key] = content
        with open(PERSISTED_DATA_FILE, "w") as file:
            json.dump(settings, file, ensure_ascii=False)

    return settings.get(key, dict())
