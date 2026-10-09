param(
    [string]$Python = 'python',
    [string]$VenvDir = '.venv310'
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
# 拒絕所有既有目標，不刪除或重建使用者環境。環境管理工具固定為 uv。
if (Test-Path -LiteralPath $VenvDir) { throw "目標已存在，保留原環境：$VenvDir" }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "需要先安裝 uv：https://docs.astral.sh/uv/getting-started/installation/" }
function Invoke-Checked([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "安裝指令失敗，exit=$LASTEXITCODE；保留已建立檔案供診斷" }
}
Invoke-Checked $Python @('-c', 'import sys; assert sys.version_info[:2] == (3, 10), "正式安裝要求 Python 3.10.x"')
Invoke-Checked uv @('venv', '--seed', '--python', $Python, $VenvDir)
$VenvPython = Join-Path $VenvDir 'Scripts/python.exe'
Invoke-Checked uv @('pip', 'install', '--python', $VenvPython, '-c', 'runtime-constraints.txt', 'pip', 'setuptools', 'wheel')
Invoke-Checked uv @('pip', 'install', '--python', $VenvPython, '--no-build-isolation', '-c', 'runtime-constraints.txt', '.')
Invoke-Checked $VenvPython @('-m', 'pip', 'check')
Invoke-Checked $VenvPython @('-m', 'core.runtime_environment')
