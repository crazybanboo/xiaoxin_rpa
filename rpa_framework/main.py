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

from core.utils import RpaLogger, ConfigManager
from core.keyboard import KeyboardController
from workflows.wechat.wechat_simple_standalone import main_semi_auto_original

class RpaFramework:
    """RPA框架主类"""
    
    def __init__(self):
        """初始化RPA框架"""
        self.logger = RpaLogger.get_logger(__name__)
        self.config = ConfigManager()
        
        # 使用全局定位器实例，避免重复初始化
        self.keyboard = KeyboardController()
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


def main():
    """主函数"""
    rpa = None
    try:
        # 创建RPA框架实例
        rpa = RpaFramework()
        
        # 显示菜单
        while rpa.running:
            print("=" * 40)
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
                main_semi_auto_original()
            elif choice == '2':
                print("启动企业微信全自动化群发功能...")
                # main_auto()
            else:
                print("无效选择，请重新输入")
    
    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        print(f"程序运行出现错误: {e}")
    finally:
        # 清理资源
        if rpa:
            rpa.cleanup()

if __name__ == "__main__":
    main() 