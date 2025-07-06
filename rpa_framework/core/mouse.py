"""
RPA框架 - 鼠标操作模块
提供完整的鼠标操作功能，包括移动、点击、拖拽、滚轮等操作
"""

import time
import pyautogui
from typing import Tuple, Optional, Union
from .utils import RpaLogger, RpaException

# 配置PyAutoGUI
pyautogui.FAILSAFE = True  # 启用故障安全
pyautogui.PAUSE = 0.1     # 操作间隔

# 添加 Windows API 支持
try:
    import win32api
    import win32con
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

class MouseController:
    """鼠标控制器类"""
    
    def __init__(self):
        self.logger = RpaLogger.get_logger(__name__)
        self.logger.info("鼠标控制器初始化完成")
        # 禁用 pyautogui 的安全检查
        pyautogui.FAILSAFE = False
    
    def get_position(self) -> Tuple[int, int]:
        """获取当前鼠标位置"""
        try:
            pos = pyautogui.position()
            self.logger.debug(f"获取鼠标位置: {pos}")
            return int(pos.x), int(pos.y)
        except Exception as e:
            self.logger.error(f"获取鼠标位置失败: {e}")
            raise RpaException(f"获取鼠标位置失败: {e}")
    
    def move_to(self, x: int, y: int, duration: float = 0.5) -> bool:
        """
        移动鼠标到指定位置
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            duration: 移动持续时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"移动鼠标到位置: ({x}, {y}), 持续时间: {duration}s")
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            self.logger.error(f"鼠标移动失败: {e}")
            raise RpaException(f"鼠标移动失败: {e}")
    
    def move_relative(self, dx: int, dy: int, duration: float = 0.5) -> bool:
        """
        相对移动鼠标
        
        Args:
            dx: X轴相对移动距离
            dy: Y轴相对移动距离
            duration: 移动持续时间（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"相对移动鼠标: dx={dx}, dy={dy}, 持续时间: {duration}s")
            pyautogui.move(dx, dy, duration=duration)
            return True
        except Exception as e:
            self.logger.error(f"鼠标相对移动失败: {e}")
            raise RpaException(f"鼠标相对移动失败: {e}")
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              button: str = 'left', clicks: int = 1, interval: float = 0.1) -> bool:
        """
        鼠标点击操作
        
        Args:
            x: 点击X坐标（None表示当前位置）
            y: 点击Y坐标（None表示当前位置）
            button: 鼠标按键（'left', 'right', 'middle'）
            clicks: 点击次数
            interval: 多次点击间隔（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if x is not None and y is not None:
                self.logger.info(f"点击位置: ({x}, {y}), 按键: {button}, 次数: {clicks}")
                pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
            else:
                current_pos = self.get_position()
                self.logger.info(f"在当前位置点击: {current_pos}, 按键: {button}, 次数: {clicks}")
                pyautogui.click(clicks=clicks, interval=interval, button=button)
            return True
        except Exception as e:
            self.logger.error(f"鼠标点击失败: {e}")
            raise RpaException(f"鼠标点击失败: {e}")
    
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        双击操作
        
        Args:
            x: 点击X坐标（None表示当前位置）
            y: 点击Y坐标（None表示当前位置）
            
        Returns:
            bool: 操作是否成功
        """
        return self.click(x, y, clicks=2, interval=0.1)
    
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        右键点击操作
        
        Args:
            x: 点击X坐标（None表示当前位置）
            y: 点击Y坐标（None表示当前位置）
            
        Returns:
            bool: 操作是否成功
        """
        return self.click(x, y, button='right')
    
    def middle_click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        中键点击操作
        
        Args:
            x: 点击X坐标（None表示当前位置）
            y: 点击Y坐标（None表示当前位置）
            
        Returns:
            bool: 操作是否成功
        """
        return self.click(x, y, button='middle')
    
    def drag_to(self, start_x: int, start_y: int, end_x: int, end_y: int, 
                duration: float = 1.0, button: str = 'left') -> bool:
        """
        拖拽操作
        
        Args:
            start_x: 起始X坐标
            start_y: 起始Y坐标
            end_x: 结束X坐标
            end_y: 结束Y坐标
            duration: 拖拽持续时间（秒）
            button: 拖拽使用的鼠标按键
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"拖拽操作: 从({start_x}, {start_y})到({end_x}, {end_y}), 持续时间: {duration}s")
            pyautogui.dragTo(end_x, end_y, duration=duration, button=button)
            return True
        except Exception as e:
            self.logger.error(f"拖拽操作失败: {e}")
            raise RpaException(f"拖拽操作失败: {e}")
    
    def drag_relative(self, dx: int, dy: int, duration: float = 1.0, button: str = 'left') -> bool:
        """
        相对拖拽操作
        
        Args:
            dx: X轴相对拖拽距离
            dy: Y轴相对拖拽距离
            duration: 拖拽持续时间（秒）
            button: 拖拽使用的鼠标按键
            
        Returns:
            bool: 操作是否成功
        """
        try:
            self.logger.info(f"相对拖拽: dx={dx}, dy={dy}, 持续时间: {duration}s")
            pyautogui.drag(dx, dy, duration=duration, button=button)
            return True
        except Exception as e:
            self.logger.error(f"相对拖拽失败: {e}")
            raise RpaException(f"相对拖拽失败: {e}")
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        滚轮操作
        
        Args:
            clicks: 滚动次数（正数向上，负数向下）
            x: 滚动位置X坐标（None表示当前位置）
            y: 滚动位置Y坐标（None表示当前位置）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if x is not None and y is not None:
                self.logger.info(f"在位置({x}, {y})滚动: {clicks}次")
                pyautogui.scroll(clicks, x=x, y=y)
            else:
                current_pos = self.get_position()
                self.logger.info(f"在当前位置{current_pos}滚动: {clicks}次")
                pyautogui.scroll(clicks)
            return True
        except Exception as e:
            self.logger.error(f"滚轮操作失败: {e}")
            raise RpaException(f"滚轮操作失败: {e}")
    
    def scroll_advanced(self, pixels: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        高级滚动操作（使用 Windows API，支持像素级滚动）
        
        Args:
            pixels: 滚动像素数（正数向上，负数向下）
            x: 滚动位置X坐标（None表示当前位置）
            y: 滚动位置Y坐标（None表示当前位置）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if not HAS_WIN32:
                self.logger.warning("Windows API 不可用，使用标准滚动方法")
                # 将像素转换为滚动次数（大概估算）
                clicks = pixels // 120  # 通常每次滚动约120像素
                return self.scroll(clicks, x, y)
            
            # 获取滚动位置
            if x is None or y is None:
                current_pos = self.get_position()
                scroll_x = x if x is not None else current_pos[0]
                scroll_y = y if y is not None else current_pos[1]
            else:
                scroll_x, scroll_y = x, y
            
            self.logger.info(f"高级滚动: 在位置({scroll_x}, {scroll_y})滚动{pixels}像素")
            
            # 获取窗口句柄
            hwnd = win32gui.WindowFromPoint((scroll_x, scroll_y))
            
            # 计算滚动量（Windows API 使用的是 120 的倍数）
            delta = pixels * 120 // 120
            
            # 发送滚动消息
            win32gui.SendMessage(hwnd, win32con.WM_MOUSEWHEEL, delta << 16, (scroll_y << 16) | scroll_x)
            
            return True
        except Exception as e:
            self.logger.error(f"高级滚动失败: {e}")
            # 回退到标准滚动方法
            clicks = pixels // 120
            return self.scroll(clicks, x, y)
    
    def scroll_smooth(self, total_pixels: int, steps: int = 10, delay: float = 0.05, 
                     x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """
        平滑滚动操作
        
        Args:
            total_pixels: 总滚动像素数
            steps: 分解为多少步
            delay: 每步之间的延迟（秒）
            x: 滚动位置X坐标
            y: 滚动位置Y坐标
            
        Returns:
            bool: 操作是否成功
        """
        try:
            pixels_per_step = total_pixels // steps
            remainder = total_pixels % steps
            
            self.logger.info(f"平滑滚动: 总共{total_pixels}像素，分{steps}步，每步{pixels_per_step}像素")
            
            for i in range(steps):
                # 最后一步加上余数
                current_pixels = pixels_per_step + (remainder if i == steps - 1 else 0)
                
                if HAS_WIN32:
                    self.scroll_advanced(current_pixels, x, y)
                else:
                    # 使用标准滚动方法
                    clicks = current_pixels // 120
                    if clicks != 0:
                        self.scroll(clicks, x, y)
                
                if i < steps - 1:  # 最后一步不需要延迟
                    time.sleep(delay)
            
            return True
        except Exception as e:
            self.logger.error(f"平滑滚动失败: {e}")
            raise RpaException(f"平滑滚动失败: {e}")
    
    def mouse_down(self, x: Optional[int] = None, y: Optional[int] = None, button: str = 'left') -> bool:
        """
        按下鼠标按键
        
        Args:
            x: 按下位置X坐标（None表示当前位置）
            y: 按下位置Y坐标（None表示当前位置）
            button: 鼠标按键（'left', 'right', 'middle'）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if x is not None and y is not None:
                self.logger.info(f"在位置({x}, {y})按下{button}键")
                pyautogui.mouseDown(x, y, button=button)
            else:
                current_pos = self.get_position()
                self.logger.info(f"在当前位置{current_pos}按下{button}键")
                pyautogui.mouseDown(button=button)
            return True
        except Exception as e:
            self.logger.error(f"按下鼠标按键失败: {e}")
            raise RpaException(f"按下鼠标按键失败: {e}")
    
    def mouse_up(self, x: Optional[int] = None, y: Optional[int] = None, button: str = 'left') -> bool:
        """
        释放鼠标按键
        
        Args:
            x: 释放位置X坐标（None表示当前位置）
            y: 释放位置Y坐标（None表示当前位置）
            button: 鼠标按键（'left', 'right', 'middle'）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            if x is not None and y is not None:
                self.logger.info(f"在位置({x}, {y})释放{button}键")
                pyautogui.mouseUp(x, y, button=button)
            else:
                current_pos = self.get_position()
                self.logger.info(f"在当前位置{current_pos}释放{button}键")
                pyautogui.mouseUp(button=button)
            return True
        except Exception as e:
            self.logger.error(f"释放鼠标按键失败: {e}")
            raise RpaException(f"释放鼠标按键失败: {e}")
    
    def is_mouse_over(self, x: int, y: int, tolerance: int = 5) -> bool:
        """
        检查鼠标是否在指定位置附近
        
        Args:
            x: 目标X坐标
            y: 目标Y坐标
            tolerance: 容差范围（像素）
            
        Returns:
            bool: 是否在指定位置附近
        """
        try:
            current_x, current_y = self.get_position()
            is_over = (abs(current_x - x) <= tolerance and abs(current_y - y) <= tolerance)
            self.logger.debug(f"检查鼠标位置: 当前({current_x}, {current_y}), 目标({x}, {y}), 容差{tolerance}, 结果: {is_over}")
            return is_over
        except Exception as e:
            self.logger.error(f"检查鼠标位置失败: {e}")
            return False

# 全局鼠标控制器实例（延迟创建）
_global_mouse = None

def _get_global_mouse():
    """获取全局鼠标控制器实例（延迟创建）"""
    global _global_mouse
    if _global_mouse is None:
        _global_mouse = MouseController()
    return _global_mouse

# 便捷函数
def move_to(x: int, y: int, duration: float = 0.5) -> bool:
    """移动鼠标到指定位置"""
    return _get_global_mouse().move_to(x, y, duration)

def click(x: Optional[int] = None, y: Optional[int] = None, button: str = 'left') -> bool:
    """鼠标点击"""
    return _get_global_mouse().click(x, y, button=button)

def double_click(x: Optional[int] = None, y: Optional[int] = None) -> bool:
    """双击"""
    return _get_global_mouse().double_click(x, y)

def right_click(x: Optional[int] = None, y: Optional[int] = None) -> bool:
    """右键点击"""
    return _get_global_mouse().right_click(x, y)

def drag_to(start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0) -> bool:
    """拖拽操作"""
    return _get_global_mouse().drag_to(start_x, start_y, end_x, end_y, duration)

def scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> bool:
    """滚轮操作"""
    return _get_global_mouse().scroll(clicks, x, y) 