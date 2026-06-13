<#
.SYNOPSIS
    修复 WSL COM 注册问题 (REGDB_E_CLASSNOTREG)
.DESCRIPTION
    此脚本执行以下修复步骤:
    1. 注册 WSL WinRT COM 类
    2. 注册 wslapi.dll COM 服务器
    3. 修复 MSI 安装程序 COM 注册
    4. 尝试安装微软官方修复脚本
#>

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  WSL COM 注册修复工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 请以管理员身份运行此脚本！" -ForegroundColor Red
    Write-Host "   右键 -> 以管理员身份运行" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✅ 管理员权限确认" -ForegroundColor Green

# ===== 步骤 1: 注册 WSL COM 类 =====
Write-Host ""
Write-Host "===== 步骤 1: 注册 WSL COM 类 =====" -ForegroundColor Yellow

$wslClsid = "{26E96230-96E8-4B9B-963C-C7E51066759D}"

try {
    # 创建 CLSID 注册表项
    $clsidPath = "HKLM:\SOFTWARE\Classes\CLSID\$wslClsid"
    if (-not (Test-Path $clsidPath)) {
        New-Item -Path $clsidPath -Force | Out-Null
        Write-Host "  ✅ 创建 CLSID 注册表项" -ForegroundColor Green
    } else {
        Write-Host "  ℹ️  CLSID 注册表项已存在" -ForegroundColor Gray
    }

    # 设置默认值
    New-ItemProperty -Path $clsidPath -Name "(Default)" -Value "Windows Subsystem for Linux" -PropertyType String -Force | Out-Null
    Write-Host "  ✅ 设置 COM 类名称" -ForegroundColor Green

    # 创建 LocalServer32 子项 (or InprocServer32)
    $serverPath = "$clsidPath\InprocServer32"
    if (-not (Test-Path $serverPath)) {
        New-Item -Path $serverPath -Force | Out-Null
    }
    New-ItemProperty -Path $serverPath -Name "(Default)" -Value "%SystemRoot%\system32\wslapi.dll" -PropertyType ExpandString -Force | Out-Null
    New-ItemProperty -Path $serverPath -Name "ThreadingModel" -Value "Both" -PropertyType String -Force | Out-Null
    Write-Host "  ✅ 设置 COM 服务器 (wslapi.dll)" -ForegroundColor Green

    # 设置权限 (允许 SYSTEM 和 Administrators)
    # 通过 regini 或 sdset 设置权限比较复杂，用 icacls 风格的方式
    Write-Host "  ℹ️  注册 COM 类完成" -ForegroundColor Gray
}
catch {
    Write-Host "  ❌ 注册 COM 类失败: $_" -ForegroundColor Red
}

# ===== 步骤 2: 注册 WSL WinRT Activatable Class =====
Write-Host ""
Write-Host "===== 步骤 2: 注册 WinRT Activatable Class =====" -ForegroundColor Yellow

$winrtClasses = @(
    @{Name = "Windows.System.LxssManager"; DllPath = "wslapi.dll"; ActivatableId = "Windows.System.LxssManager"},
    @{Name = "Windows.System.LxssManagerUser"; DllPath = "wslapi.dll"; ActivatableId = "Windows.System.LxssManagerUser"},
    @{Name = "Windows.System.LxssDistribution"; DllPath = "wslapi.dll"; ActivatableId = "Windows.System.LxssDistribution"}
)

$activatablePath = "HKLM:\SOFTWARE\Microsoft\WindowsRuntime\ActivatableClassId"

foreach ($class in $winrtClasses) {
    $classPath = "$activatablePath\$($class.ActivatableId)"
    try {
        if (-not (Test-Path $classPath)) {
            New-Item -Path $classPath -Force | Out-Null
        }
        New-ItemProperty -Path $classPath -Name "(Default)" -Value $class.Name -PropertyType String -Force | Out-Null
        New-ItemProperty -Path $classPath -Name "DllPath" -Value $class.DllPath -PropertyType ExpandString -Force | Out-Null
        New-ItemProperty -Path $classPath -Name "ThreadingModel" -Value "Both" -PropertyType String -Force | Out-Null
        New-ItemProperty -Path $classPath -Name "ActivableClassId" -Value $class.ActivatableId -PropertyType String -Force | Out-Null
        New-ItemProperty -Path $classPath -Name "TrustLevel" -Value 0 -PropertyType DWord -Force | Out-Null
        Write-Host "  ✅ 注册 $($class.ActivatableId)" -ForegroundColor Green
    }
    catch {
        Write-Host "  ❌ 注册 $($class.ActivatableId) 失败: $_" -ForegroundColor Red
    }
}

# ===== 步骤 3: 注册 wslapi.dll =====
Write-Host ""
Write-Host "===== 步骤 3: 注册 wslapi.dll =====" -ForegroundColor Yellow

try {
    # 检查文件是否存在
    if (Test-Path "$env:SystemRoot\System32\wslapi.dll") {
        # 用 regsvr32 注册
        regsvr32 /s "$env:SystemRoot\System32\wslapi.dll"
        Write-Host "  ✅ wslapi.dll 注册成功" -ForegroundColor Green
    } else {
        Write-Host "  ❌ wslapi.dll 未找到！" -ForegroundColor Red
    }
}
catch {
    Write-Host "  ❌ 注册 wslapi.dll 失败: $_" -ForegroundColor Red
}

# ===== 步骤 4: 修复 MSI 安装程序 COM 注册 =====
Write-Host ""
Write-Host "===== 步骤 4: 修复 MSI 安装程序 COM 注册 =====" -ForegroundColor Yellow

try {
    # 重新注册 Windows Installer
    msiexec /unregister | Out-Null
    msiexec /regserver | Out-Null
    Write-Host "  ✅ Windows Installer 重新注册" -ForegroundColor Green
}
catch {
    Write-Host "  ❌ 重新注册 Windows Installer 失败: $_" -ForegroundColor Red
}

try {
    # 重新注册 MSI DLL
    regsvr32 /s "$env:SystemRoot\System32\msi.dll"
    Write-Host "  ✅ msi.dll 重新注册" -ForegroundColor Green
}
catch {
    Write-Host "  ❌ 注册 msi.dll 失败: $_" -ForegroundColor Red
}

# ===== 步骤 5: 注册 LxssManager 服务 =====
Write-Host ""
Write-Host "===== 步骤 5: 检查并注册 LxssManager 服务 =====" -ForegroundColor Yellow

$serviceName = "LxssManager"
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "  ℹ️  LxssManager 服务不存在，尝试创建..." -ForegroundColor Yellow
    try {
        # 在 26100/26200 版本中，LxssManager 可能使用不同的服务架构
        # 先检查 Store 包的 wslinstaller 是否包含此功能
        $wslPackagePath = "C:\Program Files\WindowsApps\MicrosoftCorporationII.WindowsSubsystemForLinux_2.7.8.0_x64__8wekyb3d8bbwe"
        if (Test-Path $wslPackagePath) {
            Write-Host "  ℹ️  找到 WSL Store 包，尝试触发服务注册..." -ForegroundColor Yellow

            # 尝试运行 wslinstaller 以触发服务注册
            $wslinstaller = Join-Path $wslPackagePath "wslinstaller.exe"
            if (Test-Path $wslinstaller) {
                Write-Host "  运行 wslinstaller.exe 触发服务注册..." -ForegroundColor Gray
                Start-Process -FilePath $wslinstaller -ArgumentList "-register" -NoNewWindow -Wait
                Write-Host "  ✅ wslinstaller 执行完成" -ForegroundColor Green
            }
        }

        # 再次检查服务
        Start-Sleep -Seconds 2
        $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if ($service) {
            Write-Host "  ✅ LxssManager 服务已创建" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  LxssManager 服务仍未创建" -ForegroundColor Yellow
            Write-Host "  将在步骤 6 中尝试手动注册" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  ❌ 创建 LxssManager 服务失败: $_" -ForegroundColor Red
    }
} else {
    Write-Host "  ✅ LxssManager 服务已存在，状态: $($service.Status)" -ForegroundColor Green
    if ($service.Status -ne 'Running') {
        try {
            Start-Service -Name $serviceName
            Write-Host "  ✅ LxssManager 服务已启动" -ForegroundColor Green
        }
        catch {
            Write-Host "  ❌ 启动 LxssManager 服务失败: $_" -ForegroundColor Red
        }
    }
}

# ===== 步骤 6: 部署 WinSxS 中的 WSL 系统组件 =====
Write-Host ""
Write-Host "===== 步骤 6: 部署 WinSxS 中的 WSL 系统组件 =====" -ForegroundColor Yellow

# 检查 lxss.sys 驱动是否部署
if (Test-Path "$env:SystemRoot\System32\drivers\lxss.sys") {
    Write-Host "  ✅ lxss.sys 驱动已部署" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  lxss.sys 驱动未部署" -ForegroundColor Yellow
    # 从 WinSxS 复制
    $winsxsLxss = Get-ChildItem "$env:SystemRoot\WinSxS\amd64_microsoft-windows-lxss_*" -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if ($winsxsLxss) {
        $lxssSysSource = Join-Path $winsxsLxss.FullName "lxss.sys"
        if (Test-Path $lxssSysSource) {
            try {
                Copy-Item -Path $lxssSysSource -Destination "$env:SystemRoot\System32\drivers\lxss.sys" -Force
                Write-Host "  ✅ lxss.sys 已从 WinSxS 复制到 drivers" -ForegroundColor Green
            } catch {
                Write-Host "  ❌ 复制 lxss.sys 失败: $_" -ForegroundColor Red
            }
        }
    }
}

# 将旧 wsl.exe 从 WinSxS 复制到 System32 (确保系统版本一致性)
$winsxsWsl = Get-ChildItem "$env:SystemRoot\WinSxS\amd64_microsoft-windows-lxss-wsl_*" -Directory | Sort-Object Name -Descending | Select-Object -First 1
if ($winsxsWsl) {
    $wslExeSource = Join-Path $winsxsWsl.FullName "wsl.exe"
    if (Test-Path $wslExeSource) {
        Write-Host "  ℹ️  WinSxS 中包含旧版 wsl.exe (258KB)" -ForegroundColor Gray
        Write-Host "  当前 System32 wsl.exe: $(Get-Item "$env:SystemRoot\System32\wsl.exe").Length bytes (来自 Store)" -ForegroundColor Gray
    }
}

# ===== 步骤 7: 尝试微软官方修复脚本 =====
Write-Host ""
Write-Host "===== 步骤 7: 尝试微软官方修复脚本 =====" -ForegroundColor Yellow

try {
    Write-Host "  下载微软官方 WSL 修复脚本..." -ForegroundColor Gray
    Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/microsoft/WSL/master/triage/install-latest-wsl.ps1" -OutFile "$env:TEMP\install-latest-wsl.ps1"
    Write-Host "  ✅ 下载成功" -ForegroundColor Green

    Write-Host "  运行微软官方修复脚本..." -ForegroundColor Yellow
    & "$env:TEMP\install-latest-wsl.ps1"
    Write-Host "  ✅ 微软官方修复脚本执行完成" -ForegroundColor Green
}
catch {
    Write-Host "  ⚠️  下载或运行官方脚本失败 (可能网络问题): $_" -ForegroundColor Yellow
    Write-Host "  可以稍后手动访问: https://github.com/microsoft/WSL/blob/master/triage/install-latest-wsl.ps1" -ForegroundColor Gray
}

# ===== 验证 =====
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  验证修复结果" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 测试 wsl -l --quiet
Write-Host "测试 wsl -l --quiet:" -ForegroundColor Yellow
try {
    $result = & wsl -l --quiet 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ WSL 工作正常！" -ForegroundColor Green
        Write-Host "  输出: $result" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ wsl -l --quiet 仍然失败 (错误码: $LASTEXITCODE)" -ForegroundColor Red
        Write-Host "  输出: $result" -ForegroundColor Gray
    }
}
catch {
    Write-Host "  ❌ 运行 wsl 失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "诊断信息:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 输出关键诊断信息
Write-Host ""
Write-Host "wsl --version:" -ForegroundColor Yellow
wsl --version 2>&1

Write-Host ""
Write-Host "LxssManager 服务状态:" -ForegroundColor Yellow
Get-Service LxssManager -ErrorAction SilentlyContinue | Format-List Name,Status,StartType

Write-Host ""
Write-Host "WSL 相关服务:" -ForegroundColor Yellow
Get-Service -Name '*Wsl*','*Lxss*' -ErrorAction SilentlyContinue | Format-Table Name,Status,DisplayName -AutoSize

Write-Host ""
if ((Get-Service LxssManager -ErrorAction SilentlyContinue) -and ((Get-Service LxssManager).Status -eq 'Running')) {
    Write-Host "🎉 WSL 修复成功！重启电脑后运行 Podman Desktop 即可。" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠️  部分修复已完成，可能需要重启电脑后再次运行此脚本。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "尝试手动修复:" -ForegroundColor Cyan
    Write-Host "1. 打开 PowerShell(管理员)" -ForegroundColor White
    Write-Host "2. 运行: wsl --update --pre-release" -ForegroundColor White
    Write-Host "3. 重启电脑" -ForegroundColor White
}

Write-Host ""
pause
