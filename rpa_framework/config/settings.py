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
    level: str = "DEBUG"  # 默认显示所有等级日志
    max_file_size: str = "10MB"
    backup_count: int = 5
    log_format: str = "%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s"
    console_format: str = "%(log_color)s%(asctime)s [%(levelname)s] [%(name)s] %(caller_file)s:%(caller_line)d - %(message)s"
    date_format: str = "%H:%M:%S"
    enable_master_log: bool = True  # 启用总日志文件
    master_log_format: str = "%(asctime)s [%(levelname)s] [%(module_name)s] %(caller_file)s:%(caller_line)d - %(message)s"


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
    # 窗口配置
    window_size: Dict[str, int] = field(default_factory=lambda: {"width": 1200, "height": 800})
    window_position: Dict[str, int] = field(default_factory=lambda: {"x": 100, "y": 100})
    # 疯狂连点配置
    crazy_click_settings: Dict[str, Any] = field(default_factory=lambda: {
        "clicks_per_group": 100,     # 每组连点次数
        "group_interval": 2.0,       # 组间隔时间（秒）
        "total_groups": 6,           # 总组数
        "click_interval": 0.01       # 单次点击间隔
    })

class Settings:
    """RPA框架配置管理器"""
    
    def __init__(self, config_file: str = "config/settings.yaml"):
        # 获取项目根目录
        project_root = Path(__file__).parent.parent
        self.config_file = project_root / config_file
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

    def update_wechat_window_config(self, width: int, height: int, x: int, y: int) -> bool:
        """
        更新企业微信窗口配置（只更新窗口相关配置，保持其他配置不变）
        
        Args:
            width: 窗口宽度
            height: 窗口高度
            x: 窗口x坐标
            y: 窗口y坐标
            
        Returns:
            bool: 是否成功保存
        """
        try:
            # 首先更新内存中的配置
            self.wechat.window_size = {"width": width, "height": height}
            self.wechat.window_position = {"x": x, "y": y}
            
            # 读取现有的YAML文件内容
            if not self.config_file.exists():
                # 如果文件不存在，使用完整保存
                self.save_config()
                print(f"✅ 企业微信窗口配置已创建: 大小({width}x{height}), 位置({x}, {y})")
                return True
            
            # 读取现有配置
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            
            # 确保wechat节存在
            if 'wechat' not in config_data:
                config_data['wechat'] = {}
            
            # 只更新窗口相关配置
            config_data['wechat']['window_size'] = {"width": width, "height": height}
            config_data['wechat']['window_position'] = {"x": x, "y": y}
            
            # 写回文件，使用相同的格式选项
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2, sort_keys=False)
            
            print(f"✅ 企业微信窗口配置已更新: 大小({width}x{height}), 位置({x}, {y})")
            return True
            
        except Exception as e:
            print(f"❌ 更新企业微信窗口配置失败: {str(e)}")
            return False
    
    def get_wechat_window_config(self) -> Dict[str, Dict[str, int]]:
        """
        获取企业微信窗口配置
        
        Returns:
            Dict: 包含window_size和window_position的字典
        """
        return {
            "window_size": self.wechat.window_size,
            "window_position": self.wechat.window_position
        }

    def get_crazy_click_config(self) -> Dict[str, Any]:
        """
        获取疯狂连点配置
        
        Returns:
            Dict: 疯狂连点配置字典
        """
        return self.wechat.crazy_click_settings

    def validate_crazy_click_settings(self) -> bool:
        """
        验证疯狂连点配置的有效性
        
        Returns:
            bool: 配置是否有效
        """
        errors = []
        config = self.wechat.crazy_click_settings
        
        # 验证每组连点次数
        if config.get('clicks_per_group', 0) <= 0:
            errors.append("clicks_per_group 必须大于 0")
        
        # 验证组间隔时间
        if config.get('group_interval', 0) < 0:
            errors.append("group_interval 不能为负数")
        
        # 验证总组数
        if config.get('total_groups', 0) <= 0:
            errors.append("total_groups 必须大于 0")
        
        # 验证单次点击间隔
        if config.get('click_interval', 0) < 0:
            errors.append("click_interval 不能为负数")
        
        if errors:
            print("疯狂连点配置验证失败:")
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