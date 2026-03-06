from typing import Optional, Dict, Any
from .default_config import FridaConfig


def guard_os(expected: str, config: FridaConfig, action: str) -> Optional[Dict[str, Any]]:
    current = getattr(config, "os", None)
    if current and current != expected:
        return {
            "status": "error",
            "message": f"os={current}. 请先调用 config_set(os='{expected}') 然后重试 {action}"
        }
    return None
