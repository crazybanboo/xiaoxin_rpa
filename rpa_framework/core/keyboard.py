"""
RPA框架 - 键盘操作模块
提供完整的键盘操作功能，包括文本输入、快捷键、特殊按键等操作
"""

import time
import pyautogui
from typing import List, Union, Optional
from .utils import RpaLogger, RpaException

# 配置PyAutoGUI
pyautogui.FAILSAFE = True  # 启用故障安全
pyautogui.PAUSE = 0.1     # 操作间隔

class KeyboardController:
    """键盘控制器类"""
    
    def __init__(self):
        self.logger = RpaLogger.get_logger(__name__)
        self.logger.info("键盘控制器初始化完成")
        
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

# 创建全局键盘控制器实例
keyboard = KeyboardController()

# 便捷函数
def type_text(text: str, interval: float = 0.01) -> bool:
    """输入文本"""
    return keyboard.type_text(text, interval)

def press_key(key: str, presses: int = 1) -> bool:
    """按键"""
    return keyboard.press_key(key, presses)

def hotkey(*keys) -> bool:
    """快捷键"""
    return keyboard.hotkey(*keys)

def copy() -> bool:
    """复制"""
    return keyboard.copy()

def paste() -> bool:
    """粘贴"""
    return keyboard.paste()

def select_all() -> bool:
    """全选"""
    return keyboard.select_all()

def clear_text(method: str = 'ctrl_a') -> bool:
    """清除文本"""
    return keyboard.clear_text(method) 