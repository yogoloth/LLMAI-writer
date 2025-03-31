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
            'gemini_api_key': 'your_google_api_key_here',
            'custom_openai_api_key': 'your_custom_api_key_here',
            'modelscope_api_key': 'your_modelscope_token_here'
        }

        self.config['MODELS'] = {
            'gpt_model': 'gpt-4-turbo',
            'claude_model': 'claude-3-opus-20240229',
            'gemini_model': 'gemini-2.0-flash',
            'custom_openai_model': 'your_custom_model_name_here',
            'modelscope_model': 'deepseek-ai/DeepSeek-R1'
        }

        self.config['CUSTOM_OPENAI'] = {
            'enabled': 'false',
            'api_url': 'https://your-custom-api-endpoint.com/v1/chat/completions'
        }

        self.config['MODELSCOPE'] = {
            'enabled': 'false',
            'base_url': 'https://api-inference.modelscope.cn/v1/'
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

    def get_config(self, section, key, default=None):
        """获取指定配置项"""
        if section not in self.config:
            return default

        return self.config[section].get(key, default)

    def set_config(self, section, key, value):
        """设置指定配置项"""
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = str(value)

    def is_custom_openai_enabled(self):
        """检查自定义OpenAI API是否启用"""
        if 'CUSTOM_OPENAI' not in self.config:
            return False

        return self.config['CUSTOM_OPENAI'].getboolean('enabled', fallback=False)

    def is_modelscope_enabled(self):
        """检查ModelScope API是否启用"""
        if 'MODELSCOPE' not in self.config:
            return False

        return self.config['MODELSCOPE'].getboolean('enabled', fallback=False)

    def save_config(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)
