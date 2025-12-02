#!/usr/bin/env python3
"""Configuration management for flightdata."""

import os
from pathlib import Path
from typing import Optional
import json


class Config:
    """Configuration manager for ADS-B Exchange client."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to config file. If None, uses default locations.
        """
        self.config_file = config_file or self._find_config_file()
        self.config = self._load_config()
    
    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file in standard locations."""
        # Check environment variable
        if env_path := os.getenv('FLIGHTDATA_CONFIG'):
            return Path(env_path)
        
        # Check current directory
        local_config = Path('.flightdata.json')
        if local_config.exists():
            return local_config
        
        # Check home directory
        home_config = Path.home() / '.flightdata.json'
        if home_config.exists():
            return home_config
        
        return None
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        if self.config_file and self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        # Check environment variable first
        env_key = f'ADSB_EXCHANGE_{key.upper()}'
        if env_value := os.getenv(env_key):
            return env_value
        
        # Fall back to config file
        return self.config.get(key, default)
    
    @property
    def api_key(self) -> Optional[str]:
        """Get ADS-B Exchange API key."""
        return self.get('api_key')
    
    @property
    def use_rapid_api(self) -> bool:
        """Get whether to use RapidAPI endpoint."""
        value = self.get('use_rapid_api', False)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)
    
    def save_template(self, path: Optional[Path] = None):
        """Save a configuration template file."""
        path = path or Path('.flightdata.json')
        
        template = {
            "api_key": "your-rapidapi-key-here",
            "use_rapid_api": False,
            "default_radius_km": 100,
            "default_center_lat": 37.7749,
            "default_center_lon": -122.4194,
        }
        
        with open(path, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"Configuration template saved to {path}")


def create_config_file():
    """CLI tool to create configuration file."""
    import sys
    
    config = Config()
    
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path('.flightdata.json')
    
    config.save_template(path)


if __name__ == '__main__':
    create_config_file()
