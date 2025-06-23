"""
RPA框架 - 键盘操作模块
提供完整的键盘操作功能，包括文本输入、快捷键、特殊按键等操作
"""

import time
import pyautogui
import ctypes
from ctypes import wintypes
from typing import List, Union, Optional
from .utils import RpaLogger, RpaException, ConfigManager

# 配置PyAutoGUI
pyautogui.FAILSAFE = True  # 启用故障安全
pyautogui.PAUSE = 0.1     # 操作间隔

# Windows IMM32 API 声明
try:
    # 导入Windows API库
    import win32gui
    import win32api
    
    # IMM32 API函数声明
    imm32 = ctypes.windll.imm32
    user32 = ctypes.windll.user32
    
    # 定义Windows数据类型
    HWND = wintypes.HWND
    HIMC = wintypes.HANDLE
    BOOL = wintypes.BOOL
    DWORD = wintypes.DWORD
    
    # 设置函数原型
    # ImmGetContext - 获取输入法上下文
    ImmGetContext = imm32.ImmGetContext
    ImmGetContext.argtypes = [HWND]
    ImmGetContext.restype = HIMC
    
    # ImmReleaseContext - 释放输入法上下文
    ImmReleaseContext = imm32.ImmReleaseContext
    ImmReleaseContext.argtypes = [HWND, HIMC]
    ImmReleaseContext.restype = BOOL
    
    # ImmGetOpenStatus - 获取输入法开启状态
    ImmGetOpenStatus = imm32.ImmGetOpenStatus
    ImmGetOpenStatus.argtypes = [HIMC]
    ImmGetOpenStatus.restype = BOOL
    
    # ImmSetOpenStatus - 设置输入法开启状态
    ImmSetOpenStatus = imm32.ImmSetOpenStatus
    ImmSetOpenStatus.argtypes = [HIMC, BOOL]
    ImmSetOpenStatus.restype = BOOL
    
    # Windows常量定义
    IME_CMODE_ALPHANUMERIC = 0x0000  # 英文模式
    IME_CMODE_NATIVE = 0x0001        # 本地语言模式
    
    # IMM32 API可用性标志
    IMM32_AVAILABLE = True
    
except (ImportError, AttributeError) as e:
    # 如果导入失败，设置为不可用状态
    IMM32_AVAILABLE = False
    win32gui = None
    win32api = None
    ImmGetContext = None
    ImmReleaseContext = None
    ImmGetOpenStatus = None
    ImmSetOpenStatus = None

class KeyboardController:
    """键盘控制器类"""
    
    def __init__(self):
        self.logger = RpaLogger.get_logger(__name__)
        self.config = ConfigManager()
        self.logger.info("键盘控制器初始化完成")
        
        # 加载IME控制配置
        ime_config = self.config.get('keyboard.ime_control', {})
        
        # IME控制相关属性
        self._ime_api_available = IMM32_AVAILABLE and ime_config.get('enabled', True)
        self._ime_state_cache = {}
        self._fallback_enabled = ime_config.get('fallback_enabled', True)
        self._debug_mode = ime_config.get('debug_mode', False)
        self._auto_restore = ime_config.get('auto_restore', True)
        
        # 记录IME API可用性和配置
        if self._ime_api_available:
            self.logger.info("IMM32 API已加载，支持输入法控制")
            if self._debug_mode:
                self.logger.info(f"IME控制配置: 降级={self._fallback_enabled}, 调试={self._debug_mode}, 自动恢复={self._auto_restore}")
        else:
            if not IMM32_AVAILABLE:
                self.logger.warning("IMM32 API不可用，将使用降级方案")
            else:
                self.logger.info("IME控制已通过配置禁用")
        
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
    
    def get_active_window_handle(self) -> Optional[int]:
        """
        获取当前活动窗口句柄
        
        Returns:
            Optional[int]: 窗口句柄，失败时返回None
        """
        if not self._ime_api_available or not win32gui:
            self.logger.warning("win32gui不可用，无法获取窗口句柄")
            return None
            
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                if self._debug_mode:
                    try:
                        # 获取窗口标题用于调试
                        window_title = win32gui.GetWindowText(hwnd)
                        self.logger.debug(f"获取到活动窗口句柄: {hwnd}, 标题: '{window_title}'")
                    except:
                        self.logger.debug(f"获取到活动窗口句柄: {hwnd}")
                else:
                    self.logger.debug(f"获取到活动窗口句柄: {hwnd}")
                return hwnd
            else:
                self.logger.warning("未找到活动窗口")
                return None
        except Exception as e:
            self.logger.error(f"获取窗口句柄失败: {e}")
            return None
    
    def get_ime_status(self, hwnd: Optional[int] = None) -> Optional[bool]:
        """
        获取指定窗口的输入法开启状态
        
        Args:
            hwnd: 窗口句柄，为None时自动获取当前活动窗口
            
        Returns:
            Optional[bool]: 输入法状态，True为开启，False为关闭，None为获取失败
        """
        if not self._ime_api_available or not ImmGetContext or not ImmGetOpenStatus or not ImmReleaseContext:
            self.logger.warning("IMM32 API不可用，无法获取输入法状态")
            return None
            
        if hwnd is None:
            hwnd = self.get_active_window_handle()
            if hwnd is None:
                return None
        
        try:
            # 获取输入法上下文
            himc = ImmGetContext(hwnd)
            if not himc:
                self.logger.debug(f"窗口 {hwnd} 无输入法上下文")
                return False
            
            try:
                # 获取输入法开启状态
                status = ImmGetOpenStatus(himc)
                self.logger.debug(f"窗口 {hwnd} 输入法状态: {'开启' if status else '关闭'}")
                return bool(status)
            finally:
                # 释放输入法上下文
                ImmReleaseContext(hwnd, himc)
                
        except Exception as e:
            self.logger.error(f"获取输入法状态失败: {e}")
            return None
    
    def set_ime_status(self, enabled: bool, hwnd: Optional[int] = None) -> bool:
        """
        设置指定窗口的输入法开启状态
        
        Args:
            enabled: 输入法状态，True为开启，False为关闭
            hwnd: 窗口句柄，为None时自动获取当前活动窗口
            
        Returns:
            bool: 操作是否成功
        """
        if not self._ime_api_available or not ImmGetContext or not ImmSetOpenStatus or not ImmReleaseContext:
            self.logger.warning("IMM32 API不可用，尝试使用降级方案")
            return self._fallback_ime_control(enabled)
            
        if hwnd is None:
            hwnd = self.get_active_window_handle()
            if hwnd is None:
                return False
        
        try:
            # 获取输入法上下文
            himc = ImmGetContext(hwnd)
            if not himc:
                self.logger.warning(f"窗口 {hwnd} 无输入法上下文")
                return False
            
            try:
                # 设置输入法开启状态
                result = ImmSetOpenStatus(himc, enabled)
                if result:
                    self.logger.info(f"成功设置窗口 {hwnd} 输入法状态为: {'开启' if enabled else '关闭'}")
                    return True
                else:
                    self.logger.error(f"设置窗口 {hwnd} 输入法状态失败")
                    return False
            finally:
                # 释放输入法上下文
                ImmReleaseContext(hwnd, himc)
                
        except Exception as e:
            self.logger.error(f"设置输入法状态失败: {e}")
            if self._fallback_enabled:
                self.logger.info("尝试使用降级方案")
                return self._fallback_ime_control(enabled)
            return False
    
    def _fallback_ime_control(self, enabled: bool) -> bool:
        """
        输入法控制的降级方案（使用快捷键）
        
        Args:
            enabled: 输入法状态，True为开启，False为关闭
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not enabled:
                # 关闭输入法：尝试Shift键切换到英文模式
                self.logger.info("使用Shift键降级方案关闭输入法")
                self.press_key('shift')
                time.sleep(0.1)
                return True
            else:
                # 开启输入法：这个降级方案有限制，只记录警告
                self.logger.warning("降级方案无法可靠地开启输入法")
                return False
        except Exception as e:
            self.logger.error(f"降级方案执行失败: {e}")
            return False
    
    def disable_ime_temporarily(self, hwnd: Optional[int] = None) -> Optional[bool]:
        """
        临时关闭输入法，返回原始状态用于后续恢复
        
        Args:
            hwnd: 窗口句柄，为None时自动获取当前活动窗口
            
        Returns:
            Optional[bool]: 原始输入法状态，None表示操作失败
        """
        try:
            # 获取当前状态
            original_status = self.get_ime_status(hwnd)
            if original_status is None:
                self.logger.error("无法获取当前输入法状态")
                return None
            
            # 保存状态到缓存
            if hwnd is None:
                hwnd = self.get_active_window_handle()
            
            if hwnd:
                self._ime_state_cache[hwnd] = {
                    'original_status': original_status,
                    'timestamp': time.time(),
                    'context_valid': True
                }
            
            # 如果当前是开启状态，则关闭
            if original_status:
                success = self.set_ime_status(False, hwnd)
                if success:
                    self.logger.info("已临时关闭输入法")
                else:
                    self.logger.error("临时关闭输入法失败")
                    return None
            else:
                self.logger.debug("输入法已处于关闭状态")
            
            return original_status
            
        except Exception as e:
            self.logger.error(f"临时关闭输入法失败: {e}")
            return None
    
    def restore_ime_status(self, original_status: bool, hwnd: Optional[int] = None) -> bool:
        """
        根据保存的状态恢复输入法
        
        Args:
            original_status: 原始输入法状态
            hwnd: 窗口句柄，为None时自动获取当前活动窗口
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if hwnd is None:
                hwnd = self.get_active_window_handle()
            
            # 检查缓存中的状态信息
            if hwnd and hwnd in self._ime_state_cache:
                cached_info = self._ime_state_cache[hwnd]
                if cached_info['original_status'] != original_status:
                    self.logger.warning("传入的原始状态与缓存不一致")
                # 清理缓存
                del self._ime_state_cache[hwnd]
            
            # 恢复输入法状态
            success = self.set_ime_status(original_status, hwnd)
            if success:
                self.logger.info(f"已恢复输入法状态为: {'开启' if original_status else '关闭'}")
            else:
                self.logger.error("恢复输入法状态失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"恢复输入法状态失败: {e}")
            return False
    
    def ensure_english_input(self, hwnd: Optional[int] = None) -> Optional[bool]:
        """
        确保英文输入环境（重构现有方法使用新API）
        
        Args:
            hwnd: 窗口句柄，为None时自动获取当前活动窗口
            
        Returns:
            Optional[bool]: 原始输入法状态，用于后续恢复，None表示操作失败
        """
        try:
            self.logger.info("确保英文输入环境")
            
            # 使用新的API方法临时关闭输入法
            original_status = self.disable_ime_temporarily(hwnd)
            if original_status is not None:
                self.logger.info("成功确保英文输入环境")
                return original_status
            else:
                self.logger.error("确保英文输入环境失败")
                return None
                
        except Exception as e:
            self.logger.error(f"确保英文输入环境失败: {e}")
            return None

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