"""
RPA Framework 元素定位模块
提供多种定位策略：坐标定位、图像定位、窗口定位、OCR定位等
"""

import time
import numpy as np
import pyautogui
from typing import Optional, Tuple, List, Union, Dict, Any
from pathlib import Path

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
    print("警告: easyocr 未安装，OCR功能将不可用")

from .utils import logger, config, RpaException


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
            if OCR_AVAILABLE:
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
    
    def _load_template(self, template_path: str, grayscale: bool = True):
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