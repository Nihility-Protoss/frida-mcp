import os
import json
from typing import Optional, Dict, Any, Deque

# Minimal configuration loading from config.json (optional)
def load_config() -> Dict[str, Any]:
    default_config: Dict[str, Any] = {
        "server_path": None,
        "server_name": None,
        "server_port": 27042,
        "device_id": None,
        "adb_path": "adb",
    }
    # Try relative to this file first, then CWD
    candidates = [
        os.path.join(os.path.dirname(__file__), "config.json"),
        os.path.join(os.getcwd(), "config.json"),
    ]
    for cfg in candidates:
        try:
            if os.path.isfile(cfg):
                with open(cfg, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    default_config.update(loaded)
                break
        except Exception:
            # Silently fall back to defaults for minimal intrusion
            break
    return default_config