"""
RPA Framework 配置管理模块
提供全局配置管理和设置功能
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field


@dataclass
class GeneralSettings:
    """通用设置"""
    screenshot_dir: str = "logs/screenshots"
    template_dir: str = "templates"
    default_timeout: float = 10.0
    retry_count: int = 3
    retry_delay: float = 1.0
    debug_mode: bool = False


@dataclass
class MouseSettings:
    """鼠标操作设置"""
    move_duration: float = 0.5
    click_delay: float = 0.1
    double_click_interval: float = 0.1
    scroll_speed: int = 3
    fail_safe: bool = True


@dataclass
class KeyboardSettings:
    """键盘操作设置"""
    type_interval: float = 0.05
    key_delay: float = 0.1
    pause_after_type: float = 0.1
    auto_shift: bool = True


@dataclass
class ImageSettings:
    """图像识别设置"""
    confidence: float = 0.8
    grayscale: bool = True
    region: Optional[tuple] = None
    template_matching_method: str = "TM_CCOEFF_NORMED"
    scale_range: tuple = (0.8, 1.2)
    scale_step: float = 0.1


@dataclass
class WindowSettings:
    """窗口操作设置"""
    activate_timeout: float = 5.0
    window_search_timeout: float = 10.0
    min_window_size: tuple = (100, 100)
    default_window_state: str = "normal"  # normal, maximized, minimized


@dataclass
class LoggingSettings:
    """日志设置"""
    level: str = "INFO"
    max_file_size: str = "10MB"
    backup_count: int = 5
    log_format: str = "%(asctime)s [%(levelname)s] %(funcName)s:%(lineno)d - %(message)s"
    console_format: str = "%(log_color)s%(asctime)s [%(levelname)s] %(message)s"
    date_format: str = "%H:%M:%S"


@dataclass
class SecuritySettings:
    """安全设置"""
    enable_fail_safe: bool = True
    fail_safe_corner: str = "top-left"  # top-left, top-right, bottom-left, bottom-right
    max_operation_time: float = 300.0  # 最大操作时间（秒）
    screenshot_on_error: bool = True
    sensitive_data_mask: bool = True


@dataclass
class WechatSettings:
    """企业微信设置"""
    process_names: List[str] = field(default_factory=lambda: ["WXWork.exe", "企业微信.exe", "WeChatWork.exe", "wxwork.exe"])
    window_detection_timeout: float = 10.0
    operation_delay: float = 0.5
    template_confidence: float = 0.8
    multi_select_interval: float = 0.2
    message_send_delay: float = 1.0
    max_retry_count: int = 3
    screenshot_on_operation: bool = True

class Settings:
    """RPA框架配置管理器"""
    
    def __init__(self, config_file: str = "rpa_framework/config/settings.yaml"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(exist_ok=True)
        
        # 初始化各个配置组
        self.general = GeneralSettings()
        self.mouse = MouseSettings()
        self.keyboard = KeyboardSettings()
        self.image = ImageSettings()
        self.window = WindowSettings()
        self.logging = LoggingSettings()
        self.security = SecuritySettings()
        self.wechat = WechatSettings()
        
        self.load_config()
    
    def load_config(self):
        """从文件加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                
                # 更新各个配置组
                if 'general' in config_data:
                    self._update_dataclass(self.general, config_data['general'])
                if 'mouse' in config_data:
                    self._update_dataclass(self.mouse, config_data['mouse'])
                if 'keyboard' in config_data:
                    self._update_dataclass(self.keyboard, config_data['keyboard'])
                if 'image' in config_data:
                    self._update_dataclass(self.image, config_data['image'])
                if 'window' in config_data:
                    self._update_dataclass(self.window, config_data['window'])
                if 'logging' in config_data:
                    self._update_dataclass(self.logging, config_data['logging'])
                if 'security' in config_data:
                    self._update_dataclass(self.security, config_data['security'])
                if 'wechat' in config_data:
                    self._update_dataclass(self.wechat, config_data['wechat'])
                    
            except Exception as e:
                print(f"警告: 加载配置文件失败，使用默认配置: {e}")
        else:
            # 首次运行，创建默认配置文件
            self.save_config()
    
    def save_config(self):
        """保存配置到文件"""
        config_data = {
            'general': asdict(self.general),
            'mouse': asdict(self.mouse),
            'keyboard': asdict(self.keyboard),
            'image': asdict(self.image),
            'window': asdict(self.window),
            'logging': asdict(self.logging),
            'security': asdict(self.security),
            'wechat': asdict(self.wechat),
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
        except Exception as e:
            print(f"错误: 保存配置文件失败: {e}")
    
    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """更新数据类对象的属性"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            'general': asdict(self.general),
            'mouse': asdict(self.mouse),
            'keyboard': asdict(self.keyboard),
            'image': asdict(self.image),
            'window': asdict(self.window),
            'logging': asdict(self.logging),
            'security': asdict(self.security),
            'wechat': asdict(self.wechat),
        }
    
    def update_settings(self, section: str, **kwargs):
        """更新指定配置节的设置"""
        if section == 'general':
            for key, value in kwargs.items():
                if hasattr(self.general, key):
                    setattr(self.general, key, value)
        elif section == 'mouse':
            for key, value in kwargs.items():
                if hasattr(self.mouse, key):
                    setattr(self.mouse, key, value)
        elif section == 'keyboard':
            for key, value in kwargs.items():
                if hasattr(self.keyboard, key):
                    setattr(self.keyboard, key, value)
        elif section == 'image':
            for key, value in kwargs.items():
                if hasattr(self.image, key):
                    setattr(self.image, key, value)
        elif section == 'window':
            for key, value in kwargs.items():
                if hasattr(self.window, key):
                    setattr(self.window, key, value)
        elif section == 'logging':
            for key, value in kwargs.items():
                if hasattr(self.logging, key):
                    setattr(self.logging, key, value)
        elif section == 'security':
            for key, value in kwargs.items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)
        elif section == 'wechat':
            for key, value in kwargs.items():
                if hasattr(self.wechat, key):
                    setattr(self.wechat, key, value)
        
        # 保存更新后的配置
        self.save_config()
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self.general = GeneralSettings()
        self.mouse = MouseSettings()
        self.keyboard = KeyboardSettings()
        self.image = ImageSettings()
        self.window = WindowSettings()
        self.logging = LoggingSettings()
        self.security = SecuritySettings()
        self.save_config()
    
    def validate_settings(self) -> bool:
        """验证配置的有效性"""
        errors = []
        
        # 验证通用设置
        if self.general.default_timeout <= 0:
            errors.append("default_timeout 必须大于 0")
        if self.general.retry_count < 0:
            errors.append("retry_count 不能为负数")
        
        # 验证鼠标设置
        if self.mouse.move_duration < 0:
            errors.append("move_duration 不能为负数")
        if self.mouse.click_delay < 0:
            errors.append("click_delay 不能为负数")
        
        # 验证键盘设置
        if self.keyboard.type_interval < 0:
            errors.append("type_interval 不能为负数")
        
        # 验证图像设置
        if not 0 <= self.image.confidence <= 1:
            errors.append("confidence 必须在 0-1 之间")
        
        # 验证安全设置
        if self.security.max_operation_time <= 0:
            errors.append("max_operation_time 必须大于 0")
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取全局配置实例"""
    return settings


def reload_settings():
    """重新加载配置"""
    global settings
    settings.load_config()


def save_current_settings():
    """保存当前配置"""
    settings.save_config()


if __name__ == "__main__":
    # 测试配置管理
    print("RPA框架配置管理测试")
    print(f"配置文件: {settings.config_file}")
    print(f"截图目录: {settings.general.screenshot_dir}")
    print(f"鼠标移动时间: {settings.mouse.move_duration}")
    print(f"图像识别置信度: {settings.image.confidence}")
    print(f"配置验证结果: {settings.validate_settings()}") 