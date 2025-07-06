"""
RPA框架 - 键盘操作模块
提供完整的键盘操作功能，包括文本输入、快捷键、特殊按键等操作
"""

import time
import pyautogui
import keyboard
import threading
from enum import Enum
from typing import List, Union, Optional, Callable
from .utils import RpaLogger, RpaException, ConfigManager

# 配置PyAutoGUI
pyautogui.FAILSAFE = True  # 启用故障安全
pyautogui.PAUSE = 0.1     # 操作间隔

# Windows API导入
try:
    import win32gui
    import win32api
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    win32gui = None
    win32api = None
    win32con = None

class LanguageType(Enum):
    EN = 0x4090409  # 英文
    ZH = 0x8040804  # 中文

class KeyboardController:
    """键盘控制器类"""
    
    def __init__(self):
        self.logger = RpaLogger.get_logger(__name__)
        self.config = ConfigManager()
        self.logger.info("键盘控制器初始化完成")
        
        # 检查Windows API可用性
        if WIN32_AVAILABLE:
            self.logger.info("Windows API已加载，支持输入法切换")
        else:
            self.logger.warning("Windows API不可用，输入法切换功能将不可用")
        
        # 常用特殊按键映射
        self.special_keys = {
            'enter': 'enter',
            'tab': 'tab',
            'space': 'space',
            'backspace': 'backspace',
            'delete': 'delete',
            'escape': 'esc',
            'shift': 'shift',
            'ctrl': 'ctrl',
            'alt': 'alt',
            'win': 'win',
            'up': 'up',
            'down': 'down',
            'left': 'left',
            'right': 'right',
            'home': 'home',
            'end': 'end',
            'pageup': 'pageup',
            'pagedown': 'pagedown',
            'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
            'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
            'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12'
        }
        
        # 全局键盘监听相关
        self._global_listeners = {}
        self._listener_thread = None
        self._stop_listening = False
    
    def get_active_window_handle(self) -> Optional[int]:
        """
        获取当前活动窗口句柄
        
        Returns:
            Optional[int]: 窗口句柄，失败时返回None
        """
        if not WIN32_AVAILABLE or not win32gui:
            self.logger.warning("win32gui不可用，无法获取窗口句柄")
            return None
            
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                # 获取窗口名称
                try:
                    window_title = win32gui.GetWindowText(hwnd)
                    if window_title:
                        self.logger.debug(f"获取到活动窗口句柄: {hwnd}, 窗口名称: '{window_title}'")
                    else:
                        self.logger.debug(f"获取到活动窗口句柄: {hwnd}, 窗口名称: [无标题]")
                except Exception as title_error:
                    self.logger.debug(f"获取到活动窗口句柄: {hwnd}, 获取窗口名称失败: {title_error}")
                return hwnd
            else:
                self.logger.warning("未找到活动窗口")
                return None
        except Exception as e:
            self.logger.error(f"获取窗口句柄失败: {e}")
            return None
    
    def change_language(self, language: LanguageType) -> bool:
        """
        切换输入法语言
        
        Args:
            language: 语言类型 (LanguageType.EN 或 LanguageType.ZH)
            
        Returns:
            bool: 操作是否成功
        """
        if not WIN32_AVAILABLE or not win32api or not win32gui or not win32con:
            self.logger.error("Windows API不可用，无法切换输入法")
            return False
            
        try:
            # 获取当前活动窗口句柄
            hwnd = self.get_active_window_handle()
            if hwnd is None:
                return False
            
            # 获取系统输入法列表
            im_list = win32api.GetKeyboardLayoutList()
            im_list = list(map(hex, im_list))
            
            # 加载输入法（如果不存在）
            if hex(language.value) not in im_list:
                win32api.LoadKeyboardLayout('0000' + hex(language.value)[-4:], 1)
            
            # 发送切换消息
            result = win32gui.SendMessage(
                hwnd,
                win32con.WM_INPUTLANGCHANGEREQUEST,
                0,
                language.value)
            
            if result == 0:
                self.logger.info(f'成功切换到{language.name}输入法')
                return True
            else:
                self.logger.error(f'切换到{language.name}输入法失败')
                return False
                
        except Exception as e:
            self.logger.error(f"切换输入法失败: {e}")
            return False
    
    def type_text(self, text: str, interval: float = 0.01) -> bool:
        """
        输入文本
        
        Args:
            text: 要输入的文本
            interval: 字符间输入间隔（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"输入文本: '{text}', 间隔: {interval}s")
            pyautogui.typewrite(text, interval=interval)
            return True
        except Exception as e:
            self.logger.error(f"文本输入失败: {e}")
            raise RpaException(f"文本输入失败: {e}")
    
    def press_key(self, key: str, presses: int = 1, interval: float = 0.1) -> bool:
        """
        按下指定按键
        
        Args:
            key: 按键名称
            presses: 按键次数
            interval: 多次按键间隔（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 转换为PyAutoGUI识别的按键名
            key_name = self.special_keys.get(key.lower(), key)
            self.logger.info(f"按下按键: '{key_name}', 次数: {presses}, 间隔: {interval}s")
            pyautogui.press(key_name, presses=presses, interval=interval)
            return True
        except Exception as e:
            self.logger.error(f"按键操作失败: {e}")
            raise RpaException(f"按键操作失败: {e}")
    
    def key_down(self, key: str) -> bool:
        """
        按下并保持按键
        
        Args:
            key: 按键名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            key_name = self.special_keys.get(key.lower(), key)
            self.logger.info(f"按下并保持按键: '{key_name}'")
            pyautogui.keyDown(key_name)
            return True
        except Exception as e:
            self.logger.error(f"按下按键失败: {e}")
            raise RpaException(f"按下按键失败: {e}")
    
    def key_up(self, key: str) -> bool:
        """
        释放按键
        
        Args:
            key: 按键名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            key_name = self.special_keys.get(key.lower(), key)
            self.logger.info(f"释放按键: '{key_name}'")
            pyautogui.keyUp(key_name)
            return True
        except Exception as e:
            self.logger.error(f"释放按键失败: {e}")
            raise RpaException(f"释放按键失败: {e}")
    
    def hotkey(self, *keys) -> bool:
        """
        按下组合键（快捷键）
        
        Args:
            *keys: 按键组合，如 'ctrl', 'c'
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 转换按键名称
            key_names = [self.special_keys.get(key.lower(), key) for key in keys]
            self.logger.info(f"按下组合键: {' + '.join(key_names)}")
            pyautogui.hotkey(*key_names)
            return True
        except Exception as e:
            self.logger.error(f"组合键操作失败: {e}")
            raise RpaException(f"组合键操作失败: {e}")
    
    def key_combination(self, keys: List[str], hold_duration: float = 0.1) -> bool:
        """
        自定义按键组合操作
        
        Args:
            keys: 按键列表，按顺序按下
            hold_duration: 按键保持时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"执行按键组合: {keys}, 保持时间: {hold_duration}s")
            
            # 按顺序按下所有按键
            for key in keys:
                self.key_down(key)
                time.sleep(0.01)  # 短暂延迟确保按键生效
            
            # 保持指定时间
            time.sleep(hold_duration)
            
            # 按相反顺序释放所有按键
            for key in reversed(keys):
                self.key_up(key)
                time.sleep(0.01)
            
            return True
        except Exception as e:
            self.logger.error(f"按键组合操作失败: {e}")
            raise RpaException(f"按键组合操作失败: {e}")
    
    def clear_text(self, method: str = 'ctrl_a') -> bool:
        """
        清除文本内容
        
        Args:
            method: 清除方法 ('ctrl_a' - 全选删除, 'backspace' - 退格删除)
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"清除文本，方法: {method}")
            
            if method == 'ctrl_a':
                # 全选 + 删除
                self.hotkey('ctrl', 'a')
                time.sleep(0.1)
                self.press_key('delete')
            elif method == 'backspace':
                # 多次退格（适用于不支持全选的场景）
                for _ in range(50):  # 最多删除50个字符
                    self.press_key('backspace', interval=0.01)
            else:
                raise ValueError(f"不支持的清除方法: {method}")
            
            return True
        except Exception as e:
            self.logger.error(f"清除文本失败: {e}")
            raise RpaException(f"清除文本失败: {e}")
    
    def select_all(self) -> bool:
        """全选文本"""
        return self.hotkey('ctrl', 'a')
    
    def copy(self) -> bool:
        """复制"""
        return self.hotkey('ctrl', 'c')
    
    def paste(self) -> bool:
        """粘贴"""
        return self.hotkey('ctrl', 'v')
    
    def cut(self) -> bool:
        """剪切"""
        return self.hotkey('ctrl', 'x')
    
    def undo(self) -> bool:
        """撤销"""
        return self.hotkey('ctrl', 'z')
    
    def redo(self) -> bool:
        """重做"""
        return self.hotkey('ctrl', 'y')
    
    def save(self) -> bool:
        """保存"""
        return self.hotkey('ctrl', 's')
    
    def find(self) -> bool:
        """查找"""
        return self.hotkey('ctrl', 'f')
    
    def replace(self) -> bool:
        """替换"""
        return self.hotkey('ctrl', 'h')
    
    def new_tab(self) -> bool:
        """新建标签页"""
        return self.hotkey('ctrl', 't')
    
    def close_tab(self) -> bool:
        """关闭标签页"""
        return self.hotkey('ctrl', 'w')
    
    def refresh(self) -> bool:
        """刷新"""
        return self.hotkey('f5')
    
    def alt_tab(self) -> bool:
        """切换应用程序"""
        return self.hotkey('alt', 'tab')
    
    def win_key(self) -> bool:
        """Windows键"""
        return self.press_key('win')
    
    def type_with_delay(self, text: str, word_delay: float = 0.1, char_delay: float = 0.01) -> bool:
        """
        带延迟的文本输入（模拟人工输入）
        
        Args:
            text: 要输入的文本
            word_delay: 单词间延迟（秒）
            char_delay: 字符间延迟（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"模拟人工输入文本: '{text}'")
            
            words = text.split(' ')
            for i, word in enumerate(words):
                # 输入单词
                for char in word:
                    pyautogui.typewrite(char)
                    time.sleep(char_delay)
                
                # 如果不是最后一个单词，添加空格和单词间延迟
                if i < len(words) - 1:
                    pyautogui.typewrite(' ')
                    time.sleep(word_delay)
            
            return True
        except Exception as e:
            self.logger.error(f"模拟输入失败: {e}")
            raise RpaException(f"模拟输入失败: {e}")
    
    def add_global_hotkey(self, key: str, callback: Callable, suppress: bool = False) -> bool:
        """
        添加全局热键监听
        
        Args:
            key: 热键名称（如 'f12', 'ctrl+c' 等）
            callback: 回调函数
            suppress: 是否抑制原始按键事件
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"添加全局热键监听: {key}")
            
            # 使用keyboard库添加热键
            keyboard.add_hotkey(key, callback, suppress=suppress)
            self._global_listeners[key] = callback
            
            return True
        except Exception as e:
            self.logger.error(f"添加全局热键失败: {e}")
            return False
    
    def remove_global_hotkey(self, key: str) -> bool:
        """
        移除全局热键监听
        
        Args:
            key: 热键名称
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"移除全局热键监听: {key}")
            
            if key in self._global_listeners:
                keyboard.remove_hotkey(key)
                del self._global_listeners[key]
                return True
            else:
                self.logger.warning(f"未找到热键监听: {key}")
                return False
        except Exception as e:
            self.logger.error(f"移除全局热键失败: {e}")
            return False
    
    def start_global_listener(self) -> bool:
        """
        启动全局键盘监听
        
        Returns:
            bool: 操作是否成功
        """
        try:
            if self._listener_thread is not None and self._listener_thread.is_alive():
                self.logger.warning("全局键盘监听已在运行")
                return True
            
            self.logger.info("启动全局键盘监听")
            self._stop_listening = False
            
            def listener_worker():
                try:
                    # 开始监听键盘事件
                    keyboard.wait()
                except Exception as e:
                    self.logger.error(f"键盘监听线程异常: {e}")
            
            self._listener_thread = threading.Thread(target=listener_worker, daemon=True)
            self._listener_thread.start()
            
            return True
        except Exception as e:
            self.logger.error(f"启动全局键盘监听失败: {e}")
            return False
    
    def stop_global_listener(self) -> bool:
        """
        停止全局键盘监听
        
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info("停止全局键盘监听")
            
            # 清除所有热键
            for key in list(self._global_listeners.keys()):
                self.remove_global_hotkey(key)
            
            # 停止监听
            self._stop_listening = True
            
            # 等待监听线程结束
            if self._listener_thread is not None and self._listener_thread.is_alive():
                self._listener_thread.join(timeout=1.0)
            
            return True
        except Exception as e:
            self.logger.error(f"停止全局键盘监听失败: {e}")
            return False
    
    def is_listening(self) -> bool:
        """
        检查是否正在监听
        
        Returns:
            bool: 是否正在监听
        """
        return (self._listener_thread is not None and 
                self._listener_thread.is_alive() and 
                not self._stop_listening)

# 全局键盘控制器实例（延迟创建）
_global_keyboard = None

def _get_global_keyboard():
    """获取全局键盘控制器实例（延迟创建）"""
    global _global_keyboard
    if _global_keyboard is None:
        _global_keyboard = KeyboardController()
    return _global_keyboard

# 便捷函数
def type_text(text: str, interval: float = 0.01) -> bool:
    """输入文本"""
    return _get_global_keyboard().type_text(text, interval)

def press_key(key: str, presses: int = 1) -> bool:
    """按键"""
    return _get_global_keyboard().press_key(key, presses)

def hotkey(*keys) -> bool:
    """快捷键"""
    return _get_global_keyboard().hotkey(*keys)

def copy() -> bool:
    """复制"""
    return _get_global_keyboard().copy()

def paste() -> bool:
    """粘贴"""
    return _get_global_keyboard().paste()

def select_all() -> bool:
    """全选"""
    return _get_global_keyboard().select_all()

def clear_text(method: str = 'ctrl_a') -> bool:
    """清除文本"""
    return _get_global_keyboard().clear_text(method)

def change_language(language: LanguageType) -> bool:
    """切换输入法语言"""
    return _get_global_keyboard().change_language(language)

def add_global_hotkey(key: str, callback: Callable, suppress: bool = False) -> bool:
    """添加全局热键监听"""
    return _get_global_keyboard().add_global_hotkey(key, callback, suppress)

def remove_global_hotkey(key: str) -> bool:
    """移除全局热键监听"""
    return _get_global_keyboard().remove_global_hotkey(key)

def start_global_listener() -> bool:
    """启动全局键盘监听"""
    return _get_global_keyboard().start_global_listener()

def stop_global_listener() -> bool:
    """停止全局键盘监听"""
    return _get_global_keyboard().stop_global_listener()

def is_listening() -> bool:
    """检查是否正在监听"""
    return _get_global_keyboard().is_listening() 