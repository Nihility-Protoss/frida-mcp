import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict, field

@dataclass
class FridaConfig:
    os: Optional[str] = None
    server_path: Optional[str] = None
    server_name: Optional[str] = None
    server_port: int = 27042
    device_id: Optional[str] = None
    adb_path: str = "adb"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FridaConfig":
        return cls(**{
            k: v for k, v in data.items() 
            if k in cls.__dataclass_fields__
        })

    def save(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

GLOBAL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
PROJECT_CONFIG_PATH = os.path.join(os.getcwd(), "frida.mcp.config.json")

def load_config() -> FridaConfig:
    config = FridaConfig()
    
    # Try project config first (CWD), then global config (package dir)
    candidates = [
        PROJECT_CONFIG_PATH,
        GLOBAL_CONFIG_PATH,
    ]
    
    for cfg in candidates:
        try:
            if os.path.isfile(cfg):
                with open(cfg, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    return FridaConfig.from_dict(loaded)
                break
        except Exception:
            # Silently fall back to defaults
            continue
            
    return config
