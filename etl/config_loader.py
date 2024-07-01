import os
import yaml

# Default values can be defined here if necessary
DEFAULT_CONFIG = {
    "CHROMA_HOST": 'locahost',
    "CHROMA_PORT": '8000',
    "EMBEDDING_FUNCTION": 'thenlper/gte-large',
    "EMBEDDING_DEVICE": 'cpu'
}

class ConfigLoader:
    def __init__(self, config_file='config.yml'):
        self.config_file = config_file
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self):
        """
        Load configurations from the config.yml file if it exists. If not, load from environment variables.
        If the variables are not defined in either, use the default values.
        """
        if os.path.exists(self.config_file):
            self.load_from_file()
        self.load_from_env()

    def load_from_file(self):
        """Load configuration from the YAML file."""
        try:
            with open(self.config_file, 'r') as file:
                file_config = yaml.safe_load(file)
                if file_config:
                    self.config.update(file_config)
        except yaml.YAMLError as e:
            print(f"Error reading YAML file: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def load_from_env(self):
        """Load configuration from the environment variables."""
        for key in self.config:
            env_value = os.environ.get(key)
            if env_value is not None:
                self.config[key] = env_value

    def get_config(self):
        """Return the configuration dictionary."""
        return self.config

if __name__ == "__main__":
    config_loader = ConfigLoader()
    config = config_loader.get_config()
    print(config)