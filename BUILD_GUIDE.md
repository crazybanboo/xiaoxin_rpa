# RPA Framework 构建指南

## 问题说明

原始的 `build.ps1` 脚本在构建时遇到了 PyTorch 和 easyocr 依赖的兼容性问题。错误信息显示：

```
AttributeError: 'dict' object has no attribute 'endswith'
```

这是由于 Nuitka 在处理复杂的深度学习库（如 PyTorch）时的已知问题。

## 解决方案

我们提供了三个构建脚本来解决这个问题：

### 1. build.ps1 - 改进的标准构建脚本

**特点：**
- 包含完整功能（包括 OCR）
- 添加了 PyTorch 插件支持
- 排除了不必要的依赖
- 自动回退到轻量版本

**使用方法：**
```powershell
.\build.ps1
```

### 2. build_lite.ps1 - 轻量级构建脚本 ⭐ 推荐

**特点：**
- 不包含 OCR 功能
- 避免 PyTorch 和 easyocr 依赖问题
- 构建速度快，文件体积小
- 包含所有其他 RPA 功能

**使用方法：**
```powershell
.\build_lite.ps1
```

### 3. build_pyinstaller.ps1 - PyInstaller 备用方案

**特点：**
- 使用 PyInstaller 而非 Nuitka
- 对复杂依赖的兼容性更好
- 包含完整功能
- 作为 Nuitka 失败时的备用方案

**使用方法：**
```powershell
.\build_pyinstaller.ps1
```

## 推荐构建流程

1. **首先尝试轻量级版本**（最稳定）：
   ```powershell
   .\build_lite.ps1
   ```

2. **如果需要 OCR 功能，尝试 PyInstaller**：
   ```powershell
   .\build_pyinstaller.ps1
   ```

3. **最后尝试改进的标准构建**：
   ```powershell
   .\build.ps1
   ```

## 功能对比

| 功能 | build_lite.ps1 | build_pyinstaller.ps1 | build.ps1 |
|------|----------------|------------------------|-----------|
| 鼠标控制 | ✅ | ✅ | ✅ |
| 键盘控制 | ✅ | ✅ | ✅ |
| 图像识别 | ✅ | ✅ | ✅ |
| 窗口操作 | ✅ | ✅ | ✅ |
| OCR 文字识别 | ❌ | ✅ | ✅ |
| 微信自动化 | ✅ | ✅ | ✅ |
| 构建稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 文件大小 | 小 | 大 | 大 |

## 故障排除

### 如果构建失败：

1. **检查 Python 环境**：
   ```powershell
   python --version
   pip list | findstr nuitka
   ```

2. **更新构建工具**：
   ```powershell
   pip install --upgrade nuitka pyinstaller
   ```

3. **清理构建缓存**：
   ```powershell
   Remove-Item -Recurse -Force main.dist, main.build, dist, build -ErrorAction SilentlyContinue
   ```

4. **检查依赖**：
   ```powershell
   pip install -r requirements.txt
   ```

### 如果运行时出错：

1. **检查缺失的文件**：
   - 确保 `rpa_framework/config` 目录存在
   - 确保 `rpa_framework/templates` 目录存在

2. **检查权限**：
   - 以管理员身份运行 PowerShell
   - 确保可执行文件有执行权限

3. **检查系统依赖**：
   - 安装 Visual C++ Redistributable
   - 确保 Windows 系统更新

## 性能优化建议

1. **使用轻量级版本**：如果不需要 OCR 功能，优先使用 `build_lite.ps1`
2. **SSD 存储**：将项目放在 SSD 上可以加快构建速度
3. **关闭杀毒软件**：构建时临时关闭实时保护可以避免误报

## 输出文件说明

- **build_lite.ps1**: `main.dist/xiaoxin_rpa_lite.exe`
- **build_pyinstaller.ps1**: `dist/xiaoxin_rpa/xiaoxin_rpa.exe`
- **build.ps1**: `main.dist/main.exe`

所有构建都会创建一个包含所有依赖的独立目录，可以直接复制到其他机器上运行。 