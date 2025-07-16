"""
RPA Framework 元素定位模块
提供多种定位策略：坐标定位、图像定位、窗口定位、OCR定位等
"""

import time
import numpy as np
import pyautogui
from typing import Optional, Tuple, List, Union, Dict, Any
from pathlib import Path
from dataclasses import dataclass

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("警告: opencv-python 未安装，图像识别功能将不可用")

try:
    import win32gui
    import win32con
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("警告: pywin32 未安装，Windows API功能将不可用")

try:
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    easyocr = None
    print("警告: easyocr 未安装，OCR功能将不可用")

from .utils import logger, config, RpaException


@dataclass
class WindowInfo:
    """窗口信息数据结构"""
    hwnd: int
    title: str
    class_name: str
    rect: Tuple[int, int, int, int]  # (left, top, right, bottom)
    width: int
    height: int
    center: Tuple[int, int]
    is_visible: bool
    is_maximized: bool


class Locator:
    """元素定位器基类"""
    
    def __init__(self):
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.screenshot_cache_duration = 1.0  # 截图缓存时间（秒）
        
        # OCR延迟初始化
        self._ocr_reader = None
        self._ocr_initialized = False
    
    @property
    def ocr_reader(self):
        """延迟初始化OCR读取器"""
        if not self._ocr_initialized:
            self._ocr_initialized = True
            if OCR_AVAILABLE and easyocr is not None:
                try:
                    self._ocr_reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
                except Exception as e:
                    logger.warning(f"OCR初始化失败: {e}")
                    self._ocr_reader = None
            else:
                self._ocr_reader = None
        return self._ocr_reader
    
    def get_screenshot(self, region: Optional[Tuple[int, int, int, int]] = None, 
                      use_cache: bool = True):
        """
        获取屏幕截图
        
        Args:
            region: 截图区域 (left, top, width, height)
            use_cache: 是否使用缓存
            
        Returns:
            截图的numpy数组或PIL Image
        """
        current_time = time.time()
        
        # 检查是否可以使用缓存
        if (use_cache and self.last_screenshot is not None and 
            current_time - self.last_screenshot_time < self.screenshot_cache_duration and
            region is None):
            return self.last_screenshot
        
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # 如果OpenCV可用，转换为numpy数组
            if CV2_AVAILABLE:
                screenshot_np = np.array(screenshot)
                
                # 缓存全屏截图
                if region is None:
                    self.last_screenshot = screenshot_np
                    self.last_screenshot_time = current_time
                
                return screenshot_np
            else:
                # 缓存PIL图像
                if region is None:
                    self.last_screenshot = screenshot
                    self.last_screenshot_time = current_time
                
                return screenshot
            
        except Exception as e:
            raise RpaException(f"获取截图失败: {e}", "SCREENSHOT_ERROR")


class CoordinateLocator(Locator):
    """坐标定位器"""
    
    def locate_by_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """
        根据绝对坐标定位
        
        Args:
            x: X坐标
            y: Y坐标
            
        Returns:
            坐标元组 (x, y)
        """
        screen_width, screen_height = pyautogui.size()
        
        if not (0 <= x <= screen_width and 0 <= y <= screen_height):
            raise RpaException(f"坐标超出屏幕范围: ({x}, {y})", "COORDINATE_OUT_OF_BOUNDS")
        
        logger.debug(f"坐标定位: ({x}, {y})")
        return (x, y)
    
    def locate_by_relative_coordinates(self, x_ratio: float, y_ratio: float) -> Tuple[int, int]:
        """
        根据相对坐标定位（屏幕百分比）
        
        Args:
            x_ratio: X坐标比例 (0-1)
            y_ratio: Y坐标比例 (0-1)
            
        Returns:
            绝对坐标元组 (x, y)
        """
        if not (0 <= x_ratio <= 1 and 0 <= y_ratio <= 1):
            raise RpaException(f"相对坐标超出范围: ({x_ratio}, {y_ratio})", "RELATIVE_COORDINATE_ERROR")
        
        screen_width, screen_height = pyautogui.size()
        x = int(screen_width * x_ratio)
        y = int(screen_height * y_ratio)
        
        logger.debug(f"相对坐标定位: ({x_ratio}, {y_ratio}) -> ({x}, {y})")
        return (x, y)


class ImageLocator(Locator):
    """图像定位器"""
    
    def __init__(self):
        super().__init__()
        self.template_cache = {}  # 模板缓存
        
        if not CV2_AVAILABLE:
            logger.warning("OpenCV不可用，图像定位功能受限")
    
    def locate_by_template(self, template_path: str, 
                          confidence: Optional[float] = None,
                          region: Optional[Tuple[int, int, int, int]] = None,
                          grayscale: Optional[bool] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        通过模板匹配定位元素
        
        Args:
            template_path: 模板图片路径
            confidence: 匹配置信度，默认使用配置值
            region: 搜索区域 (left, top, width, height)
            grayscale: 是否使用灰度匹配
            
        Returns:
            匹配区域 (left, top, right, bottom) 或 None
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV不可用，无法进行图像匹配")
            return None
            
        if confidence is None:
            confidence = config.get('image.confidence', 0.8)
        if grayscale is None:
            grayscale = config.get('image.grayscale', True)
        
        try:
            # 加载模板图片
            template = self._load_template(template_path, grayscale if grayscale is not None else True)
            if template is None:
                return None
            
            # 获取屏幕截图
            screenshot = self.get_screenshot(region)
            
            # 确保screenshot是numpy数组格式
            if not isinstance(screenshot, np.ndarray):
                screenshot = np.array(screenshot)
            
            # 转换为OpenCV格式
            if grayscale:
                if len(screenshot.shape) == 3:
                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
                if len(template.shape) == 3:
                    template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
            else:
                if len(screenshot.shape) == 3:
                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
                if len(template.shape) == 3:
                    template = cv2.cvtColor(template, cv2.COLOR_RGB2BGR)
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= (confidence if confidence is not None else 0.8):
                # 计算匹配区域
                h, w = template.shape[:2]
                left = max_loc[0]
                top = max_loc[1]
                
                # 如果指定了搜索区域，需要调整坐标
                if region:
                    left += region[0]
                    top += region[1]
                
                right = left + w
                bottom = top + h
                
                logger.debug(f"图像匹配成功: {template_path}, 置信度: {max_val:.3f}, 位置: ({left}, {top}, {right}, {bottom})")
                return (left, top, right, bottom)
            else:
                logger.debug(f"图像匹配失败: {template_path}, 最高置信度: {max_val:.3f} < {confidence}")
                return None
                
        except Exception as e:
            logger.error(f"图像定位失败: {e}")
            return None
    
    def locate_all_by_template(self, template_path: Optional[str] = None, 
                             confidence: Optional[float] = None,
                             region: Optional[Tuple[int, int, int, int]] = None,
                             grayscale: Optional[bool] = None,
                             max_results: int = 30) -> List[Tuple[int, int, int, int, float]]:
        """
        通过模板匹配定位所有匹配的元素
        
        Args:
            template_path: 模板图片路径
            confidence: 匹配置信度，默认使用配置值
            region: 搜索区域 (left, top, width, height)
            grayscale: 是否使用灰度匹配
            max_results: 最大返回结果数量
            
        Returns:
            匹配区域列表 [(left, top, right, bottom, confidence), ...]
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV不可用，无法进行图像匹配")
            return []
            
        if confidence is None:
            confidence = config.get('image.confidence', 0.8)
        if grayscale is None:
            grayscale = config.get('image.grayscale', True)
        
        try:
            # 加载模板图片
            template = self._load_template(template_path, grayscale if grayscale is not None else True)
            if template is None:
                return []
            
            # 获取屏幕截图
            screenshot = self.get_screenshot(region)
            
            # 确保screenshot是numpy数组格式
            if not isinstance(screenshot, np.ndarray):
                screenshot = np.array(screenshot)
            
            # 转换为OpenCV格式
            if grayscale:
                if len(screenshot.shape) == 3:
                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
                if len(template.shape) == 3:
                    template = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
            else:
                if len(screenshot.shape) == 3:
                    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
                if len(template.shape) == 3:
                    template = cv2.cvtColor(template, cv2.COLOR_RGB2BGR)
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            h, w = template.shape[:2]
            
            # 找到所有匹配的位置
            locations = np.where(result >= (confidence if confidence is not None else 0.8))
            matches = []
            
            # 将匹配位置转换为矩形区域
            for pt in zip(*locations[::-1]):  # 交换x和y坐标
                left = pt[0]
                top = pt[1]
                
                # 如果指定了搜索区域，需要调整坐标
                if region:
                    left += region[0]
                    top += region[1]
                
                right = left + w
                bottom = top + h
                confidence_score = result[pt[1], pt[0]]
                
                matches.append((left, top, right, bottom, confidence_score))
            
            # 去重：移除重叠的匹配
            filtered_matches = self._filter_overlapping_matches(matches, overlap_threshold=0.5)
            
            # 按置信度排序
            filtered_matches.sort(key=lambda x: x[4], reverse=True)
            
            # 限制结果数量
            filtered_matches = filtered_matches[:max_results]
            
            # 返回坐标列表（包含置信度）
            result_list = [(match[0], match[1], match[2], match[3], match[4]) for match in filtered_matches]
            
            logger.debug(f"图像匹配找到 {len(result_list)} 个结果: {template_path}")
            return result_list
                
        except Exception as e:
            logger.error(f"批量图像定位失败: {e}")
            return []

    def _filter_overlapping_matches(self, matches: List[Tuple[int, int, int, int, float]], 
                                  overlap_threshold: float = 0.5) -> List[Tuple[int, int, int, int, float]]:
        """
        过滤重叠的匹配结果
        
        Args:
            matches: 匹配结果列表 [(left, top, right, bottom, confidence), ...]
            overlap_threshold: 重叠阈值
            
        Returns:
            过滤后的匹配结果列表
        """
        if not matches:
            return []
        
        # 按置信度排序
        matches.sort(key=lambda x: x[4], reverse=True)
        
        filtered = []
        for current_match in matches:
            is_overlapping = False
            current_rect = current_match[:4]
            
            for existing_match in filtered:
                existing_rect = existing_match[:4]
                
                # 计算重叠面积
                overlap_area = self._calculate_overlap_area(current_rect, existing_rect)
                current_area = (current_rect[2] - current_rect[0]) * (current_rect[3] - current_rect[1])
                
                # 如果重叠面积超过阈值，则认为是重叠的
                if overlap_area / current_area > overlap_threshold:
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered.append(current_match)
        
        return filtered

    def _calculate_overlap_area(self, rect1: Tuple[int, int, int, int], 
                              rect2: Tuple[int, int, int, int]) -> float:
        """
        计算两个矩形的重叠面积
        
        Args:
            rect1: 矩形1 (left, top, right, bottom)
            rect2: 矩形2 (left, top, right, bottom)
            
        Returns:
            重叠面积
        """
        left1, top1, right1, bottom1 = rect1
        left2, top2, right2, bottom2 = rect2
        
        # 计算重叠区域
        overlap_left = max(left1, left2)
        overlap_top = max(top1, top2)
        overlap_right = min(right1, right2)
        overlap_bottom = min(bottom1, bottom2)
        
        # 如果没有重叠，返回0
        if overlap_left >= overlap_right or overlap_top >= overlap_bottom:
            return 0.0
        
        # 计算重叠面积
        overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
        return overlap_area

    def _load_template(self, template_path: Optional[str] = None, grayscale: bool = True):
        """
        加载模板图片
        
        Args:
            template_path: 模板路径
            grayscale: 是否转为灰度
            
        Returns:
            模板图片的numpy数组
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV不可用，无法加载模板")
            return None
            
        cache_key = f"{template_path}_{grayscale}"
        
        # 检查缓存
        if cache_key in self.template_cache:
            return self.template_cache[cache_key]
        if template_path is None:
            return None

        try:
            # 检查文件是否存在
            if not Path(template_path).exists():
                # 尝试在templates目录中查找
                template_dir = Path(config.get('general.template_dir', 'templates'))
                full_path = template_dir / template_path
                if full_path.exists():
                    template_path = str(full_path)
                else:
                    logger.error(f"模板文件不存在: {template_path}")
                    return None
            
            # 加载图片
            if grayscale:
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            else:
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            
            if template is None:
                logger.error(f"无法加载模板图片: {template_path}")
                return None
            
            # 缓存模板
            self.template_cache[cache_key] = template
            
            return template
            
        except Exception as e:
            logger.error(f"加载模板失败: {e}")
            return None


class WindowLocator(Locator):
    """窗口定位器（Windows专用）"""
    
    def __init__(self):
        super().__init__()
        if not WIN32_AVAILABLE:
            logger.warning("Win32API不可用，窗口定位功能受限")
    
    def find_window_by_title(self, title: str, exact_match: bool = False) -> Optional[int]:
        """
        根据窗口标题查找窗口句柄
        
        Args:
            title: 窗口标题
            exact_match: 是否精确匹配
            
        Returns:
            窗口句柄或None
        """
        if not WIN32_AVAILABLE:
            logger.error("Win32API不可用")
            return None
        
        def enum_windows_proc(hwnd, lParam):
            window_title = win32gui.GetWindowText(hwnd)
            if exact_match:
                if window_title == title:
                    lParam.append(hwnd)
            else:
                if title.lower() in window_title.lower():
                    lParam.append(hwnd)
            return True
        
        windows = []
        try:
            win32gui.EnumWindows(enum_windows_proc, windows)
            return windows[0] if windows else None
        except Exception as e:
            logger.error(f"查找窗口失败: {e}")
            return None
    
    def find_window_by_class(self, class_name: str) -> Optional[int]:
        """
        根据窗口类名查找窗口
        
        Args:
            class_name: 窗口类名
            
        Returns:
            窗口句柄或None
        """
        if not WIN32_AVAILABLE:
            logger.error("Win32API不可用")
            return None
        
        try:
            hwnd = win32gui.FindWindow(class_name, None)
            return hwnd if hwnd else None
        except Exception as e:
            logger.error(f"根据类名查找窗口失败: {e}")
            return None
    
    def get_window_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        """
        获取窗口矩形区域
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            窗口区域 (left, top, right, bottom)
        """
        if not WIN32_AVAILABLE:
            return None
        
        try:
            rect = win32gui.GetWindowRect(hwnd)
            return rect
        except Exception as e:
            logger.error(f"获取窗口区域失败: {e}")
            return None
    
    def activate_window(self, hwnd: int) -> bool:
        """
        激活窗口
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            是否成功
        """
        if not WIN32_AVAILABLE:
            return False
        
        try:
            # 显示窗口
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # 设置为前台窗口
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.1)  # 等待窗口激活
            return True
        except Exception as e:
            logger.error(f"激活窗口失败: {e}")
            return False
    
    def get_window_info(self, hwnd: Optional[int] = None) -> Optional[WindowInfo]:
        """
        获取窗口详细信息
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            WindowInfo对象或None
        """
        if hwnd is None:
            return None
        if not WIN32_AVAILABLE:
            return None
        
        try:
            # 获取窗口标题
            title = win32gui.GetWindowText(hwnd)
            
            # 获取窗口类名
            class_name = win32gui.GetClassName(hwnd)
            
            # 获取窗口矩形区域
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            
            # 计算宽度、高度和中心点
            width = right - left
            height = bottom - top
            center = (left + width // 2, top + height // 2)
            
            # 检查窗口是否可见
            is_visible = bool(win32gui.IsWindowVisible(hwnd))
            
            # 检查窗口是否最大化
            placement = win32gui.GetWindowPlacement(hwnd)
            is_maximized = placement[1] == win32con.SW_SHOWMAXIMIZED
            
            window_info = WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                rect=rect,
                width=width,
                height=height,
                center=center,
                is_visible=is_visible,
                is_maximized=is_maximized
            )
            
            logger.debug(f"获取窗口信息: {title} ({width}x{height})")
            return window_info
            
        except Exception as e:
            logger.error(f"获取窗口信息失败: {e}")
            return None
    
    def get_window_size(self, hwnd: int) -> Optional[Tuple[int, int]]:
        """
        获取窗口大小
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            窗口大小 (width, height) 或 None
        """
        window_info = self.get_window_info(hwnd)
        if window_info:
            return (window_info.width, window_info.height)
        return None
    
    def get_window_position(self, hwnd: int) -> Optional[Tuple[int, int]]:
        """
        获取窗口位置
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            窗口位置 (left, top) 或 None
        """
        window_info = self.get_window_info(hwnd)
        if window_info:
            return (window_info.rect[0], window_info.rect[1])
        return None
    
    def get_window_center(self, hwnd: int) -> Optional[Tuple[int, int]]:
        """
        获取窗口中心点坐标
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            窗口中心点 (x, y) 或 None
        """
        window_info = self.get_window_info(hwnd)
        if window_info:
            return window_info.center
        return None
    
    def convert_to_relative_coords(self, x: int, y: int, hwnd: int) -> Optional[Tuple[float, float]]:
        """
        将绝对坐标转换为窗口相对坐标
        
        Args:
            x: 绝对X坐标
            y: 绝对Y坐标
            hwnd: 窗口句柄
            
        Returns:
            相对坐标 (x_ratio, y_ratio) 或 None，范围为0-1
        """
        window_info = self.get_window_info(hwnd)
        if not window_info:
            return None
        
        # 计算相对坐标
        relative_x = (x - window_info.rect[0]) / window_info.width
        relative_y = (y - window_info.rect[1]) / window_info.height
        
        # 确保坐标在有效范围内
        relative_x = max(0.0, min(1.0, relative_x))
        relative_y = max(0.0, min(1.0, relative_y))
        
        return (relative_x, relative_y)
    
    def convert_from_relative_coords(self, x_ratio: float, y_ratio: float, hwnd: int) -> Optional[Tuple[int, int]]:
        """
        将窗口相对坐标转换为绝对坐标
        
        Args:
            x_ratio: 相对X坐标 (0-1)
            y_ratio: 相对Y坐标 (0-1)
            hwnd: 窗口句柄
            
        Returns:
            绝对坐标 (x, y) 或 None
        """
        window_info = self.get_window_info(hwnd)
        if not window_info:
            return None
        
        # 计算绝对坐标
        x = int(window_info.rect[0] + x_ratio * window_info.width)
        y = int(window_info.rect[1] + y_ratio * window_info.height)
        
        return (x, y)
    
    def is_window_state(self, hwnd: int, state: str) -> bool:
        """
        检查窗口状态
        
        Args:
            hwnd: 窗口句柄
            state: 状态类型 ('visible', 'maximized', 'minimized')
            
        Returns:
            是否为指定状态
        """
        if not WIN32_AVAILABLE:
            return False
        
        try:
            if state == 'visible':
                return bool(win32gui.IsWindowVisible(hwnd))
            elif state == 'maximized':
                placement = win32gui.GetWindowPlacement(hwnd)
                return placement[1] == win32con.SW_SHOWMAXIMIZED
            elif state == 'minimized':
                placement = win32gui.GetWindowPlacement(hwnd)
                return placement[1] == win32con.SW_SHOWMINIMIZED
            else:
                logger.warning(f"未知的窗口状态: {state}")
                return False
        except Exception as e:
            logger.error(f"检查窗口状态失败: {e}")
            return False
    
    def set_window_size(self, hwnd: int, width: int, height: int) -> bool:
        """
        设置窗口大小
        
        Args:
            hwnd: 窗口句柄
            width: 窗口宽度
            height: 窗口高度
            
        Returns:
            是否设置成功
        """
        if not WIN32_AVAILABLE:
            logger.error("Windows API不可用，无法设置窗口大小")
            return False
        
        try:
            # 获取当前窗口位置和大小
            rect = win32gui.GetWindowRect(hwnd)
            current_x, current_y = rect[0], rect[1]
            old_width = rect[2] - rect[0]
            old_height = rect[3] - rect[1]
            
            # 设置窗口大小和位置
            win32gui.SetWindowPos(
                hwnd,
                0,  # hWndInsertAfter
                current_x,  # X
                current_y,  # Y
                width,  # cx
                height,  # cy
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )
            
            # 等待窗口调整完成
            time.sleep(0.1)
            
            # 获取调整后的窗口信息来验证是否成功
            new_rect = win32gui.GetWindowRect(hwnd)
            new_width = new_rect[2] - new_rect[0]
            new_height = new_rect[3] - new_rect[1]
            
            # 检查窗口大小是否被成功调整（允许小范围误差）
            width_diff = abs(new_width - width)
            height_diff = abs(new_height - height)
            
            # 允许5像素的误差范围
            tolerance = 5
            
            if width_diff <= tolerance and height_diff <= tolerance:
                logger.info(f"窗口大小设置成功: {new_width}x{new_height}")
                return True
            else:
                logger.warning(f"窗口大小调整可能不完全精确: 目标({width}x{height}), 实际({new_width}x{new_height})")
                # 即使不完全精确，只要有明显变化就认为成功
                if (abs(new_width - old_width) > tolerance or abs(new_height - old_height) > tolerance):
                    logger.info("窗口大小已发生变化，认为调整成功")
                    return True
                else:
                    logger.error("窗口大小未发生变化，调整失败")
                    return False
                
        except Exception as e:
            logger.error(f"设置窗口大小失败: {e}")
            return False
    
    def set_window_position(self, hwnd: int, x: int, y: int) -> bool:
        """
        设置窗口位置
        
        Args:
            hwnd: 窗口句柄
            x: 窗口X坐标
            y: 窗口Y坐标
            
        Returns:
            是否设置成功
        """
        if not WIN32_AVAILABLE:
            logger.error("Windows API不可用，无法设置窗口位置")
            return False
        
        try:
            # 获取当前窗口大小和位置
            rect = win32gui.GetWindowRect(hwnd)
            current_width = rect[2] - rect[0]
            current_height = rect[3] - rect[1]
            old_x = rect[0]
            old_y = rect[1]
            
            # 设置窗口位置
            win32gui.SetWindowPos(
                hwnd,
                0,  # hWndInsertAfter
                x,  # X
                y,  # Y
                current_width,  # cx
                current_height,  # cy
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )
            
            # 等待窗口调整完成
            time.sleep(0.1)
            
            # 获取调整后的窗口信息来验证是否成功
            new_rect = win32gui.GetWindowRect(hwnd)
            new_x = new_rect[0]
            new_y = new_rect[1]
            
            # 检查窗口位置是否被成功调整（允许小范围误差）
            x_diff = abs(new_x - x)
            y_diff = abs(new_y - y)
            
            # 允许5像素的误差范围
            tolerance = 5
            
            if x_diff <= tolerance and y_diff <= tolerance:
                logger.info(f"窗口位置设置成功: ({new_x}, {new_y})")
                return True
            else:
                logger.warning(f"窗口位置调整可能不完全精确: 目标({x}, {y}), 实际({new_x}, {new_y})")
                # 即使不完全精确，只要有明显变化就认为成功
                if (abs(new_x - old_x) > tolerance or abs(new_y - old_y) > tolerance):
                    logger.info("窗口位置已发生变化，认为调整成功")
                    return True
                else:
                    logger.error("窗口位置未发生变化，调整失败")
                    return False
                
        except Exception as e:
            logger.error(f"设置窗口位置失败: {e}")
            return False
    
    def set_window_size_and_position(self, hwnd: int, x: int, y: int, width: int, height: int) -> bool:
        """
        同时设置窗口大小和位置
        
        Args:
            hwnd: 窗口句柄
            x: 窗口X坐标
            y: 窗口Y坐标
            width: 窗口宽度
            height: 窗口高度
            
        Returns:
            是否设置成功
        """
        if not WIN32_AVAILABLE:
            logger.error("Windows API不可用，无法设置窗口大小和位置")
            return False
        
        try:
            # 获取调整前的窗口信息
            old_rect = win32gui.GetWindowRect(hwnd)
            old_width = old_rect[2] - old_rect[0]
            old_height = old_rect[3] - old_rect[1]
            
            # 同时设置窗口大小和位置
            win32gui.SetWindowPos(
                hwnd,
                0,  # hWndInsertAfter
                x,  # X
                y,  # Y
                width,  # cx
                height,  # cy
                win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE
            )
            
            # 等待窗口调整完成
            time.sleep(0.1)
            
            # 获取调整后的窗口信息来验证是否成功
            new_rect = win32gui.GetWindowRect(hwnd)
            new_width = new_rect[2] - new_rect[0]
            new_height = new_rect[3] - new_rect[1]
            new_x = new_rect[0]
            new_y = new_rect[1]
            
            # 检查窗口是否被成功调整（允许小范围误差）
            width_diff = abs(new_width - width)
            height_diff = abs(new_height - height)
            x_diff = abs(new_x - x)
            y_diff = abs(new_y - y)
            
            # 允许5像素的误差范围
            tolerance = 5
            
            if (width_diff <= tolerance and height_diff <= tolerance and 
                x_diff <= tolerance and y_diff <= tolerance):
                logger.info(f"窗口大小和位置设置成功: {new_width}x{new_height} at ({new_x}, {new_y})")
                return True
            else:
                logger.warning(f"窗口调整可能不完全精确: 目标({width}x{height} at ({x}, {y})), 实际({new_width}x{new_height} at ({new_x}, {new_y}))")
                # 即使不完全精确，只要有明显变化就认为成功
                if (abs(new_width - old_width) > tolerance or abs(new_height - old_height) > tolerance):
                    logger.info("窗口大小已发生变化，认为调整成功")
                    return True
                else:
                    logger.error("窗口大小和位置未发生变化，调整失败")
                    return False
                
        except Exception as e:
            logger.error(f"设置窗口大小和位置失败: {e}")
            return False


class OCRLocator(Locator):
    """OCR文字定位器"""
    
    def locate_by_text(self, text: str, 
                      region: Optional[Tuple[int, int, int, int]] = None,
                      exact_match: bool = False) -> List[Tuple[int, int, int, int]]:
        """
        通过OCR识别文字定位
        
        Args:
            text: 要查找的文字
            region: 搜索区域
            exact_match: 是否精确匹配
            
        Returns:
            匹配的文字区域列表
        """
        if not OCR_AVAILABLE or self.ocr_reader is None:
            logger.error("OCR功能不可用")
            return []
        
        try:
            # 获取截图
            screenshot = self.get_screenshot(region)
            
            # OCR识别
            results = self.ocr_reader.readtext(screenshot)
            
            matches = []
            for (bbox, detected_text, confidence) in results:
                if confidence < 0.5:  # 置信度过低，跳过
                    continue
                
                # 文字匹配
                if exact_match:
                    if detected_text.strip() == text.strip():
                        matches.append(self._bbox_to_rect(bbox, region))
                else:
                    if text.lower() in detected_text.lower():
                        matches.append(self._bbox_to_rect(bbox, region))
            
            logger.debug(f"OCR文字定位: '{text}' 找到 {len(matches)} 个匹配")
            return matches
            
        except Exception as e:
            logger.error(f"OCR定位失败: {e}")
            return []
    
    def _bbox_to_rect(self, bbox: List[List[int]], 
                     region: Optional[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
        """
        将OCR边界框转换为矩形区域
        
        Args:
            bbox: OCR边界框
            region: 搜索区域偏移
            
        Returns:
            矩形区域 (left, top, right, bottom)
        """
        # 获取边界框的最小和最大坐标
        xs = [point[0] for point in bbox]
        ys = [point[1] for point in bbox]
        
        left = min(xs)
        top = min(ys)
        right = max(xs)
        bottom = max(ys)
        
        # 如果有搜索区域偏移，需要调整坐标
        if region:
            left += region[0]
            top += region[1]
            right += region[0]
            bottom += region[1]
        
        return (left, top, right, bottom)


class CompositeLocator:
    """组合定位器 - 整合多种定位策略"""
    
    def __init__(self):
        self.coordinate_locator = CoordinateLocator()
        self.image_locator = ImageLocator()
        self.window_locator = WindowLocator()
        self.ocr_locator = OCRLocator()
    
    def locate_element(self, locator_config: Dict[str, Any]) -> Optional[Tuple[int, int, int, int]]:
        """
        根据配置定位元素
        
        Args:
            locator_config: 定位配置字典
            
        Returns:
            元素区域或None
        """
        locator_type = locator_config.get('type')
        
        if locator_type == 'coordinates':
            x = locator_config.get('x')
            y = locator_config.get('y')
            if x is not None and y is not None:
                pos = self.coordinate_locator.locate_by_coordinates(x, y)
                return (pos[0], pos[1], pos[0] + 1, pos[1] + 1)  # 返回1x1区域
        
        elif locator_type == 'image':
            template_path = locator_config.get('template')
            confidence = locator_config.get('confidence')
            region = locator_config.get('region')
            if template_path:
                return self.image_locator.locate_by_template(template_path, confidence, region)
        
        elif locator_type == 'text':
            text = locator_config.get('text')
            region = locator_config.get('region')
            exact_match = locator_config.get('exact_match', False)
            if text:
                results = self.ocr_locator.locate_by_text(text, region, exact_match)
                return results[0] if results else None
        
        elif locator_type == 'window':
            title = locator_config.get('title')
            class_name = locator_config.get('class')
            if title:
                hwnd = self.window_locator.find_window_by_title(title)
                if hwnd:
                    return self.window_locator.get_window_rect(hwnd)
            elif class_name:
                hwnd = self.window_locator.find_window_by_class(class_name)
                if hwnd:
                    return self.window_locator.get_window_rect(hwnd)
        
        return None

    def locate_all_by_template(self, template_path: Optional[str] = None, 
                             confidence: Optional[float] = None,
                             region: Optional[Tuple[int, int, int, int]] = None,
                             grayscale: Optional[bool] = None,
                             max_results: int = 10) -> List[Tuple[int, int, int, int, float]]:
        """
        通过模板匹配定位所有匹配的元素
        
        Args:
            template_path: 模板图片路径
            confidence: 匹配置信度
            region: 搜索区域
            grayscale: 是否使用灰度匹配
            max_results: 最大返回结果数量
            
        Returns:
            匹配区域列表 [(left, top, right, bottom, confidence), ...]
        """
        return self.image_locator.locate_all_by_template(
            template_path, confidence, region, grayscale, max_results
        )


# 全局定位器实例
locator = CompositeLocator()


if __name__ == "__main__":
    # 测试代码
    logger.info("元素定位模块测试")
    
    # 测试坐标定位
    coord_locator = CoordinateLocator()
    pos = coord_locator.locate_by_coordinates(100, 100)
    logger.info(f"坐标定位测试: {pos}")
    
    # 测试相对坐标
    rel_pos = coord_locator.locate_by_relative_coordinates(0.5, 0.5)
    logger.info(f"相对坐标定位测试: {rel_pos}")
    
    logger.info("定位模块初始化完成") 