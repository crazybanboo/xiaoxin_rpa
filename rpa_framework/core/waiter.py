"""
RPA框架 - 等待和验证模块
提供完整的等待和验证功能，包括元素等待、图像等待、条件等待等
"""

import time
import pyautogui
from typing import Callable, Optional, Tuple, Any
from .utils import RpaLogger, RpaException
from .locator import ImageLocator

class WaitController:
    """等待控制器类"""
    
    def __init__(self):
        self.logger = RpaLogger.get_logger(__name__)
        self.logger.info("等待控制器初始化完成")
        self.image_locator = ImageLocator()
    
    def wait_for_element(self, locator_func: Callable, timeout: float = 10.0, 
                        check_interval: float = 0.5, *args, **kwargs) -> bool:
        """
        等待元素出现
        
        Args:
            locator_func: 定位函数
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            *args, **kwargs: 传递给定位函数的参数
            
        Returns:
            bool: 是否找到元素
        """
        try:
            self.logger.info(f"等待元素出现，超时时间: {timeout}s, 检查间隔: {check_interval}s")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    result = locator_func(*args, **kwargs)
                    if result:
                        self.logger.info("元素已找到")
                        return True
                except Exception:
                    # 定位失败，继续等待
                    pass
                
                time.sleep(check_interval)
            
            self.logger.warning(f"等待元素超时: {timeout}s")
            return False
            
        except Exception as e:
            self.logger.error(f"等待元素失败: {e}")
            raise RpaException(f"等待元素失败: {e}")
    
    def wait_for_image(self, image_path: str, timeout: float = 10.0, 
                      check_interval: float = 0.5, confidence: float = 0.8,
                      region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        等待图像出现
        
        Args:
            image_path: 图像路径
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            confidence: 匹配置信度
            region: 搜索区域 (x, y, width, height)
            
        Returns:
            Optional[Tuple[int, int]]: 图像中心坐标，未找到返回None
        """
        try:
            self.logger.info(f"等待图像出现: {image_path}, 超时: {timeout}s, 置信度: {confidence}")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                result = self.image_locator.locate_by_template(image_path, confidence, region)
                location = (result[0] + (result[2] - result[0]) // 2, result[1] + (result[3] - result[1]) // 2) if result else None
                if location:
                    self.logger.info(f"图像已找到，位置: {location}")
                    return location
                
                time.sleep(check_interval)
            
            self.logger.warning(f"等待图像超时: {timeout}s")
            return None
            
        except Exception as e:
            self.logger.error(f"等待图像失败: {e}")
            raise RpaException(f"等待图像失败: {e}")
    
    def wait_until(self, condition_func: Callable, timeout: float = 10.0,
                   check_interval: float = 0.5, *args, **kwargs) -> bool:
        """
        等待条件满足
        
        Args:
            condition_func: 条件函数，返回True表示条件满足
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            *args, **kwargs: 传递给条件函数的参数
            
        Returns:
            bool: 条件是否满足
        """
        try:
            self.logger.info(f"等待条件满足，超时时间: {timeout}s")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    if condition_func(*args, **kwargs):
                        self.logger.info("条件已满足")
                        return True
                except Exception as e:
                    self.logger.debug(f"条件检查异常: {e}")
                
                time.sleep(check_interval)
            
            self.logger.warning(f"等待条件超时: {timeout}s")
            return False
            
        except Exception as e:
            self.logger.error(f"等待条件失败: {e}")
            raise RpaException(f"等待条件失败: {e}")
    
    def wait_for_pixel_color(self, x: int, y: int, expected_color: Tuple[int, int, int],
                           timeout: float = 10.0, check_interval: float = 0.5,
                           tolerance: int = 10) -> bool:
        """
        等待指定位置像素颜色变化
        
        Args:
            x: X坐标
            y: Y坐标
            expected_color: 期望的RGB颜色值
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            tolerance: 颜色容差
            
        Returns:
            bool: 颜色是否匹配
        """
        try:
            self.logger.info(f"等待像素颜色变化: ({x}, {y}), 期望颜色: {expected_color}")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                current_color = pyautogui.pixel(x, y)
                
                # 检查颜色是否在容差范围内
                color_match = all(
                    abs(current_color[i] - expected_color[i]) <= tolerance
                    for i in range(3)
                )
                
                if color_match:
                    self.logger.info(f"像素颜色匹配: {current_color}")
                    return True
                
                time.sleep(check_interval)
            
            self.logger.warning(f"等待像素颜色超时: {timeout}s")
            return False
            
        except Exception as e:
            self.logger.error(f"等待像素颜色失败: {e}")
            raise RpaException(f"等待像素颜色失败: {e}")
    
    def wait_for_window_title(self, title: str, timeout: float = 10.0,
                             check_interval: float = 0.5, exact_match: bool = False) -> bool:
        """
        等待窗口标题出现
        
        Args:
            title: 窗口标题
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            exact_match: 是否精确匹配
            
        Returns:
            bool: 是否找到窗口
        """
        try:
            self.logger.info(f"等待窗口标题: '{title}', 精确匹配: {exact_match}")
            
            # 尝试导入Win32API
            try:
                import win32gui
                
                def enum_windows_callback(hwnd, windows):
                    window_title = win32gui.GetWindowText(hwnd)
                    if exact_match:
                        if window_title == title:
                            windows.append(hwnd)
                    else:
                        if title.lower() in window_title.lower():
                            windows.append(hwnd)
                    return True
                
                start_time = time.time()
                while time.time() - start_time < timeout:
                    windows = []
                    win32gui.EnumWindows(enum_windows_callback, windows)
                    
                    if windows:
                        self.logger.info(f"找到窗口: {len(windows)}个")
                        return True
                    
                    time.sleep(check_interval)
                
                self.logger.warning(f"等待窗口标题超时: {timeout}s")
                return False
                
            except ImportError:
                self.logger.warning("Win32API不可用，跳过窗口标题等待")
                return False
            
        except Exception as e:
            self.logger.error(f"等待窗口标题失败: {e}")
            raise RpaException(f"等待窗口标题失败: {e}")
    
    def wait_and_retry(self, action_func: Callable, max_retries: int = 3,
                      retry_interval: float = 1.0, *args, **kwargs) -> Any:
        """
        执行操作并在失败时重试
        
        Args:
            action_func: 要执行的操作函数
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）
            *args, **kwargs: 传递给操作函数的参数
            
        Returns:
            Any: 操作函数的返回值
        """
        try:
            self.logger.info(f"执行操作，最大重试次数: {max_retries}")
            
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    result = action_func(*args, **kwargs)
                    if attempt > 0:
                        self.logger.info(f"操作在第{attempt + 1}次尝试成功")
                    return result
                    
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        self.logger.warning(f"操作失败，第{attempt + 1}次尝试: {e}")
                        time.sleep(retry_interval)
                    else:
                        self.logger.error(f"操作失败，已达到最大重试次数: {e}")
            
            # 如果所有重试都失败，抛出最后一个异常
            if last_exception:
                raise last_exception
            else:
                raise RpaException("操作失败，未知错误")
            
        except Exception as e:
            self.logger.error(f"重试操作失败: {e}")
            raise RpaException(f"重试操作失败: {e}")
    
    def sleep(self, duration: float) -> None:
        """
        休眠指定时间
        
        Args:
            duration: 休眠时间（秒）
        """
        self.logger.info(f"休眠 {duration} 秒")
        time.sleep(duration)
    
    def wait_for_stable_image(self, image_path: str, timeout: float = 10.0,
                             stability_duration: float = 2.0, check_interval: float = 0.5,
                             confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        等待图像稳定出现（连续一段时间都能找到）
        
        Args:
            image_path: 图像路径
            timeout: 总超时时间（秒）
            stability_duration: 稳定持续时间（秒）
            check_interval: 检查间隔（秒）
            confidence: 匹配置信度
            
        Returns:
            Optional[Tuple[int, int]]: 图像中心坐标，未找到返回None
        """
        try:
            self.logger.info(f"等待图像稳定: {image_path}, 稳定时间: {stability_duration}s")
            
            start_time = time.time()
            stable_start = None
            last_location = None
            
            while time.time() - start_time < timeout:
                result = self.image_locator.locate_by_template(image_path, confidence)
                location = (result[0] + (result[2] - result[0]) // 2, result[1] + (result[3] - result[1]) // 2) if result else None
                
                if location:
                    if stable_start is None:
                        # 第一次找到图像
                        stable_start = time.time()
                        last_location = location
                    elif time.time() - stable_start >= stability_duration:
                        # 图像已稳定足够时间
                        self.logger.info(f"图像已稳定，位置: {location}")
                        return location
                else:
                    # 图像消失，重置稳定计时
                    stable_start = None
                    last_location = None
                
                time.sleep(check_interval)
            
            self.logger.warning(f"等待图像稳定超时: {timeout}s")
            return None
            
        except Exception as e:
            self.logger.error(f"等待图像稳定失败: {e}")
            raise RpaException(f"等待图像稳定失败: {e}")

# 创建全局等待控制器实例
waiter = WaitController()

# 便捷函数
def wait_for_image(image_path: str, timeout: float = 10.0, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
    """等待图像出现"""
    return waiter.wait_for_image(image_path, timeout, confidence=confidence)

def wait_until(condition_func: Callable, timeout: float = 10.0, *args, **kwargs) -> bool:
    """等待条件满足"""
    return waiter.wait_until(condition_func, timeout, *args, **kwargs)

def sleep(duration: float) -> None:
    """休眠"""
    waiter.sleep(duration)

def wait_and_retry(action_func: Callable, max_retries: int = 3, *args, **kwargs) -> Any:
    """重试执行操作"""
    return waiter.wait_and_retry(action_func, max_retries, *args, **kwargs) 