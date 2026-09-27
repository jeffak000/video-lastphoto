param([switch]$Uninstall)
$exts = @("mp4","mov","mkv","avi","flv","webm","m4v","wmv","ts")
$root = $PSScriptRoot
$log = Join-Path $root "install_log.txt"

if ($Uninstall) {
    foreach ($e in $exts) {
        $key = "HKCU:\Software\Classes\SystemFileAssociations\.$e\shell\ExtractTailFrame"
        if (Test-Path $key) { Remove-Item -Path $key -Recurse -Force }
    }
    "右键菜单已卸载 $(Get-Date)" | Out-File $log -Encoding utf8
    Write-Host "右键菜单已卸载"
    exit
}

$cmd = "`"$PSScriptRoot\extract_tail.bat`" `"%1`""
foreach ($e in $exts) {
    $key = "HKCU:\Software\Classes\SystemFileAssociations\.$e\shell\ExtractTailFrame"
    if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
    New-ItemProperty -Path $key -Name "(default)" -Value "提取尾帧高清图" -PropertyType String -Force | Out-Null
    $cmdKey = Join-Path $key "command"
    if (-not (Test-Path $cmdKey)) { New-Item -Path $cmdKey -Force | Out-Null }
    New-ItemProperty -Path $cmdKey -Name "(default)" -Value $cmd -PropertyType String -Force | Out-Null
}
"右键菜单安装完成 $(Get-Date)`n脚本: $script`n命令: $cmd" | Out-File $log -Encoding utf8
Write-Host "右键菜单安装完成"
