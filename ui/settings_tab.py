import os
import configparser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QFormLayout, QCheckBox,
    QMessageBox, QSpinBox, QComboBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from ui.custom_model_dialog import CustomModelDialog

class SettingsTab(QWidget):
    """设置标签页"""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window
        self.config_manager = main_window.config_manager

        # 初始化UI
        self._init_ui()

        # 加载配置
        self._load_config()

    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        main_layout = QVBoxLayout(self)

        # 创建代理设置组
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QFormLayout()

        self.proxy_enabled = QCheckBox("启用代理")
        proxy_layout.addRow("", self.proxy_enabled)

        self.proxy_host = QLineEdit()
        proxy_layout.addRow("代理主机:", self.proxy_host)

        self.proxy_port = QSpinBox()
        self.proxy_port.setRange(1, 65535)
        self.proxy_port.setValue(10808)
        proxy_layout.addRow("代理端口:", self.proxy_port)

        proxy_group.setLayout(proxy_layout)
        main_layout.addWidget(proxy_group)

        # 创建API密钥设置组
        api_group = QGroupBox("API密钥设置")
        api_layout = QFormLayout()

        self.gpt_api_key = QLineEdit()
        self.gpt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("OpenAI API密钥:", self.gpt_api_key)

        self.claude_api_key = QLineEdit()
        self.claude_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("Anthropic API密钥:", self.claude_api_key)

        self.gemini_api_key = QLineEdit()
        self.gemini_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("Google API密钥:", self.gemini_api_key)

        # 添加自定义OpenAI兼容API密钥
        self.custom_openai_api_key = QLineEdit()
        self.custom_openai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("自定义OpenAI API密钥:", self.custom_openai_api_key)

        # 添加ModelScope API密钥
        self.modelscope_api_key = QLineEdit()
        self.modelscope_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("ModelScope Token:", self.modelscope_api_key)

        api_group.setLayout(api_layout)
        main_layout.addWidget(api_group)

        # 创建模型设置组
        model_group = QGroupBox("模型设置")
        model_layout = QFormLayout()

        self.gpt_model = QLineEdit()
        model_layout.addRow("GPT模型:", self.gpt_model)

        self.claude_model = QLineEdit()
        model_layout.addRow("Claude模型:", self.claude_model)

        self.gemini_model = QLineEdit()
        model_layout.addRow("Gemini模型:", self.gemini_model)

        # 添加自定义OpenAI兼容API模型
        self.custom_openai_model = QLineEdit()
        model_layout.addRow("自定义OpenAI模型:", self.custom_openai_model)

        # 添加ModelScope模型
        self.modelscope_model = QLineEdit()
        model_layout.addRow("ModelScope模型:", self.modelscope_model)

        model_group.setLayout(model_layout)
        main_layout.addWidget(model_group)

        # 创建自定义OpenAI API设置组
        custom_openai_group = QGroupBox("自定义OpenAI兼容API设置")
        custom_openai_layout = QFormLayout()

        self.custom_openai_enabled = QCheckBox("启用自定义OpenAI兼容API")
        custom_openai_layout.addRow("", self.custom_openai_enabled)

        self.custom_openai_url = QLineEdit()
        self.custom_openai_url.setPlaceholderText("https://your-custom-api-endpoint.com/v1/chat/completions")
        custom_openai_layout.addRow("API地址:", self.custom_openai_url)

        # 添加多模型管理按钮
        self.manage_models_button = QPushButton("管理自定义模型")
        self.manage_models_button.clicked.connect(self._manage_custom_models)
        custom_openai_layout.addRow("", self.manage_models_button)

        custom_openai_group.setLayout(custom_openai_layout)
        main_layout.addWidget(custom_openai_group)

        # ModelScope API设置已在代码中配置好，不需要在UI中显示

        # 创建按钮布局
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        self.reset_button = QPushButton("重置设置")
        self.reset_button.clicked.connect(self._load_config)
        button_layout.addWidget(self.reset_button)

        main_layout.addLayout(button_layout)

        # 添加弹性空间
        main_layout.addStretch()

    def _load_config(self):
        """加载配置"""
        config = self.config_manager.config

        # 加载代理设置
        if "PROXY" in config:
            proxy_config = config["PROXY"]
            self.proxy_enabled.setChecked(proxy_config.getboolean("enabled", True))
            self.proxy_host.setText(proxy_config.get("host", "127.0.0.1"))
            self.proxy_port.setValue(proxy_config.getint("port", 10808))

        # 加载API密钥设置
        if "API_KEYS" in config:
            api_config = config["API_KEYS"]
            self.gpt_api_key.setText(api_config.get("gpt_api_key", ""))
            self.claude_api_key.setText(api_config.get("claude_api_key", ""))
            self.gemini_api_key.setText(api_config.get("gemini_api_key", ""))
            self.custom_openai_api_key.setText(api_config.get("custom_openai_api_key", ""))
            self.modelscope_api_key.setText(api_config.get("modelscope_api_key", ""))

        # 加载模型设置
        if "MODELS" in config:
            model_config = config["MODELS"]
            self.gpt_model.setText(model_config.get("gpt_model", "gpt-4-turbo"))
            self.claude_model.setText(model_config.get("claude_model", "claude-3-opus-20240229"))
            self.gemini_model.setText(model_config.get("gemini_model", "gemini-2.0-flash"))
            self.custom_openai_model.setText(model_config.get("custom_openai_model", ""))
            self.modelscope_model.setText(model_config.get("modelscope_model", "deepseek-ai/DeepSeek-R1"))

        # 加载自定义OpenAI API设置
        if "CUSTOM_OPENAI" in config:
            custom_openai_config = config["CUSTOM_OPENAI"]
            self.custom_openai_enabled.setChecked(custom_openai_config.getboolean("enabled", False))
            self.custom_openai_url.setText(custom_openai_config.get("api_url", ""))

        # ModelScope API设置已在代码中配置好，不需要在UI中显示

    def save_settings(self):
        """保存设置"""
        config = self.config_manager.config

        # 保存代理设置
        if "PROXY" not in config:
            config["PROXY"] = {}

        config["PROXY"]["enabled"] = str(self.proxy_enabled.isChecked()).lower()
        config["PROXY"]["host"] = self.proxy_host.text()
        config["PROXY"]["port"] = str(self.proxy_port.value())

        # 保存API密钥设置
        if "API_KEYS" not in config:
            config["API_KEYS"] = {}

        config["API_KEYS"]["gpt_api_key"] = self.gpt_api_key.text()
        config["API_KEYS"]["claude_api_key"] = self.claude_api_key.text()
        config["API_KEYS"]["gemini_api_key"] = self.gemini_api_key.text()
        config["API_KEYS"]["custom_openai_api_key"] = self.custom_openai_api_key.text()
        config["API_KEYS"]["modelscope_api_key"] = self.modelscope_api_key.text()

        # 保存模型设置
        if "MODELS" not in config:
            config["MODELS"] = {}

        config["MODELS"]["gpt_model"] = self.gpt_model.text()
        config["MODELS"]["claude_model"] = self.claude_model.text()
        config["MODELS"]["gemini_model"] = self.gemini_model.text()
        config["MODELS"]["custom_openai_model"] = self.custom_openai_model.text()
        config["MODELS"]["modelscope_model"] = self.modelscope_model.text()

        # 保存自定义OpenAI API设置
        if "CUSTOM_OPENAI" not in config:
            config["CUSTOM_OPENAI"] = {}

        config["CUSTOM_OPENAI"]["enabled"] = str(self.custom_openai_enabled.isChecked()).lower()
        config["CUSTOM_OPENAI"]["api_url"] = self.custom_openai_url.text()

        # ModelScope API设置已在代码中配置好，不需要在UI中显示

        # 保存配置
        self.config_manager.save_config()

        # 显示成功消息
        QMessageBox.information(self, "保存成功", "设置已保存")

        # 提示重启应用
        QMessageBox.warning(
            self,
            "需要重启",
            "某些设置更改需要重启应用才能生效。"
        )

    def _manage_custom_models(self):
        """管理自定义模型"""
        dialog = CustomModelDialog(self, self.config_manager)
        dialog.exec()
