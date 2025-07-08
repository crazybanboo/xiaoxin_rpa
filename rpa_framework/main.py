"""
RPA框架 - 主程序入口
提供RPA框架的使用示例和基本测试功能
"""

import sys
import os
import time
import signal
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.utils import RpaLogger, RpaException, ConfigManager, ScreenCapture
from core.locator import CoordinateLocator, ImageLocator, WindowLocator, locator
from core.mouse import MouseController
from core.keyboard import KeyboardController, LanguageType
from core.waiter import WaitController
from workflows.wechat.wechat_half_auto import main_semi_auto, main_auto

class RpaFramework:
    """RPA框架主类"""
    
    def __init__(self):
        """初始化RPA框架"""
        self.logger = RpaLogger.get_logger(__name__)
        self.config = ConfigManager()
        
        # 使用全局定位器实例，避免重复初始化
        self.locator = locator
        self.coordinate_locator = locator.coordinate_locator
        self.image_locator = locator.image_locator
        self.window_locator = locator.window_locator
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.waiter = WaitController(image_locator=self.image_locator)
        self.screen_capture = ScreenCapture()
        
        # 程序运行状态
        self.running = True
        
        # 设置F12终止程序功能
        self.setup_f12_exit()
        
        self.logger.info("RPA框架初始化完成")
    
    def setup_f12_exit(self):
        """设置F12键终止程序功能"""
        try:
            def on_f12_pressed():
                """F12按键回调函数"""
                self.logger.info("检测到F12按键，正在终止程序...")
                print("\n🔥 检测到F12按键，程序即将终止...")
                self.running = False
                
                # 停止全局键盘监听
                self.keyboard.stop_global_listener()
                
                # 强制退出程序
                os._exit(0)
            
            # 添加F12全局热键监听
            success = self.keyboard.add_global_hotkey('f12', on_f12_pressed, suppress=True)
            if success:
                # 启动全局键盘监听
                self.keyboard.start_global_listener()
                self.logger.info("F12终止程序功能已启用")
                print("💡 提示：按F12键可随时终止程序")
            else:
                self.logger.warning("F12终止程序功能启用失败")
                print("⚠️  警告：F12终止程序功能启用失败")
                
        except Exception as e:
            self.logger.error(f"设置F12终止程序功能失败: {e}")
            print(f"❌ 设置F12终止程序功能失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理资源...")
            # 停止全局键盘监听
            if hasattr(self, 'keyboard'):
                self.keyboard.stop_global_listener()
            print("✅ 资源清理完成")
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")
            print(f"❌ 资源清理失败: {e}")

    def demo_basic_operations(self):
        """演示基本操作"""
        try:
            self.logger.info("开始演示基本操作")
            
            # 1. 鼠标操作演示
            print("1. 鼠标操作演示")
            current_pos = self.mouse.get_position()
            print(f"当前鼠标位置: {current_pos}")
            
            # 移动鼠标
            self.mouse.move_to(500, 300, duration=1.0)
            self.waiter.sleep(1)
            
            # 点击操作
            self.mouse.click()
            self.waiter.sleep(0.5)
            
            # 2. 键盘操作演示
            print("2. 键盘操作演示")
            
            # 打开记事本进行测试
            self.keyboard.hotkey('win', 'r')  # 打开运行对话框
            self.waiter.sleep(1)
            
            self.keyboard.type_text('notepad')  # 输入notepad
            self.waiter.sleep(0.5)
            self.keyboard.press_key('enter')  # 按回车
            self.waiter.sleep(0.5)
            self.keyboard.press_key('enter')  # 按回车
            self.waiter.sleep(2)  # 等待记事本打开
            
            # 在记事本中输入文本（切换到英文输入）
            print("正在切换到英文输入环境...")
            english_switch_success = self.keyboard.change_language(LanguageType.EN)
            
            try:
                demo_text = "这是RPA框架的演示文本\\n包含多行内容\\n测试完成！"
                print(f"输入演示文本: {demo_text}")
                self.keyboard.type_text(demo_text)
                self.waiter.sleep(1)
                
                # 演示英文文本输入
                self.keyboard.press_key('enter')
                english_text = "\\nEnglish text input test - RPA Framework Demo"
                print(f"输入英文文本: {english_text}")
                self.keyboard.type_text(english_text)
                self.waiter.sleep(1)
                
            finally:
                # 恢复中文输入法（如果之前切换成功）
                if english_switch_success:
                    print("正在恢复中文输入法...")
                    self.keyboard.change_language(LanguageType.ZH)
                    print("输入法已恢复为中文")
            
            # 3. 组合操作演示
            print("3. 组合操作演示")
            
            # 全选文本
            self.keyboard.select_all()
            self.waiter.sleep(0.5)
            
            # 复制文本
            self.keyboard.copy()
            self.waiter.sleep(0.5)
            
            # 移动到文档末尾
            self.keyboard.hotkey('ctrl', 'end')
            self.waiter.sleep(0.5)
            
            # 换行并粘贴
            self.keyboard.press_key('enter')
            self.keyboard.type_text("\\n复制的内容：\\n")
            self.keyboard.paste()
            
            print("基本操作演示完成！")
            
        except Exception as e:
            self.logger.error(f"演示过程出现错误: {e}")
            print(f"演示失败: {e}")
    
    def demo_image_recognition(self):
        """演示图像识别功能"""
        try:
            self.logger.info("开始演示图像识别功能")
            print("3. 图像识别演示")
            
            # 截取当前屏幕作为参考
            screenshot_path = "current_screen.png"
            self.screen_capture.screenshot(filename=screenshot_path)
            print(f"屏幕截图已保存: {screenshot_path}")
            
            # 截取屏幕的一个区域作为模板
            template_path = "template.png"
            region = (100, 100, 200, 100)  # left, top, width, height
            self.screen_capture.screenshot(region=region, filename=template_path)
            print(f"模板图像已保存: {template_path}")
            
            # 尝试在屏幕上找到这个模板
            result = self.image_locator.locate_by_template(template_path)
            if result:
                # 转换为中心坐标
                center_x = result[0] + (result[2] - result[0]) // 2
                center_y = result[1] + (result[3] - result[1]) // 2
                location = (center_x, center_y)
                print(f"找到模板图像，位置: {location}")
                
                # 点击找到的位置
                self.mouse.click(location[0], location[1])
                print("已点击找到的图像位置")
            else:
                print("未找到模板图像")
            
        except Exception as e:
            self.logger.error(f"图像识别演示出现错误: {e}")
            print(f"图像识别演示失败: {e}")
    
    def demo_window_operations(self):
        """演示窗口操作功能"""
        try:
            self.logger.info("开始演示窗口操作功能")
            print("5. 窗口操作演示")
            
            # 查找记事本窗口
            notepad_windows = self.window_locator.find_window_by_title("记事本")
            if notepad_windows:
                window_handle = notepad_windows
                print(f"找到记事本窗口: {window_handle}")
                
                # 激活窗口
                if self.window_locator.activate_window(window_handle):
                    print("记事本窗口已激活")
                    
                    # 获取窗口位置和大小
                    rect = self.window_locator.get_window_rect(window_handle)
                    if rect:
                        print(f"窗口位置和大小: {rect}")
                        
                        # 窗口操作完成（move_window方法不可用）
                        print("窗口操作演示完成")
            else:
                print("未找到记事本窗口")
            
        except Exception as e:
            self.logger.error(f"窗口操作演示出现错误: {e}")
            print(f"窗口操作演示失败: {e}")
    
    def demo_wait_operations(self):
        """演示等待操作功能"""
        try:
            self.logger.info("开始演示等待操作功能")
            print("6. 等待操作演示")
            
            # 等待条件演示
            def check_mouse_position():
                x, y = self.mouse.get_position()
                return x > 800 and y > 400
            
            print("请将鼠标移动到屏幕右下角（坐标大于800,400）...")
            
            # 等待鼠标移动到指定位置
            if self.waiter.wait_until(check_mouse_position, timeout=10.0):
                print("鼠标位置条件满足！")
            else:
                print("等待超时，鼠标未移动到指定位置")
            
            # 重试操作演示
            def unreliable_operation():
                import random
                if random.random() < 0.7:  # 70%的失败率
                    raise Exception("模拟操作失败")
                return "操作成功"
            
            print("演示重试操作...")
            try:
                result = self.waiter.wait_and_retry(unreliable_operation, max_retries=5)
                print(f"重试操作结果: {result}")
            except Exception as e:
                print(f"重试操作最终失败: {e}")
            
        except Exception as e:
            self.logger.error(f"等待操作演示出现错误: {e}")
            print(f"等待操作演示失败: {e}")
    
    def demo_ime_control(self):
        """演示IME输入法控制功能"""
        try:
            self.logger.info("开始演示IME输入法控制功能")
            print("6. IME输入法控制演示")

            # 打开记事本进行测试
            print("打开记事本进行输入法控制测试...")
            self.keyboard.hotkey('win', 'r')
            self.waiter.sleep(0.5)
            self.keyboard.type_text('notepad')
            self.waiter.sleep(0.5)
            self.keyboard.press_key('enter')
            self.waiter.sleep(0.5)
            self.keyboard.press_key('enter')
            self.waiter.sleep(2)
            
            # 测试切换到英文输入法
            print("测试切换到英文输入法...")
            if self.keyboard.change_language(LanguageType.EN):
                print("成功切换到英文输入法")
                
                # 输入英文文本
                test_text = "IME Control Test - English Input"
                print(f"输入测试文本: {test_text}")
                self.keyboard.type_text(test_text)
                self.waiter.sleep(1)
            else:
                print("切换到英文输入法失败")
            print("IME控制演示完成！")
        except Exception as e:
            self.logger.error(f"IME控制演示出现错误: {e}")
            print(f"IME控制演示失败: {e}")
    
    def run_full_demo(self):
        """运行完整演示"""
        try:
            print("=" * 50)
            print("RPA框架功能演示开始")
            print("=" * 50)
            
            # 基本操作演示
            self.demo_basic_operations()
            self.waiter.sleep(2)
            
            # 图像识别演示
            self.demo_image_recognition()
            self.waiter.sleep(2)
            
            # 窗口操作演示
            self.demo_window_operations()
            self.waiter.sleep(2)
            
            # 等待操作演示
            self.demo_wait_operations()
            
            print("=" * 50)
            print("RPA框架功能演示完成")
            print("=" * 50)
            
        except Exception as e:
            self.logger.error(f"演示过程出现错误: {e}")
            print(f"演示失败: {e}")

def main():
    """主函数"""
    rpa = None
    try:
        # 创建RPA框架实例
        rpa = RpaFramework()
        
        # 显示菜单
        while rpa.running:
            print("\\n" + "=" * 40)
            print("RPA框架菜单")
            print("=" * 40)
            print("1. 企业微信半自动化群发")
            print("2. 企业微信全自动化群发")
            print("0. 退出")
            print("=" * 40)
            
            try:
                choice = input("请选择操作 (0-2): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\\n程序被用户中断")
                break
            
            if choice == '0':
                print("退出程序")
                break
            elif choice == '1':
                print("启动企业微信半自动化群发功能...")
                main_semi_auto()
            elif choice == '2':
                print("启动企业微信全自动化群发功能...")
                main_auto()
            else:
                print("无效选择，请重新输入")
    
    except KeyboardInterrupt:
        print("\\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出现错误: {e}")
    finally:
        # 清理资源
        if rpa:
            rpa.cleanup()

if __name__ == "__main__":
    main() 