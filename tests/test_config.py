import pytest
from config import TestLoader as ConfigLoader



class TestConfigLoader:
    default_config = "tests/assets/config.yml"
    custom_config = "tests/assets/custom.yml"
    empty_config = "tests/assets/empty.yml"

    def test_load_default_config(self):
        loader = ConfigLoader(default_config_path=self.default_config, custom_config_path=self.empty_config)
        config = loader.default_config
        assert config is not None  # Add more specific checks based on your default config

    def test_load_custom_config(self):
        loader = ConfigLoader( custom_config_path=self.custom_config)
        config = loader.custom_config
        assert config is not None  # Add more specific checks based on your custom config

    def test_missing_required_fields(self):
        loader = ConfigLoader(default_config_path="tests/assets/incomplete.yml", custom_config_path=self.empty_config)
        with pytest.raises(ValueError):
            _ = loader.merged_config

    def test_task_validation_logic(self):
        loader = ConfigLoader(default_config_path="tests/assets/invalid_task.yml", custom_config_path=self.empty_config)
        with pytest.raises(ValueError):
            _ = loader.merged_config

    def test_file_not_found(self):
        loader = ConfigLoader(default_config_path="nonexistent.yml", custom_config_path=self.empty_config)
        with pytest.raises(FileNotFoundError):
            _ = loader.default_config

    def test_config_merging(self):
        loader = ConfigLoader(default_config_path=self.default_config, custom_config_path=self.custom_config)
        merged_config = loader.merged_config

        # Check if values not in custom.yml retain their original values from default_config.yml
        assert merged_config['server']['name'] == "DefaultServer"
        assert merged_config['server']['port'] == 7777

        # Check if values from custom.yml override those in default_config.yml
        assert merged_config['server']['max_players'] == 30
        assert merged_config['server']['ip_address'] == "192.168.1.101"