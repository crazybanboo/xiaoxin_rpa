"""
企业微信工作流使用示例
展示重构后的简化API使用方法

重构后的优势：
1. 更简洁的API调用
2. 直接的异常处理
3. 内置调试支持
4. 灵活的配置管理
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from workflows.wechat.wechat_simple import WechatWorkflow, quick_mass_send, quick_semi_auto_send
from core.mouse_helpers import find_and_click, find_template_centers
from core.vision_debug import debug_template_match, batch_confidence_test
from config.settings import get_config, set_config, with_config_override
from workflows.wechat.exceptions import WechatOperationError


def example_1_basic_workflow():
    """示例1：基础工作流使用"""
    print("=== 示例1：基础工作流使用 ===")
    
    try:
        # 创建工作流实例
        workflow = WechatWorkflow(debug_mode=True)
        
        # 执行初始化
        if workflow.initialize_and_adjust_window():
            print("✅ 企业微信初始化成功")
            
            # 查找并点击特定元素
            if workflow.find_and_click_wechat_element("contact_button.png"):
                print("✅ 成功点击联系人按钮")
            
            # 滚动联系人列表
            workflow.scroll_contact_list("down", 300)
            print("✅ 联系人列表滚动完成")
            
        else:
            print("❌ 企业微信初始化失败")
            
    except WechatOperationError as e:
        print(f"❌ 操作失败: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")


def example_2_mass_sending():
    """示例2：群发消息"""
    print("\n=== 示例2：群发消息 ===")
    
    try:
        # 使用便捷函数进行群发
        success = quick_mass_send(
            group_template="group_item.png",  # 群组模板
            max_groups=20,                    # 最多选择20个群
            use_crazy_click=False,            # 不使用疯狂点击
            debug_mode=True                   # 启用调试模式
        )
        
        if success:
            print("✅ 群发消息成功")
        else:
            print("❌ 群发消息失败")
            
    except Exception as e:
        print(f"❌ 群发异常: {e}")


def example_3_semi_auto_workflow():
    """示例3：半自动工作流"""
    print("\n=== 示例3：半自动工作流 ===")
    
    try:
        # 使用半自动模式，在关键点暂停等待用户确认
        success = quick_semi_auto_send(debug_mode=True)
        
        if success:
            print("✅ 半自动工作流执行成功")
        else:
            print("❌ 半自动工作流执行失败")
            
    except Exception as e:
        print(f"❌ 半自动工作流异常: {e}")


def example_4_crazy_click():
    """示例4：疯狂点击功能"""
    print("\n=== 示例4：疯狂点击功能 ===")
    
    try:
        workflow = WechatWorkflow(debug_mode=True)
        
        # 初始化
        if workflow.initialize_and_adjust_window():
            # 设置多选模式
            workflow.setup_multiselect_mode()
            
            # 手动选择群组
            input("请手动选择要发送的群组，然后按回车继续...")
            
            # 使用疯狂点击发送
            if workflow.perform_crazy_click("send_button.png", groups=6, clicks_per_group=100):
                print("✅ 疯狂点击发送成功")
            else:
                print("❌ 疯狂点击发送失败")
                
    except Exception as e:
        print(f"❌ 疯狂点击异常: {e}")


def example_5_template_debugging():
    """示例5：模板调试"""
    print("\n=== 示例5：模板调试 ===")
    
    # 调试单个模板
    print("启动模板调试界面...")
    debug_template_match("contact_button.png", confidence=0.8)
    
    # 批量置信度测试
    print("执行批量置信度测试...")
    results = batch_confidence_test(
        "group_item.png", 
        confidence_range=(0.6, 0.95),
        step=0.05
    )
    
    print(f"置信度测试结果: {len(results)} 个测试点")
    for conf, count in results.items():
        if count > 0:
            print(f"  置信度 {conf:.2f}: 找到 {count} 个匹配")


def example_6_direct_mouse_operations():
    """示例6：直接使用鼠标操作"""
    print("\n=== 示例6：直接使用鼠标操作 ===")
    
    try:
        # 查找并点击（不使用工作流封装）
        if find_and_click("contact_button.png", confidence=0.8, timeout=5.0):
            print("✅ 直接点击成功")
        
        # 查找模板中心点
        centers = find_template_centers("group_item.png", confidence=0.8, max_results=5)
        print(f"找到 {len(centers)} 个群组中心点: {centers}")
        
        # 批量点击这些位置
        from core.mouse_helpers import batch_click
        if centers:
            clicked = batch_click(centers, delay=0.3)
            print(f"✅ 批量点击完成: {clicked} 个位置")
            
    except Exception as e:
        print(f"❌ 直接操作异常: {e}")


def example_7_config_management():
    """示例7：配置管理"""
    print("\n=== 示例7：配置管理 ===")
    
    # 获取配置
    current_confidence = get_config('image.confidence', 0.8)
    print(f"当前图像置信度: {current_confidence}")
    
    # 设置配置
    set_config('image.confidence', 0.9)
    print("图像置信度已设置为 0.9")
    
    # 使用临时配置覆盖
    with with_config_override(image_confidence=0.95, debug_mode=True):
        print("在这个代码块中，置信度临时设置为 0.95")
        # 在这里执行需要高置信度的操作
        
    print(f"退出代码块后，置信度恢复为: {get_config('image.confidence')}")


def example_8_error_handling():
    """示例8：错误处理最佳实践"""
    print("\n=== 示例8：错误处理最佳实践 ===")
    
    workflow = WechatWorkflow(debug_mode=True)
    
    try:
        # 尝试执行可能失败的操作
        workflow.initialize_and_adjust_window()
        
        # 查找可选元素（不是必需的）
        if workflow.find_and_click_wechat_element("optional_button.png", required=False):
            print("找到可选按钮并点击")
        else:
            print("可选按钮未找到，跳过")
        
        # 查找必需元素
        workflow.find_and_click_wechat_element("required_button.png", required=True)
        
    except WechatOperationError as e:
        print(f"企业微信操作错误: {e}")
        # 可以在这里添加重试逻辑或回滚操作
        
    except Exception as e:
        print(f"未知错误: {e}")
        # 记录详细错误信息
        import traceback
        print(traceback.format_exc())


def example_9_workflow_execution_summary():
    """示例9：工作流执行摘要"""
    print("\n=== 示例9：工作流执行摘要 ===")
    
    workflow = WechatWorkflow(debug_mode=True)
    
    # 执行一些操作
    workflow.execute()
    
    # 获取执行摘要
    summary = workflow.get_execution_summary()
    
    print(f"工作流名称: {summary['name']}")
    print(f"执行时长: {summary['duration']:.2f} 秒")
    print(f"总操作数: {summary['total_operations']}")
    print(f"错误数量: {summary['error_count']}")
    print(f"成功率: {summary['success_rate']:.2%}")


def main():
    """主函数：运行所有示例"""
    print("企业微信工作流示例程序")
    print("重构后的简化API演示")
    print("=" * 50)
    
    examples = [
        ("基础工作流", example_1_basic_workflow),
        ("群发消息", example_2_mass_sending),
        ("半自动工作流", example_3_semi_auto_workflow),
        ("疯狂点击", example_4_crazy_click),
        ("模板调试", example_5_template_debugging),
        ("直接鼠标操作", example_6_direct_mouse_operations),
        ("配置管理", example_7_config_management),
        ("错误处理", example_8_error_handling),
        ("执行摘要", example_9_workflow_execution_summary),
    ]
    
    print("可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("0. 运行所有示例")
    
    choice = input("\n请选择要运行的示例 (0-9): ").strip()
    
    try:
        if choice == "0":
            # 运行所有示例
            for name, func in examples:
                print(f"\n{'='*20} {name} {'='*20}")
                try:
                    func()
                except KeyboardInterrupt:
                    print("用户中断")
                    break
                except Exception as e:
                    print(f"示例执行异常: {e}")
        else:
            # 运行单个示例
            index = int(choice) - 1
            if 0 <= index < len(examples):
                name, func = examples[index]
                print(f"\n运行示例: {name}")
                func()
            else:
                print("无效选择")
                
    except ValueError:
        print("请输入有效数字")
    except KeyboardInterrupt:
        print("\n程序被用户中断")


if __name__ == "__main__":
    main()