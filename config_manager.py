#!/usr/bin/env python3
"""
📋 Configuration Manager
מנהל תצורה מרכזי לכל הפרויקט
"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Centralized configuration management
    Loads from config.yaml and allows environment variable overrides
    """
    
    _instance = None
    _config = None
    
    def __new__(cls, config_path: Optional[str] = None):
        """Singleton pattern - only one config instance"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager"""
        if self._config is not None:
            return  # Already initialized
        
        if config_path is None:
            # Default path
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"✅ Configuration loaded from {self.config_path}")
            return config
        
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            return self._get_default_config()
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # Environment variables override format: CC_SECTION_KEY
        # Example: CC_IBKR_PORT=7496
        
        env_prefix = "CC_"
        
        for key, value in os.environ.items():
            if not key.startswith(env_prefix):
                continue
            
            # Parse key: CC_IBKR_PORT -> ['ibkr', 'port']
            parts = key[len(env_prefix):].lower().split('_')
            
            if len(parts) < 2:
                continue
            
            # Navigate config structure
            config_section = self._config
            for part in parts[:-1]:
                if part not in config_section:
                    config_section[part] = {}
                config_section = config_section[part]
            
            # Set value with type conversion
            final_key = parts[-1]
            config_section[final_key] = self._convert_type(value)
            
            logger.info(f"✅ Config override from env: {key}")
    
    def _convert_type(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Try boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Try int
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key
        
        Examples:
            config.get('ibkr.port')  # Returns 7497
            config.get('strategy.dte_min')  # Returns 21
            config.get('missing.key', 0)  # Returns 0
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by dot-notation key
        Note: This only affects runtime config, not the file
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.info(f"✅ Config updated: {key} = {value}")
    
    def get_section(self, section: str) -> Dict:
        """Get entire configuration section"""
        return deepcopy(self.get(section, {}))
    
    def reload(self):
        """Reload configuration from file"""
        self._config = self._load_config()
        self._apply_env_overrides()
        logger.info("✅ Configuration reloaded")
    
    def save(self, path: Optional[str] = None):
        """Save current configuration to file"""
        save_path = Path(path) if path else self.config_path
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"✅ Configuration saved to {save_path}")
        
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
    
    def _get_default_config(self) -> Dict:
        """Return default configuration if file not found"""
        return {
            'ibkr': {
                'host': '127.0.0.1',
                'port': 7497,
                'client_id': 1,
                'timeout': 30
            },
            'strategy': {
                'dte_min': 21,
                'dte_max': 45,
                'delta_target': 0.30,
                'min_premium_dollars': 50
            },
            'risk': {
                'max_trades_per_day': 5,
                'max_position_size_pct': 10.0
            },
            'logging': {
                'level': 'INFO',
                'file': 'trading.log'
            },
            'modes': {
                'default_mode': 'paper'
            }
        }
    
    def validate(self) -> bool:
        """Validate configuration has required fields"""
        required_sections = ['ibkr', 'strategy', 'risk', 'logging']
        
        for section in required_sections:
            if section not in self._config:
                logger.error(f"❌ Missing required config section: {section}")
                return False
        
        # Validate IBKR settings
        ibkr = self._config.get('ibkr', {})
        if not all(k in ibkr for k in ['host', 'port', 'client_id']):
            logger.error("❌ Incomplete IBKR configuration")
            return False
        
        logger.info("✅ Configuration validation passed")
        return True
    
    def to_dict(self) -> Dict:
        """Return configuration as dictionary"""
        return deepcopy(self._config)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ConfigManager(config_path={self.config_path})"


# ==================== Helper Functions ====================

def get_config() -> ConfigManager:
    """Get global configuration instance"""
    return ConfigManager()


def reload_config():
    """Reload global configuration"""
    config = get_config()
    config.reload()


# ==================== Quick Access Functions ====================

def get_ibkr_config() -> Dict:
    """Get IBKR configuration"""
    return get_config().get_section('ibkr')


def get_strategy_config() -> Dict:
    """Get strategy configuration"""
    return get_config().get_section('strategy')


def get_risk_config() -> Dict:
    """Get risk management configuration"""
    return get_config().get_section('risk')


def is_live_mode() -> bool:
    """Check if running in live trading mode"""
    return get_config().get('modes.default_mode') == 'live'


def is_paper_mode() -> bool:
    """Check if running in paper trading mode"""
    return get_config().get('modes.default_mode') == 'paper'


def is_demo_mode() -> bool:
    """Check if running in demo mode"""
    return get_config().get('modes.default_mode') == 'demo'


# ==================== Testing ====================

if __name__ == "__main__":
    # Test configuration manager
    print("🧪 Testing Configuration Manager\n")
    
    # Create config manager
    config = ConfigManager()
    
    # Test get
    print(f"IBKR Port: {config.get('ibkr.port')}")
    print(f"DTE Min: {config.get('strategy.dte_min')}")
    print(f"Max Trades: {config.get('risk.max_trades_per_day')}")
    print(f"Default: {config.get('missing.key', 'DEFAULT')}")
    
    # Test set
    config.set('strategy.dte_min', 25)
    print(f"\nAfter set - DTE Min: {config.get('strategy.dte_min')}")
    
    # Test section
    ibkr_config = config.get_section('ibkr')
    print(f"\nIBKR Config: {ibkr_config}")
    
    # Test validation
    print(f"\nValidation: {'✅' if config.validate() else '❌'}")
    
    # Test quick access
    print(f"\nIs Live Mode: {is_live_mode()}")
    print(f"Is Paper Mode: {is_paper_mode()}")
    
    print("\n✅ All tests passed!")
