from typing import Optional, Dict, Any
from models.sysSetting import SysSetting

class GlobalConfig:
    _instance = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalConfig, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_config(cls) -> Optional[Dict[str, Any]]:
        """获取缓存的配置"""
        return cls._config

    @classmethod
    def update_config(cls, config: SysSetting) -> None:
        """更新缓存的配置"""
        if not config:
            return
        
        cls._config = {
            "id": config.id,
            "emby_url": config.emby_url,
            "emby_api_key": config.emby_api_key,
            "alist_url": config.alist_url,
            "alist_api_key": config.alist_api_key,
            "tianyiAccount": config.tianyiAccount,
            "tianyiPassword": config.tianyiPassword,
            "quarkCookie": config.quarkCookie,
            "created_at": config.created_at,
            "updated_at": config.updated_at
        }

    @classmethod
    def clear_config(cls) -> None:
        """清除缓存的配置"""
        cls._config = None

# 创建全局实例
global_config = GlobalConfig() 