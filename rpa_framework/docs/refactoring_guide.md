# RPA框架重构使用指南

## 重构概述

本次重构的目标是消除过度封装，简化API调用，提高开发效率。重构后的框架具有以下特点：

### 🎯 重构改进

1. **消除过度封装** - 移除了 `WechatOperationInterface` 等不必要的抽象层
2. **简化API调用** - 直接使用功能函数，减少调用链长度  
3. **强化调试支持** - 内置图像识别调试工具
4. **优化配置管理** - 支持运行时配置更新和环境变量
5. **统一错误处理** - 使用标准异常机制而非复杂的结果包装

### 📁 新的代码结构

```
rpa_framework/
├── core/
│   ├── mouse_helpers.py      # 通用鼠标操作工具
│   ├── vision_debug.py       # 图像识别调试框架
│   ├── workflow_base.py      # 工作流基础类
│   ├── template_manager.py   # 模板管理器
│   └── ...
├── workflows/
│   └── wechat/
│       ├── wechat_simple.py  # 简化的企业微信工作流
│       └── ...
├── examples/
│   └── wechat_workflow_examples.py  # 使用示例
└── docs/
    └── refactoring_guide.md  # 本文档
```

## 使用指南

### 1. 基础鼠标操作

重构前（复杂）：
```python
wechat_auto = WechatHalfAuto()
result = wechat_auto.find_and_click_button("button.png", confidence=0.8)
if result.success:
    print(f"点击成功: {result.message}")
```

重构后（简洁）：
```python
from core.mouse_helpers import find_and_click

try:
    find_and_click("button.png", confidence=0.8)
    print("点击成功")
except TemplateNotFound:
    print("按钮未找到")
```

### 2. 企业微信工作流

#### 2.1 快速群发

```python
from workflows.wechat.wechat_simple import quick_mass_send

# 一行代码实现群发
success = quick_mass_send(
    group_template="group_item.png",
    max_groups=20,
    use_crazy_click=False,
    debug_mode=True
)
```

#### 2.2 详细工作流控制

```python
from workflows.wechat.wechat_simple import WechatWorkflow

workflow = WechatWorkflow(debug_mode=True)

try:
    # 1. 初始化
    workflow.initialize_and_adjust_window()
    
    # 2. 设置多选模式
    workflow.setup_multiselect_mode()
    
    # 3. 选择群组
    count = workflow.select_groups("group_item.png", max_groups=50)
    print(f"选择了 {count} 个群组")
    
    # 4. 发送消息
    workflow.send_message()
    
except WechatOperationError as e:
    print(f"操作失败: {e}")
```

### 3. 图像识别调试

#### 3.1 启动调试界面

```python
from core.vision_debug import debug_template_match

# 启动可视化调试界面
debug_template_match("button.png", confidence=0.8)
```

#### 3.2 批量置信度测试

```python
from core.vision_debug import batch_confidence_test

# 测试不同置信度下的匹配结果
results = batch_confidence_test(
    "group_item.png",
    confidence_range=(0.6, 0.95),
    step=0.05
)

for confidence, count in results.items():
    print(f"置信度 {confidence:.2f}: {count} 个匹配")
```

### 4. 配置管理

#### 4.1 基础配置操作

```python
from config.settings import get_config, set_config

# 获取配置
confidence = get_config('image.confidence', 0.8)

# 设置配置
set_config('image.confidence', 0.9, save=True)
```

#### 4.2 临时配置覆盖

```python
from config.settings import with_config_override

# 临时修改配置
with with_config_override(image_confidence=0.95, debug_mode=True):
    # 在这个代码块中使用临时配置
    find_and_click("high_precision_button.png")
# 退出后自动恢复原配置
```

#### 4.3 环境变量支持

```bash
# 设置环境变量
export RPA_IMAGE_CONFIDENCE=0.9
export RPA_DEBUG_MODE=true
export RPA_WINDOW_WIDTH=1400
export RPA_WINDOW_HEIGHT=900
```

```python
from config.settings import get_settings

# 从环境变量加载配置
settings = get_settings()
settings.load_from_env()
```

### 5. 模板管理

#### 5.1 自动模板发现

```python
from core.template_manager import template_manager

# 扫描并注册所有模板
template_manager.scan_templates()

# 获取模板路径
path = template_manager.get_template_path("button.png")
```

#### 5.2 模板分组管理

```python
# 注册模板到特定分组
template_manager.register_template(
    name="send_button",
    path="templates/wechat/send_button.png",
    group="wechat",
    description="发送按钮",
    confidence=0.8,
    tags=["button", "send"]
)

# 列出分组中的模板
wechat_templates = template_manager.list_templates("wechat")

# 搜索模板
results = template_manager.search_templates("send", group="wechat")
```

### 6. 工作流基类使用

#### 6.1 创建自定义工作流

```python
from core.workflow_base import WorkflowBase

class MyCustomWorkflow(WorkflowBase):
    def run(self) -> bool:
        try:
            # 1. 查找并点击按钮
            if not self.find_and_click("start_button.png"):
                return False
            
            # 2. 等待页面加载
            self.sleep(2.0, "等待页面加载")
            
            # 3. 批量操作
            count = self.find_all_and_click("item.png", max_clicks=10)
            print(f"处理了 {count} 个项目")
            
            return True
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            return False

# 使用工作流
workflow = MyCustomWorkflow("我的工作流", debug_mode=True)
success = workflow.execute()
```

#### 6.2 获取执行摘要

```python
# 执行完成后获取摘要
summary = workflow.get_execution_summary()
print(f"执行时长: {summary['duration']:.2f}秒")
print(f"成功率: {summary['success_rate']:.2%}")
print(f"错误数: {summary['error_count']}")
```

## 最佳实践

### 1. 错误处理

```python
from workflows.wechat.exceptions import WechatOperationError
from core.mouse_helpers import TemplateNotFound

try:
    # 执行操作
    workflow.find_and_click_wechat_element("button.png", required=True)
    
except TemplateNotFound:
    # 处理模板未找到
    print("模板未找到，可能需要更新模板文件")
    
except WechatOperationError as e:
    # 处理企业微信特定错误
    print(f"企业微信操作失败: {e}")
    
except Exception as e:
    # 处理其他异常
    print(f"未知错误: {e}")
```

### 2. 调试模式开发

```python
# 开发时启用调试模式
workflow = WechatWorkflow(debug_mode=True)

# 调试特定模板
workflow.debug_template("problem_button.png", confidence=0.8)

# 测试不同置信度
results = workflow.test_template_confidence("button.png", 0.6, 0.95)
```

### 3. 配置管理

```python
# 为不同环境使用不同配置
if environment == "production":
    set_config('general.debug_mode', False)
    set_config('image.confidence', 0.9)
else:
    set_config('general.debug_mode', True)
    set_config('image.confidence', 0.8)
```

### 4. 模板组织

```
templates/
├── wechat/
│   ├── buttons/
│   │   ├── send_button.png
│   │   └── cancel_button.png
│   ├── groups/
│   │   └── group_item.png
│   └── interface/
│       └── contact_list.png
└── common/
    ├── ok_button.png
    └── close_button.png
```

## 性能优化

### 1. 模板缓存

```python
# 模板会自动缓存，避免重复加载
# 如需清理缓存：
template_manager.template_cache.clear()
```

### 2. 配置调优

```python
# 根据实际情况调整超时和重试
set_config('general.default_timeout', 5.0)
set_config('general.retry_count', 3)
set_config('mouse.move_duration', 0.3)
```

### 3. 批量操作

```python
# 使用批量操作提高效率
from core.mouse_helpers import batch_click

positions = [(100, 100), (200, 200), (300, 300)]
batch_click(positions, delay=0.2, randomize_delay=True)
```

## 迁移指南

### 从旧API迁移到新API

| 旧API | 新API |
|-------|-------|
| `wechat_auto.find_and_click_button()` | `find_and_click()` |
| `wechat_auto.operation_interface.locate_template()` | `find_template_centers()` |
| `result.success` | 异常处理 |
| `config.get('section.key')` | `get_config('section.key')` |

### 迁移步骤

1. **更新导入语句**
   ```python
   # 旧
   from workflows.wechat.wechat_half_auto import WechatHalfAuto
   
   # 新
   from workflows.wechat.wechat_simple import WechatWorkflow
   ```

2. **简化错误处理**
   ```python
   # 旧
   result = operation()
   if not result.success:
       handle_error(result.message)
   
   # 新
   try:
       operation()
   except OperationError as e:
       handle_error(str(e))
   ```

3. **更新配置访问**
   ```python
   # 旧
   config = load_config()
   value = config['section']['key']
   
   # 新
   value = get_config('section.key', default_value)
   ```

## 常见问题

### Q: 如何启用调试模式？
A: 在创建工作流时设置 `debug_mode=True`，或通过配置设置全局调试模式。

### Q: 模板匹配失败怎么办？
A: 使用 `debug_template_match()` 可视化调试，或 `batch_confidence_test()` 测试最佳置信度。

### Q: 如何处理不同分辨率的屏幕？
A: 为不同分辨率准备对应的模板文件，使用模板管理器进行分组管理。

### Q: 配置修改后如何生效？
A: 运行时配置修改立即生效，文件配置需要重启程序或调用 `reload_settings()`。

## 技术支持

如遇到问题，请检查：

1. **日志文件** - 查看 `logs/` 目录下的日志文件
2. **配置文件** - 检查 `config/settings.yaml` 配置是否正确
3. **模板文件** - 确认模板文件存在且格式正确
4. **环境变量** - 检查相关环境变量设置

更多示例请参考 `examples/wechat_workflow_examples.py` 文件。