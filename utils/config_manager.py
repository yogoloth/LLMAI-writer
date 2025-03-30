import configparser
import os

class ConfigManager:
    """配置管理器，负责读取和管理配置文件"""

    def __init__(self, config_path='config.ini'):
        self.config_path = config_path
        self.config = configparser.ConfigParser()

        if os.path.exists(config_path):
            self.config.read(config_path, encoding='utf-8')
        else:
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置文件"""
        self.config['PROXY'] = {
            'enabled': 'true',
            'host': '127.0.0.1',
            'port': '10808'
        }

        self.config['API_KEYS'] = {
            'gpt_api_key': 'your_openai_api_key_here',
            'claude_api_key': 'your_anthropic_api_key_here',
            'gemini_api_key': 'your_google_api_key_here'
        }

        self.config['MODELS'] = {
            'gpt_model': 'gpt-4-turbo',
            'claude_model': 'claude-3-opus-20240229',
            'gemini_model': 'gemini-2.0-flash'
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get_proxy_settings(self):
        """获取代理设置"""
        if 'PROXY' not in self.config:
            return None

        proxy_config = self.config['PROXY']
        enabled = proxy_config.getboolean('enabled', fallback=True)

        if not enabled:
            return None

        host = proxy_config.get('host', fallback='127.0.0.1')
        port = proxy_config.getint('port', fallback=10808)

        return {
            'http': f'http://{host}:{port}',
            'https': f'http://{host}:{port}'
        }

    def get_api_key(self, model_type):
        """获取指定模型的API密钥"""
        if 'API_KEYS' not in self.config:
            return None

        key_name = f'{model_type}_api_key'
        return self.config['API_KEYS'].get(key_name, None)

    def get_model_name(self, model_type):
        """获取指定类型的模型名称"""
        if 'MODELS' not in self.config:
            return None

        model_name = f'{model_type}_model'
        return self.config['MODELS'].get(model_name, None)

    def save_config(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
