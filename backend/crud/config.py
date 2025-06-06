from pathlib import Path
import os
import yaml
from typing import Dict, Any

class Settings:
    def __init__(self):
        self.env = os.getenv("ENV", "dev")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        config_path = Path(__file__).parent.parent / "config" / f"config.{self.env}.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    @property
    def app_config(self) -> Dict[str, Any]:
        return self.config["app"]

    @property
    def server_config(self) -> Dict[str, Any]:
        return self.config["server"]

    @property
    def database_config(self) -> Dict[str, Any]:
        return self.config["database"]

    @property
    def logging_config(self) -> Dict[str, Any]:
        return self.config["logging"]

    @property
    def security_config(self) -> Dict[str, Any]:
        return self.config["security"]

# 创建全局配置实例
settings = Settings() 