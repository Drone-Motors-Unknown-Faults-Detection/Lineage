param([Parameter(Mandatory=$true)][string]$Python310Path)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$runtimeVersion=& $Python310Path -c 'import platform; print(platform.python_version())'
if ($runtimeVersion -ne '3.10.19') { throw "Expected Python3.10.19, got $runtimeVersion" }
if (-not (Test-Path -LiteralPath '.venv310/Scripts/python.exe')) {
    & $Python310Path -m venv .venv310
    if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' }
}
$researchPython=Join-Path $PSScriptRoot '.venv310/Scripts/python.exe'
if ((& $researchPython -c 'import platform; print(platform.python_version())') -ne '3.10.19') { throw 'Existing venv has different Python; refusing overwrite' }
& $researchPython -m pip install -c requirements/constraints-win-py31019.txt numpy pandas scipy scikit-learn hdbscan matplotlib loguru tornado joblib threadpoolctl
if ($LASTEXITCODE -ne 0) { throw 'dependency installation failed' }
& $researchPython -m pip install -e . --no-deps
if ($LASTEXITCODE -ne 0) { throw 'editable installation failed' }
& $researchPython -m pip check
if ($LASTEXITCODE -ne 0) { throw 'dependency check failed' }
$env:PYTHONIOENCODING='utf-8'
$env:MPLCONFIGDIR=Join-Path $PSScriptRoot 'output/fault_type_mplcache'
& $researchPython -m experiments.synchronized_compatibility
if ($LASTEXITCODE -ne 0) { throw 'compatibility checks failed; see saved output' }
