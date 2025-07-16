"""
RPA框架 - 简化版本主程序
直接调用原版半自动逻辑，避免复杂的依赖关系
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主函数"""
    try:
        # 直接从原版文件导入
        from workflows.wechat.wechat_half_auto import main_semi_auto
        
        # 显示菜单
        while True:
            print("\n" + "=" * 40)
            print("RPA框架菜单")
            print("=" * 40)
            print("1. 企业微信半自动化群发")
            print("0. 退出")
            print("=" * 40)
            
            try:
                choice = input("请选择操作 (0-1): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n程序被用户中断")
                break
            
            if choice == '0':
                print("退出程序")
                break
            elif choice == '1':
                print("启动企业微信半自动化群发功能...")
                try:
                    main_semi_auto()
                except Exception as e:
                    print(f"执行失败: {e}")
            else:
                print("无效选择，请重新输入")
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出现错误: {e}")

if __name__ == "__main__":
    main()