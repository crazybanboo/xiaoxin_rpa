"""
RPA框架 - 图像识别调试框架
提供强大但简洁的调试工具，帮助快速调试模板匹配问题

功能特性：
1. 实时模板匹配可视化
2. 置信度调试滑块
3. 区域选择工具
4. 匹配结果边框显示
5. 批量置信度测试
"""

import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Tuple, Optional, Dict, Any
import threading
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from .locator import CompositeLocator
from .utils import logger, RpaException


class VisionDebugger:
    """图像识别调试器"""
    
    def __init__(self):
        self.locator = CompositeLocator()
        self.current_template = None
        self.current_screenshot = None
        self.debug_window = None
        self.is_running = False
        
    def debug_template_match(self, template_path: str, 
                           confidence: float = 0.8,
                           region: Optional[Tuple[int, int, int, int]] = None,
                           grayscale: bool = True) -> None:
        """
        调试模板匹配
        
        Args:
            template_path: 模板路径
            confidence: 初始置信度
            region: 搜索区域
            grayscale: 是否使用灰度模式
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV不可用，无法启动图像调试")
            return
        
        self.current_template = template_path
        self._launch_debug_window(template_path, confidence, region, grayscale)
    
    def _launch_debug_window(self, template_path: str, confidence: float, 
                           region: Optional[Tuple[int, int, int, int]], grayscale: bool):
        """启动调试窗口"""
        
        # 创建主窗口
        self.debug_window = tk.Tk()
        self.debug_window.title(f"图像识别调试 - {Path(template_path).name}")
        self.debug_window.geometry("800x600")
        
        # 配置变量
        self.confidence_var = tk.DoubleVar(value=confidence)
        self.grayscale_var = tk.BooleanVar(value=grayscale)
        self.live_update_var = tk.BooleanVar(value=False)
        
        # 创建UI布局
        self._create_debug_ui()
        
        # 初始化
        self._update_debug_display()
        
        # 启动窗口
        self.debug_window.mainloop()
    
    def _create_debug_ui(self):
        """创建调试UI"""
        main_frame = ttk.Frame(self.debug_window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding=10)
        control_frame.pack(fill='x', pady=(0, 10))
        
        # 置信度控制
        ttk.Label(control_frame, text="置信度:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        confidence_scale = ttk.Scale(control_frame, from_=0.1, to=1.0, 
                                   variable=self.confidence_var, 
                                   orient='horizontal', length=200,
                                   command=self._on_confidence_change)
        confidence_scale.grid(row=0, column=1, sticky='ew', padx=(0, 10))
        
        confidence_label = ttk.Label(control_frame, text="0.80")
        confidence_label.grid(row=0, column=2, sticky='w')
        self.confidence_label = confidence_label
        
        # 灰度模式
        ttk.Checkbutton(control_frame, text="灰度模式", 
                       variable=self.grayscale_var,
                       command=self._on_grayscale_change).grid(row=0, column=3, sticky='w', padx=(20, 0))
        
        # 实时更新
        ttk.Checkbutton(control_frame, text="实时更新", 
                       variable=self.live_update_var,
                       command=self._on_live_update_change).grid(row=0, column=4, sticky='w', padx=(20, 0))
        
        # 按钮组
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=1, column=0, columnspan=5, pady=(10, 0), sticky='ew')
        
        ttk.Button(button_frame, text="手动刷新", 
                  command=self._update_debug_display).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="选择模板", 
                  command=self._select_template).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="批量测试", 
                  command=self._batch_confidence_test).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="区域选择", 
                  command=self._region_selector).pack(side='left', padx=(0, 5))
        
        # 配置列权重
        control_frame.grid_columnconfigure(1, weight=1)
        
        # 显示区域
        display_frame = ttk.LabelFrame(main_frame, text="匹配结果", padding=10)
        display_frame.pack(fill='both', expand=True)
        
        # 创建Canvas用于显示图像
        self.canvas = tk.Canvas(display_frame, bg='white')
        self.canvas.pack(fill='both', expand=True)
        
        # 信息标签
        self.info_label = ttk.Label(display_frame, text="准备就绪")
        self.info_label.pack(pady=(10, 0))
        
        # 启动实时更新线程
        self.is_running = True
        self._start_live_update_thread()
    
    def _on_confidence_change(self, value):
        """置信度变化回调"""
        self.confidence_label.config(text=f"{float(value):.2f}")
        if self.live_update_var.get():
            self._update_debug_display()
    
    def _on_grayscale_change(self):
        """灰度模式变化回调"""
        if self.live_update_var.get():
            self._update_debug_display()
    
    def _on_live_update_change(self):
        """实时更新变化回调"""
        if self.live_update_var.get():
            self._update_debug_display()
    
    def _update_debug_display(self):
        """更新调试显示"""
        if not self.current_template:
            return
        
        try:
            # 获取当前参数
            confidence = self.confidence_var.get()
            grayscale = self.grayscale_var.get()
            
            # 执行模板匹配
            results = self.locator.image_locator.locate_all_by_template(
                self.current_template, confidence, grayscale=grayscale, max_results=20
            )
            
            # 获取截图
            screenshot = self.locator.image_locator.get_screenshot()
            
            # 在截图上绘制匹配结果
            display_image = self._draw_matches_on_screenshot(screenshot, results)
            
            # 显示在Canvas上
            self._display_image_on_canvas(display_image)
            
            # 更新信息
            info_text = f"找到 {len(results)} 个匹配项，置信度: {confidence:.2f}"
            if results:
                best_confidence = max(result[4] for result in results)
                info_text += f"，最高置信度: {best_confidence:.3f}"
            self.info_label.config(text=info_text)
            
        except Exception as e:
            logger.error(f"更新调试显示时出错: {e}")
            self.info_label.config(text=f"错误: {str(e)}")
    
    def _draw_matches_on_screenshot(self, screenshot, results):
        """在截图上绘制匹配结果"""
        if not isinstance(screenshot, np.ndarray):
            screenshot = np.array(screenshot)
        
        # 确保是BGR格式（OpenCV格式）
        if len(screenshot.shape) == 3:
            display_image = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        else:
            display_image = screenshot.copy()
        
        # 绘制匹配框
        for i, (left, top, right, bottom, confidence) in enumerate(results):
            # 根据置信度设置颜色
            if confidence >= 0.9:
                color = (0, 255, 0)  # 绿色
            elif confidence >= 0.8:
                color = (0, 255, 255)  # 黄色
            else:
                color = (0, 0, 255)  # 红色
            
            # 绘制矩形框
            cv2.rectangle(display_image, (left, top), (right, bottom), color, 2)
            
            # 绘制置信度文本
            text = f"{confidence:.3f}"
            cv2.putText(display_image, text, (left, top - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return display_image
    
    def _display_image_on_canvas(self, image):
        """在Canvas上显示图像"""
        # 转换为PIL Image
        if isinstance(image, np.ndarray):
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # 获取Canvas大小
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # 缩放图像以适应Canvas
            pil_image.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
        
        # 转换为PhotoImage
        photo = ImageTk.PhotoImage(pil_image)
        
        # 清空Canvas并显示图像
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, 
                                image=photo, anchor='center')
        
        # 保存引用防止垃圾回收
        self.canvas.image = photo
    
    def _select_template(self):
        """选择模板文件"""
        file_path = filedialog.askopenfilename(
            title="选择模板文件",
            filetypes=[("图像文件", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if file_path:
            self.current_template = file_path
            self._update_debug_display()
    
    def _batch_confidence_test(self):
        """批量置信度测试"""
        if not self.current_template:
            messagebox.showwarning("警告", "请先选择模板文件")
            return
        
        self._show_batch_test_window()
    
    def _show_batch_test_window(self):
        """显示批量测试窗口"""
        test_window = tk.Toplevel(self.debug_window)
        test_window.title("批量置信度测试")
        test_window.geometry("600x400")
        
        # 参数设置
        param_frame = ttk.LabelFrame(test_window, text="测试参数", padding=10)
        param_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(param_frame, text="起始置信度:").grid(row=0, column=0, sticky='w')
        start_var = tk.DoubleVar(value=0.6)
        ttk.Entry(param_frame, textvariable=start_var, width=10).grid(row=0, column=1, sticky='w', padx=(5, 20))
        
        ttk.Label(param_frame, text="结束置信度:").grid(row=0, column=2, sticky='w')
        end_var = tk.DoubleVar(value=0.95)
        ttk.Entry(param_frame, textvariable=end_var, width=10).grid(row=0, column=3, sticky='w', padx=(5, 20))
        
        ttk.Label(param_frame, text="步长:").grid(row=0, column=4, sticky='w')
        step_var = tk.DoubleVar(value=0.05)
        ttk.Entry(param_frame, textvariable=step_var, width=10).grid(row=0, column=5, sticky='w', padx=(5, 0))
        
        # 开始测试按钮
        ttk.Button(param_frame, text="开始测试", 
                  command=lambda: self._run_batch_test(start_var.get(), end_var.get(), 
                                                     step_var.get(), result_text)).grid(row=1, column=0, columnspan=6, pady=10)
        
        # 结果显示
        result_frame = ttk.LabelFrame(test_window, text="测试结果", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        result_text = tk.Text(result_frame, height=15)
        scrollbar = ttk.Scrollbar(result_frame, orient='vertical', command=result_text.yview)
        result_text.configure(yscrollcommand=scrollbar.set)
        
        result_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def _run_batch_test(self, start_conf: float, end_conf: float, step: float, result_text: tk.Text):
        """运行批量测试"""
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "开始批量置信度测试...\n")
        result_text.insert(tk.END, f"模板: {self.current_template}\n")
        result_text.insert(tk.END, f"置信度范围: {start_conf:.2f} - {end_conf:.2f}, 步长: {step:.2f}\n")
        result_text.insert(tk.END, "-" * 50 + "\n")
        
        current_conf = start_conf
        while current_conf <= end_conf:
            try:
                # 执行匹配
                results = self.locator.image_locator.locate_all_by_template(
                    self.current_template, current_conf, max_results=10
                )
                
                # 输出结果
                result_text.insert(tk.END, f"置信度 {current_conf:.2f}: 找到 {len(results)} 个匹配项")
                
                if results:
                    best_match = max(results, key=lambda x: x[4])
                    result_text.insert(tk.END, f", 最高置信度: {best_match[4]:.3f}")
                
                result_text.insert(tk.END, "\n")
                result_text.see(tk.END)
                result_text.update()
                
            except Exception as e:
                result_text.insert(tk.END, f"置信度 {current_conf:.2f}: 错误 - {str(e)}\n")
            
            current_conf += step
        
        result_text.insert(tk.END, "-" * 50 + "\n")
        result_text.insert(tk.END, "批量测试完成！\n")
        result_text.see(tk.END)
    
    def _region_selector(self):
        """区域选择工具"""
        messagebox.showinfo("区域选择", "区域选择功能正在开发中...")
    
    def _start_live_update_thread(self):
        """启动实时更新线程"""
        def update_thread():
            while self.is_running:
                try:
                    if self.live_update_var.get():
                        self.debug_window.after(0, self._update_debug_display)
                    time.sleep(0.5)  # 每0.5秒检查一次
                except:
                    break
        
        thread = threading.Thread(target=update_thread, daemon=True)
        thread.start()
    
    def close(self):
        """关闭调试器"""
        self.is_running = False
        if self.debug_window:
            self.debug_window.destroy()


# 便捷函数
def debug_template_match(template_path: str, confidence: float = 0.8) -> None:
    """
    调试模板匹配（便捷函数）
    
    Args:
        template_path: 模板图片路径
        confidence: 初始置信度
    """
    if not CV2_AVAILABLE:
        print("OpenCV不可用，无法启动图像调试")
        return
    
    debugger = VisionDebugger()
    debugger.debug_template_match(template_path, confidence)


def batch_confidence_test(template_path: str, 
                         confidence_range: Tuple[float, float] = (0.6, 0.95),
                         step: float = 0.05) -> Dict[float, int]:
    """
    批量置信度测试（便捷函数）
    
    Args:
        template_path: 模板路径
        confidence_range: 置信度范围 (start, end)
        step: 步长
        
    Returns:
        测试结果字典 {置信度: 匹配数量}
    """
    if not CV2_AVAILABLE:
        logger.error("OpenCV不可用，无法进行批量测试")
        return {}
    
    locator = CompositeLocator()
    results = {}
    
    start_conf, end_conf = confidence_range
    current_conf = start_conf
    
    logger.info(f"开始批量置信度测试: {template_path}")
    logger.info(f"置信度范围: {start_conf:.2f} - {end_conf:.2f}, 步长: {step:.2f}")
    
    while current_conf <= end_conf:
        try:
            matches = locator.image_locator.locate_all_by_template(
                template_path, current_conf, max_results=20
            )
            
            match_count = len(matches)
            results[current_conf] = match_count
            
            logger.info(f"置信度 {current_conf:.2f}: 找到 {match_count} 个匹配项")
            
            if matches:
                best_match = max(matches, key=lambda x: x[4])
                logger.info(f"  最高置信度: {best_match[4]:.3f}")
            
        except Exception as e:
            logger.error(f"置信度 {current_conf:.2f} 测试失败: {e}")
            results[current_conf] = 0
        
        current_conf += step
    
    logger.info("批量置信度测试完成")
    return results


def live_match_preview(template_path: str, confidence: float = 0.8, duration: float = 10.0) -> None:
    """
    实时匹配预览（便捷函数）
    
    Args:
        template_path: 模板路径
        confidence: 置信度
        duration: 预览持续时间（秒）
    """
    if not CV2_AVAILABLE:
        logger.error("OpenCV不可用，无法启动实时预览")
        return
    
    locator = CompositeLocator()
    start_time = time.time()
    
    logger.info(f"开始实时匹配预览: {template_path}, 持续时间: {duration}秒")
    
    while time.time() - start_time < duration:
        try:
            # 执行匹配
            results = locator.image_locator.locate_all_by_template(
                template_path, confidence, max_results=5
            )
            
            if results:
                logger.info(f"找到 {len(results)} 个匹配项")
                for i, (left, top, right, bottom, match_conf) in enumerate(results):
                    logger.info(f"  匹配{i+1}: ({left}, {top}, {right}, {bottom}), 置信度: {match_conf:.3f}")
            else:
                logger.info("未找到匹配项")
            
            time.sleep(1.0)
            
        except KeyboardInterrupt:
            logger.info("用户中断预览")
            break
        except Exception as e:
            logger.error(f"实时预览出错: {e}")
            break
    
    logger.info("实时匹配预览结束")


def visual_region_selector() -> Optional[Tuple[int, int, int, int]]:
    """
    可视化区域选择工具
    
    Returns:
        选择的区域 (left, top, width, height) 或 None
    """
    # 这里应该实现一个可视化的区域选择工具
    # 由于复杂性，这里先返回None，留待以后实现
    logger.warning("可视化区域选择工具暂未实现")
    return None