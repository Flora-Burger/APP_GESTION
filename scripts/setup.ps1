# Script de configuration initiale pour Windows
$ErrorActionPreference = "Stop"
$Racine = Split-Path -Parent $PSScriptRoot
Set-Location $Racine

$pythonCmd = $null
$candidats = @(
    "python",
    "python3",
    "py",
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
)

foreach ($cmd in $candidats) {
    try {
        $version = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $version -match "Python 3\.(1[1-9]|[2-9][0-9])") {
            $pythonCmd = $cmd
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-Host "Python 3.11+ no encontrado. Instale Python desde https://www.python.org/downloads/"
    exit 1
}

Write-Host "Usando: $pythonCmd"
& $pythonCmd -m venv VFLORA
& ".\VFLORA\Scripts\pip.exe" install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

& ".\VFLORA\Scripts\alembic.exe" upgrade head
& ".\VFLORA\Scripts\python.exe" scripts/seed_donnees.py

Write-Host "Configuracion completada. Ejecute:"
Write-Host "  .\VFLORA\Scripts\Activate.ps1"
Write-Host "  uvicorn backend.app.main:app --reload"
