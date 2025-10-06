#!/usr/bin/env python3
"""
🧪 Unit Tests for Configuration Manager
"""

import unittest
import sys
import os
from pathlib import Path
import tempfile
import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigManager, get_config, is_live_mode, is_paper_mode


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Create temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
        
        # Create test config
        test_config = {
            'ibkr': {
                'port': 7497,
                'client_id': 1,
                'host': '127.0.0.1'
            },
            'strategy': {
                'dte_min': 21,
                'dte_max': 45,
                'delta_target': 0.30
            },
            'risk': {
                'max_trades_per_day': 5
            },
            'modes': {
                'default_mode': 'paper'
            },
            'logging': {
                'level': 'INFO'
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._config = None
        
        # Create config manager with test file
        self.config = ConfigManager(self.config_path)
    
    def tearDown(self):
        """Cleanup after tests"""
        # Clean up temp files
        if self.config_path.exists():
            self.config_path.unlink()
        
        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._config = None
    
    def test_singleton_pattern(self):
        """Test that ConfigManager uses singleton pattern"""
        config1 = ConfigManager(self.config_path)
        config2 = ConfigManager(self.config_path)
        
        self.assertIs(config1, config2, "ConfigManager should be singleton")
    
    def test_load_config(self):
        """Test loading configuration from file"""
        port = self.config.get('ibkr.port')
        self.assertEqual(port, 7497, "Should load port from config")
        
        dte_min = self.config.get('strategy.dte_min')
        self.assertEqual(dte_min, 21, "Should load dte_min from config")
    
    def test_get_nested_key(self):
        """Test getting nested configuration values"""
        # Test nested access with dot notation
        port = self.config.get('ibkr.port')
        self.assertEqual(port, 7497)
        
        delta = self.config.get('strategy.delta_target')
        self.assertEqual(delta, 0.30)
    
    def test_get_with_default(self):
        """Test getting value with default fallback"""
        # Existing key
        port = self.config.get('ibkr.port', 9999)
        self.assertEqual(port, 7497)
        
        # Missing key should return default
        missing = self.config.get('missing.key', 'DEFAULT')
        self.assertEqual(missing, 'DEFAULT')
    
    def test_set_value(self):
        """Test setting configuration values"""
        # Set new value
        self.config.set('strategy.dte_min', 30)
        
        # Verify it was set
        new_value = self.config.get('strategy.dte_min')
        self.assertEqual(new_value, 30)
    
    def test_get_section(self):
        """Test getting entire configuration section"""
        ibkr_section = self.config.get_section('ibkr')
        
        self.assertIsInstance(ibkr_section, dict)
        self.assertIn('port', ibkr_section)
        self.assertEqual(ibkr_section['port'], 7497)
    
    def test_validation(self):
        """Test configuration validation"""
        is_valid = self.config.validate()
        self.assertTrue(is_valid, "Test config should be valid")
    
    def test_validation_missing_section(self):
        """Test validation fails with missing required section"""
        # Remove required section
        del self.config._config['ibkr']
        
        is_valid = self.config.validate()
        self.assertFalse(is_valid, "Should fail validation with missing section")
    
    def test_env_override(self):
        """Test environment variable override"""
        # Set environment variable
        os.environ['CC_IBKR_PORT'] = '7496'
        
        # Reset and reload config
        ConfigManager._instance = None
        ConfigManager._config = None
        config = ConfigManager(self.config_path)
        
        # Check if env var overrode config
        port = config.get('ibkr.port')
        self.assertEqual(port, 7496, "Env var should override config file")
        
        # Cleanup
        del os.environ['CC_IBKR_PORT']
    
    def test_type_conversion(self):
        """Test automatic type conversion"""
        # Test boolean conversion
        self.assertEqual(self.config._convert_type('true'), True)
        self.assertEqual(self.config._convert_type('false'), False)
        
        # Test int conversion
        self.assertEqual(self.config._convert_type('123'), 123)
        
        # Test float conversion
        self.assertEqual(self.config._convert_type('1.23'), 1.23)
        
        # Test string (no conversion)
        self.assertEqual(self.config._convert_type('hello'), 'hello')
    
    def test_to_dict(self):
        """Test converting config to dictionary"""
        config_dict = self.config.to_dict()
        
        self.assertIsInstance(config_dict, dict)
        self.assertIn('ibkr', config_dict)
        self.assertIn('strategy', config_dict)


class TestQuickAccessFunctions(unittest.TestCase):
    """Test quick access helper functions"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Create temporary config
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
        
        test_config = {
            'ibkr': {'port': 7497},
            'strategy': {'dte_min': 21},
            'risk': {'max_trades_per_day': 5},
            'modes': {'default_mode': 'paper'},
            'logging': {'level': 'INFO'}
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._config = None
        
        # Initialize with test config
        ConfigManager(self.config_path)
    
    def tearDown(self):
        """Cleanup"""
        if self.config_path.exists():
            self.config_path.unlink()
        ConfigManager._instance = None
        ConfigManager._config = None
    
    def test_is_paper_mode(self):
        """Test paper mode detection"""
        self.assertTrue(is_paper_mode())
        self.assertFalse(is_live_mode())
    
    def test_is_live_mode(self):
        """Test live mode detection"""
        config = get_config()
        config.set('modes.default_mode', 'live')
        
        self.assertTrue(is_live_mode())
        self.assertFalse(is_paper_mode())


# ==================== Run Tests ====================

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestQuickAccessFunctions))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success/failure
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running Config Manager Tests\n")
    print("=" * 60)
    
    success = run_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)
