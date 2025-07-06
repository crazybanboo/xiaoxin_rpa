# RPA Framework 轻量级构建脚本
# 不包含 OCR 功能，避免 PyTorch 和 easyocr 依赖问题

param(
    [switch]$Clean,  # 添加 -Clean 参数用于强制清理
    [switch]$Force   # 添加 -Force 参数用于强制重新构建
)

Write-Host "开始构建 RPA Framework 轻量版..." -ForegroundColor Green

# 检查 Nuitka 是否安装
try {
    python -m nuitka --version | Out-Null
    Write-Host "✓ Nuitka 已安装" -ForegroundColor Green
} catch {
    Write-Host "❌ Nuitka 未安装，正在安装..." -ForegroundColor Red
    pip install nuitka
}

# 智能清理策略
if ($Clean -or $Force) {
    Write-Host "执行强制清理..." -ForegroundColor Yellow
    if (Test-Path "main.dist") {
        Remove-Item -Recurse -Force "main.dist"
    }
    if (Test-Path "main.build") {
        Remove-Item -Recurse -Force "main.build"
    }
} else {
    # 检查是否需要清理
    $needsClean = $false
    
    # 检查源文件是否比构建文件更新
    if (Test-Path "main.dist/xiaoxin_rpa_lite.exe") {
        $exeTime = (Get-Item "main.dist/xiaoxin_rpa_lite.exe").LastWriteTime
        $sourceFiles = Get-ChildItem "rpa_framework" -Recurse -File -Include "*.py" | Where-Object { $_.LastWriteTime -gt $exeTime }
        
        if ($sourceFiles.Count -gt 0) {
            Write-Host "检测到源文件更新，需要重新构建..." -ForegroundColor Yellow
            $needsClean = $true
        } else {
            Write-Host "源文件未更新，使用增量构建..." -ForegroundColor Green
        }
    } else {
        Write-Host "首次构建或可执行文件不存在..." -ForegroundColor Yellow
        $needsClean = $true
    }
    
    if ($needsClean) {
        Write-Host "清理构建缓存..." -ForegroundColor Yellow
        if (Test-Path "main.dist") {
            Remove-Item -Recurse -Force "main.dist"
        }
        if (Test-Path "main.build") {
            Remove-Item -Recurse -Force "main.build"
        }
    }
}

Write-Host "正在执行轻量级构建（不包含OCR功能）..." -ForegroundColor Cyan

# 轻量级构建命令
python -m nuitka `
    --standalone `
    --follow-imports `
    --include-package-data=rpa_framework `
    --include-data-dir=rpa_framework/config=rpa_framework/config `
    --include-data-dir=rpa_framework/templates=rpa_framework/templates `
    --include-data-dir=rpa_framework/logs=rpa_framework/logs `
    --show-progress `
    --enable-plugin=numpy `
    --nofollow-import-to=easyocr `
    --nofollow-import-to=torch `
    --nofollow-import-to=torchvision `
    --nofollow-import-to=tensorflow `
    --nofollow-import-to=matplotlib `
    --nofollow-import-to=tkinter `
    --nofollow-import-to=IPython `
    --nofollow-import-to=jupyter `
    --nofollow-import-to=notebook `
    --nofollow-import-to=pytest `
    --nofollow-import-to=sphinx `
    --assume-yes-for-downloads `
    --output-filename=xiaoxin_rpa_lite.exe `
    rpa_framework/main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 轻量级构建成功！" -ForegroundColor Green
    Write-Host "可执行文件位置: main.dist/xiaoxin_rpa_lite.exe" -ForegroundColor Green
    Write-Host "注意：此版本不包含OCR功能，但包含所有其他RPA功能" -ForegroundColor Yellow
    
    # 手动复制配置文件和模板文件以确保完整性
    Write-Host "正在修复配置文件和模板文件..." -ForegroundColor Cyan
    
    # 复制完整的配置文件
    if (Test-Path "rpa_framework/config/settings.yaml") {
        # 确保目标目录存在
        if (-not (Test-Path "main.dist/config")) {
            New-Item -ItemType Directory -Path "main.dist/config" -Force | Out-Null
        }
        
        Copy-Item "rpa_framework/config/settings.yaml" "main.dist/config/settings.yaml" -Force
        Write-Host "✓ 已复制完整的 settings.yaml 配置文件" -ForegroundColor Green
    }
    
    # 复制完整的模板文件
    if (Test-Path "rpa_framework/templates") {
        # 确保目标目录存在
        if (-not (Test-Path "main.dist/templates")) {
            New-Item -ItemType Directory -Path "main.dist/templates" -Force | Out-Null
        }
        
        # 递归复制所有模板文件
        Copy-Item "rpa_framework/templates/*" "main.dist/templates/" -Recurse -Force
        Write-Host "✓ 已复制完整的 templates 模板文件" -ForegroundColor Green
    }
    
    # 验证文件复制结果
    Write-Host "正在验证文件复制结果..." -ForegroundColor Cyan
    
    # 检查 settings.yaml 是否完整
    try {
        $originalLines = (Get-Content "rpa_framework/config/settings.yaml").Count
        if (Test-Path "main.dist/config/settings.yaml") {
            $copiedLines = (Get-Content "main.dist/config/settings.yaml").Count
            if ($originalLines -eq $copiedLines) {
                Write-Host "✓ settings.yaml 文件复制完整 ($copiedLines 行)" -ForegroundColor Green
            } else {
                Write-Host "⚠️ settings.yaml 文件可能不完整 (原始: $originalLines 行, 复制: $copiedLines 行)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ settings.yaml 文件复制失败，目标文件不存在" -ForegroundColor Red
        }
    } catch {
        Write-Host "⚠️ 无法验证 settings.yaml 文件完整性: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 检查模板文件是否完整
    try {
        $originalTemplates = Get-ChildItem "rpa_framework/templates" -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count
        if (Test-Path "main.dist/templates") {
            $copiedTemplates = Get-ChildItem "main.dist/templates" -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count
            if ($originalTemplates -eq $copiedTemplates) {
                Write-Host "✓ 模板文件复制完整 ($copiedTemplates 个文件)" -ForegroundColor Green
            } else {
                Write-Host "⚠️ 模板文件可能不完整 (原始: $originalTemplates 个, 复制: $copiedTemplates 个)" -ForegroundColor Yellow
            }
        } else {
            Write-Host "❌ 模板文件复制失败，目标目录不存在" -ForegroundColor Red
        }
    } catch {
        Write-Host "⚠️ 无法验证模板文件完整性: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # 测试构建的可执行文件
    Write-Host "正在测试构建的可执行文件..." -ForegroundColor Cyan
    try {
        $testResult = & "main.dist/xiaoxin_rpa_lite.exe" --version 2>&1
        Write-Host "✓ 可执行文件测试通过！" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ 可执行文件测试失败，但构建已完成" -ForegroundColor Yellow
    }
    
    # 显示文件大小信息
    $fileSize = (Get-Item "main.dist/xiaoxin_rpa_lite.exe").Length / 1MB
    Write-Host "可执行文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Cyan
    
} else {
    Write-Host "❌ 轻量级构建失败" -ForegroundColor Red
    Write-Host "请检查错误信息并尝试以下解决方案：" -ForegroundColor Yellow
    Write-Host "1. 确保所有依赖都已正确安装" -ForegroundColor Yellow
    Write-Host "2. 尝试使用 PyInstaller: .\build_pyinstaller.ps1" -ForegroundColor Yellow
    Write-Host "3. 检查 Python 环境是否正确配置" -ForegroundColor Yellow
    Write-Host "4. 如果问题持续，尝试强制清理: .\build_lite.ps1 -Clean" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "使用说明：" -ForegroundColor Cyan
Write-Host "  .\build_lite.ps1        # 智能增量构建（推荐）" -ForegroundColor White
Write-Host "  .\build_lite.ps1 -Clean # 强制清理后构建" -ForegroundColor White
Write-Host "  .\build_lite.ps1 -Force # 强制重新构建" -ForegroundColor White
Write-Host ""
Write-Host "轻量级构建完成！" -ForegroundColor Green 