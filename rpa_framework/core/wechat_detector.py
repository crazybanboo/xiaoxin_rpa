"""
企业微信进程检测器模块
提供企业微信进程检测、窗口句柄获取等功能
"""

import psutil
import win32gui
import win32process
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """进程信息数据结构"""
    pid: int
    name: str
    exe_path: str
    memory_usage: int
    cpu_percent: float
    create_time: float


class WechatProcessDetector:
    """企业微信进程检测器"""
    
    def __init__(self, process_names: Optional[List[str]] = None):
        """
        初始化企业微信进程检测器
        
        Args:
            process_names: 企业微信进程名称列表，默认为常见的企业微信进程名
        """
        self.process_names = process_names or [
            "WXWork.exe", 
            "企业微信.exe", 
            "WeChatWork.exe",
            "wxwork.exe"
        ]
        logger.info(f"初始化企业微信进程检测器，监控进程: {self.process_names}")
    
    def find_wechat_processes(self) -> List[ProcessInfo]:
        """
        查找所有企业微信进程
        
        Returns:
            List[ProcessInfo]: 找到的企业微信进程信息列表
        """
        wechat_processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'memory_info', 'cpu_percent', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] in self.process_names:
                        process_info = ProcessInfo(
                            pid=proc_info['pid'],
                            name=proc_info['name'],
                            exe_path=proc_info['exe'] or '',
                            memory_usage=proc_info['memory_info'].rss if proc_info['memory_info'] else 0,
                            cpu_percent=proc_info['cpu_percent'] or 0.0,
                            create_time=proc_info['create_time'] or 0.0
                        )
                        wechat_processes.append(process_info)
                        logger.debug(f"找到企业微信进程: PID={process_info.pid}, 名称={process_info.name}")
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    # 忽略无法访问的进程
                    continue
                    
        except Exception as e:
            logger.error(f"枚举进程时发生错误: {e}")
            
        logger.info(f"共找到 {len(wechat_processes)} 个企业微信进程")
        return wechat_processes
    
    def get_main_wechat_process(self) -> Optional[ProcessInfo]:
        """
        获取主要的企业微信进程（通常是内存使用最大的）
        
        Returns:
            Optional[ProcessInfo]: 主要的企业微信进程信息，如果没有找到则返回None
        """
        processes = self.find_wechat_processes()
        
        if not processes:
            logger.warning("未找到任何企业微信进程")
            return None
            
        # 选择内存使用最大的进程作为主进程
        main_process = max(processes, key=lambda p: p.memory_usage)
        logger.info(f"选择主要企业微信进程: PID={main_process.pid}, 内存使用={main_process.memory_usage // 1024 // 1024}MB")
        
        return main_process
    
    def is_wechat_running(self) -> bool:
        """
        检查企业微信是否正在运行
        
        Returns:
            bool: 如果企业微信正在运行返回True，否则返回False
        """
        processes = self.find_wechat_processes()
        is_running = len(processes) > 0
        logger.debug(f"企业微信运行状态: {is_running}")
        return is_running
    
    def get_process_window_handle(self, pid: int) -> Optional[int]:
        """
        根据进程ID获取对应的窗口句柄
        
        Args:
            pid: 进程ID
            
        Returns:
            Optional[int]: 窗口句柄，如果没有找到则返回None
        """
        def enum_windows_callback(hwnd, windows):
            """枚举窗口回调函数"""
            if win32gui.IsWindowVisible(hwnd):
                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid == pid:
                    window_title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    windows.append({
                        'hwnd': hwnd,
                        'title': window_title,
                        'class_name': class_name,
                        'width': width,
                        'height': height
                    })
            return True
        
        try:
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if not windows:
                logger.warning(f"未找到进程 {pid} 对应的可见窗口")
                return None
            
            # 优先选择主窗口的策略：
            # 1. 首先查找类名为 'WeWorkWindow' 的窗口（企业微信主窗口）
            # 2. 其次查找有标题且大小合理的窗口
            # 3. 最后选择最大的窗口
            
            main_windows = []
            
            # 策略1：查找WeWorkWindow类的窗口
            for window in windows:
                if window['class_name'] == 'WeWorkWindow':
                    main_windows.append(window)
            
            if main_windows:
                # 选择最大的WeWorkWindow窗口
                best_window = max(main_windows, key=lambda w: w['width'] * w['height'])
                logger.info(f"找到进程 {pid} 的主窗口句柄: {best_window['hwnd']}, 标题: {best_window['title']}")
                return best_window['hwnd']
            
            # 策略2：查找有标题且大小合理的窗口
            for window in windows:
                if (window['title'] and 
                    window['width'] > 100 and 
                    window['height'] > 100):
                    main_windows.append(window)
            
            if main_windows:
                # 选择最大的窗口
                best_window = max(main_windows, key=lambda w: w['width'] * w['height'])
                logger.info(f"找到进程 {pid} 的窗口句柄: {best_window['hwnd']}, 标题: {best_window['title']}")
                return best_window['hwnd']
            
            # 策略3：选择最大的窗口（兜底策略）
            if windows:
                best_window = max(windows, key=lambda w: w['width'] * w['height'])
                logger.warning(f"未找到明确的主窗口，选择最大窗口: {best_window['hwnd']}, 标题: {best_window['title']}, 大小: {best_window['width']}x{best_window['height']}")
                return best_window['hwnd']
            
            return None
                
        except Exception as e:
            logger.error(f"获取进程 {pid} 窗口句柄时发生错误: {e}")
            return None
    
    def get_wechat_window_handle(self) -> Optional[int]:
        """
        获取企业微信主窗口句柄
        
        Returns:
            Optional[int]: 企业微信主窗口句柄，如果没有找到则返回None
        """
        main_process = self.get_main_wechat_process()
        if not main_process:
            return None
            
        return self.get_process_window_handle(main_process.pid)
    
    def wait_for_wechat(self, timeout: float = 30.0) -> Optional[ProcessInfo]:
        """
        等待企业微信启动
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            Optional[ProcessInfo]: 企业微信进程信息，如果超时则返回None
        """
        logger.info(f"等待企业微信启动，超时时间: {timeout}秒")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            main_process = self.get_main_wechat_process()
            if main_process:
                logger.info(f"企业微信已启动，等待时间: {time.time() - start_time:.2f}秒")
                return main_process
            
            time.sleep(1.0)
        
        logger.warning(f"等待企业微信启动超时 ({timeout}秒)")
        return None 