#Requires -RunAsAdministrator

$backupDir = "$env:USERPROFILE\Desktop\WSL_Registry_Backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$backupFile = "$backupDir\WSL_Installer_Keys.reg"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  WSL MSI 强制移除工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "===== 搜索所有相关注册表项 =====" -ForegroundColor Yellow

$foundKeys = @()
$searchedPaths = @()

# 搜索 Installer\Products
$possibleProductsPaths = @(
    "HKLM:\SOFTWARE\Classes\Installer\Products",
    "HKCR:\Installer\Products",
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\Products"
)

foreach ($pp in $possibleProductsPaths) {
    if (Test-Path $pp) {
        $searchedPaths += $pp
        $productKeys = Get-ChildItem $pp -ErrorAction SilentlyContinue
        foreach ($key in $productKeys) {
            try {
                $props = Get-ItemProperty -Path $key.PSPath -ErrorAction SilentlyContinue
                if ($props.ProductName -like "*Windows Subsystem for Linux*" -or $props.ProductName -like "*WSL*") {
                    Write-Host "  🎯 Installer: $($key.PSChildName) -> $($props.ProductName)" -ForegroundColor Green
                    $foundKeys += $key.PSPath
                }
            } catch {}
        }
    }
}

# 搜索 Uninstall
$uninstallPaths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
)

foreach ($upath in $uninstallPaths) {
    if (Test-Path $upath) {
        $searchedPaths += $upath
        $items = Get-ChildItem $upath -ErrorAction SilentlyContinue
        foreach ($item in $items) {
            try {
                $props = Get-ItemProperty -Path $item.PSPath -ErrorAction SilentlyContinue
                if ($props.DisplayName -like "*Windows Subsystem for Linux*" -or $props.DisplayName -like "*WSL*") {
                    Write-Host "  🎯 Uninstall: $($item.PSChildName) -> $($props.DisplayName)" -ForegroundColor Green
                    $foundKeys += $item.PSPath
                }
            } catch {}
        }
    }
}

if ($foundKeys.Count -eq 0) {
    Write-Host "  ⚠️ 未找到匹配的注册表项" -ForegroundColor Yellow
    Write-Host "  已搜索:" -ForegroundColor Gray
    foreach ($p in $searchedPaths) { Write-Host "    - $p" -ForegroundColor Gray }
} else {
    Write-Host ""
    Write-Host "===== 备份并删除 ===== 找到 $($foundKeys.Count) 个 =====" -ForegroundColor Yellow

    foreach ($key in $foundKeys) {
        $regPath = $key -replace '^HKLM:\\', 'HKEY_LOCAL_MACHINE\'
        $regPath = $regPath -replace '^HKCR:\\', 'HKEY_CLASSES_ROOT\'
        try {
            $null = cmd /c "reg export `"$regPath`" `"$backupFile`" /append 2>&1"
            Remove-Item -Path $key -Recurse -Force -ErrorAction Stop
            Write-Host "  ✅ 已删除: $regPath" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ 删除失败: $regPath - $_" -ForegroundColor Red
        }
    }
    Write-Host "  ℹ️ 备份: $backupFile" -ForegroundColor Gray
}

Write-Host ""
Write-Host "===== 验证 =====" -ForegroundColor Yellow
$remaining = Get-WmiObject -Class Win32_Product -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*Windows Subsystem for Linux*" }
if ($remaining) {
    Write-Host "  ⚠️ 仍有残留: $($remaining.Name) v$($remaining.Version)" -ForegroundColor Yellow
} else {
    Write-Host "  ✅ WMI 中已无残留" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  完成！请重启电脑后下载安装最新版：" -ForegroundColor Cyan
Write-Host "  https://github.com/microsoft/WSL/releases/tag/2.7.10" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
pause
