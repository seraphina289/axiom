"""
Configuration management for Axiom editor
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import os

from .error_handler import AxiomError, ConfigError


class Config:
    """Configuration management with file persistence and validation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Default configuration values
        self.defaults = {
            # Editor behavior
            'tab_width': 4,
            'use_spaces_for_tabs': True,
            'auto_indent': True,
            'wrap_lines': False,
            'show_line_numbers': True,
            'highlight_current_line': True,
            
            # File handling
            'max_file_size': 50 * 1024 * 1024,  # 50MB
            'default_encoding': 'utf-8',
            'backup_files': True,
            'auto_save_interval': 300,  # 5 minutes
            
            # Display
            'color_scheme': 'default',
            'font_size': 12,
            'show_whitespace': False,
            'show_eol': False,
            
            # Search and replace
            'case_sensitive_search': False,
            'regex_search': False,
            'highlight_search_results': True,
            
            # Performance
            'syntax_highlighting': True,
            'lazy_loading': True,
            'max_undo_levels': 1000,
            
            # Interface
            'show_status_bar': True,
            'show_ruler': False,
            'scroll_margin': 3,
            'smooth_scrolling': True,
            
            # Advanced
            'plugin_directory': None,
            'custom_commands': {},
            'key_bindings': {},
        }
        
        # Current configuration
        self.config = self.defaults.copy()
        
        # Configuration file paths
        self.config_dir = Path.home() / '.axiom'
        self.config_file = self.config_dir / 'config.json'
        self.backup_file = self.config_dir / 'config.backup.json'
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Load from file if it exists
            if self.config_file.exists():
                self._load_from_file()
            else:
                self.logger.info("No config file found, using defaults")
                self._save_config()  # Create initial config file
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Use defaults on load failure
            self.config = self.defaults.copy()
    
    def _load_from_file(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Validate and merge with defaults
            self.config = self.defaults.copy()
            self._merge_config(loaded_config)
            
            self.logger.info(f"Configuration loaded from {self.config_file}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            self._restore_from_backup()
        except Exception as e:
            self.logger.error(f"Error reading config file: {e}")
            self._restore_from_backup()
    
    def _merge_config(self, loaded_config: Dict[str, Any]):
        """Merge loaded configuration with defaults, validating values"""
        for key, value in loaded_config.items():
            if key in self.defaults:
                # Validate value type
                default_type = type(self.defaults[key])
                if isinstance(value, default_type) or value is None:
                    self.config[key] = value
                else:
                    self.logger.warning(f"Invalid type for config key '{key}': expected {default_type.__name__}, got {type(value).__name__}")
            else:
                self.logger.warning(f"Unknown config key ignored: '{key}'")
    
    def _restore_from_backup(self):
        """Restore configuration from backup file"""
        try:
            if self.backup_file.exists():
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    backup_config = json.load(f)
                
                self.config = self.defaults.copy()
                self._merge_config(backup_config)
                
                self.logger.info("Configuration restored from backup")
            else:
                self.logger.warning("No backup file found, using defaults")
                
        except Exception as e:
            self.logger.error(f"Failed to restore from backup: {e}")
            # Fall back to defaults
            self.config = self.defaults.copy()
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            # Create backup before saving
            if self.config_file.exists():
                self.config_file.replace(self.backup_file)
            
            # Save configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, sort_keys=True)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise ConfigError(f"Cannot save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """Set configuration value with validation"""
        try:
            # Validate key exists in defaults
            if key not in self.defaults:
                raise ConfigError(f"Unknown configuration key: '{key}'")
            
            # Validate value type (allow None for optional values)
            default_type = type(self.defaults[key])
            if value is not None and not isinstance(value, default_type):
                raise ConfigError(f"Invalid type for '{key}': expected {default_type.__name__}, got {type(value).__name__}")
            
            # Validate specific values
            self._validate_specific_value(key, value)
            
            # Set value
            old_value = self.config.get(key)
            self.config[key] = value
            
            # Save if requested
            if save:
                self._save_config()
            
            self.logger.info(f"Configuration updated: {key} = {value} (was {old_value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set config value: {e}")
            raise ConfigError(f"Cannot set configuration value: {e}")
    
    def _validate_specific_value(self, key: str, value: Any):
        """Validate specific configuration values"""
        if key == 'tab_width' and value is not None:
            if not (1 <= value <= 16):
                raise ConfigError("Tab width must be between 1 and 16")
        
        elif key == 'max_file_size' and value is not None:
            if value < 1024:  # Minimum 1KB
                raise ConfigError("Max file size must be at least 1KB")
        
        elif key == 'auto_save_interval' and value is not None:
            if value < 30:  # Minimum 30 seconds
                raise ConfigError("Auto save interval must be at least 30 seconds")
        
        elif key == 'max_undo_levels' and value is not None:
            if not (1 <= value <= 10000):
                raise ConfigError("Max undo levels must be between 1 and 10000")
        
        elif key == 'font_size' and value is not None:
            if not (8 <= value <= 72):
                raise ConfigError("Font size must be between 8 and 72")
        
        elif key == 'scroll_margin' and value is not None:
            if not (0 <= value <= 20):
                raise ConfigError("Scroll margin must be between 0 and 20")
        
        elif key == 'color_scheme' and value is not None:
            valid_schemes = ['default', 'dark', 'light', 'high_contrast']
            if value not in valid_schemes:
                raise ConfigError(f"Invalid color scheme. Valid options: {', '.join(valid_schemes)}")
    
    def reset_to_defaults(self, save: bool = True):
        """Reset configuration to default values"""
        try:
            self.config = self.defaults.copy()
            
            if save:
                self._save_config()
            
            self.logger.info("Configuration reset to defaults")
            
        except Exception as e:
            raise ConfigError(f"Cannot reset configuration: {e}")
    
    def update_multiple(self, updates: Dict[str, Any], save: bool = True):
        """Update multiple configuration values at once"""
        errors = []
        
        # Validate all values first
        for key, value in updates.items():
            try:
                if key not in self.defaults:
                    errors.append(f"Unknown key: '{key}'")
                    continue
                
                default_type = type(self.defaults[key])
                if value is not None and not isinstance(value, default_type):
                    errors.append(f"Invalid type for '{key}': expected {default_type.__name__}")
                    continue
                
                self._validate_specific_value(key, value)
                
            except Exception as e:
                errors.append(f"Validation error for '{key}': {e}")
        
        if errors:
            raise ConfigError("Configuration validation failed: " + "; ".join(errors))
        
        # Apply all updates
        for key, value in updates.items():
            self.config[key] = value
        
        if save:
            self._save_config()
        
        self.logger.info(f"Updated {len(updates)} configuration values")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config.copy()
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return self.defaults.copy()
    
    def is_default(self, key: str) -> bool:
        """Check if a configuration value is set to default"""
        return self.config.get(key) == self.defaults.get(key)
    
    def get_changed_values(self) -> Dict[str, Any]:
        """Get configuration values that differ from defaults"""
        changed = {}
        for key, value in self.config.items():
            if value != self.defaults.get(key):
                changed[key] = value
        return changed
    
    def export_config(self, filename: str) -> bool:
        """Export configuration to specified file"""
        try:
            export_data = {
                'axiom_config_version': '1.0',
                'exported_at': self._get_timestamp(),
                'configuration': self.config
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, sort_keys=True)
            
            self.logger.info(f"Configuration exported to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, filename: str, merge: bool = True) -> bool:
        """Import configuration from specified file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Extract configuration data
            if 'configuration' in import_data:
                imported_config = import_data['configuration']
            else:
                imported_config = import_data
            
            if merge:
                # Merge with current configuration
                self._merge_config(imported_config)
            else:
                # Replace current configuration
                self.config = self.defaults.copy()
                self._merge_config(imported_config)
            
            self._save_config()
            self.logger.info(f"Configuration imported from {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    # Property accessors for commonly used config values
    @property
    def tab_width(self) -> int:
        return self.config['tab_width']
    
    @tab_width.setter
    def tab_width(self, value: int):
        self.set('tab_width', value)
    
    @property
    def use_spaces_for_tabs(self) -> bool:
        return self.config['use_spaces_for_tabs']
    
    @use_spaces_for_tabs.setter
    def use_spaces_for_tabs(self, value: bool):
        self.set('use_spaces_for_tabs', value)
    
    @property
    def show_line_numbers(self) -> bool:
        return self.config['show_line_numbers']
    
    @show_line_numbers.setter
    def show_line_numbers(self, value: bool):
        self.set('show_line_numbers', value)
    
    @property
    def max_file_size(self) -> int:
        return self.config['max_file_size']
    
    @property
    def syntax_highlighting(self) -> bool:
        return self.config['syntax_highlighting']
    
    @syntax_highlighting.setter
    def syntax_highlighting(self, value: bool):
        self.set('syntax_highlighting', value)
