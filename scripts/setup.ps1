# setup.ps1 — Instala Python, pip y Playwright para el proyecto Carne
# Ejecutar desde la carpeta del proyecto:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Setup: Carne Scraper" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Verificar / instalar Python ───────────────────────────────────
Write-Host "[1/4] Verificando Python..." -ForegroundColor Yellow

$python = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(\d+)") {
            $minor = [int]$Matches[1]
            if ($minor -ge 9) {
                $python = $cmd
                Write-Host "      OK — $ver" -ForegroundColor Green
                break
            } else {
                Write-Host "      Python $ver encontrado pero se requiere 3.9+." -ForegroundColor DarkYellow
            }
        }
    } catch { }
}

if (-not $python) {
    Write-Host "      Python 3.9+ no encontrado. Instalando via winget..." -ForegroundColor Yellow
    try {
        winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        # Refrescar PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path","User")
        $python = "python"
        Write-Host "      Python instalado correctamente." -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "  ERROR: No se pudo instalar Python automaticamente." -ForegroundColor Red
        Write-Host "  Descargalo manualmente desde: https://www.python.org/downloads/" -ForegroundColor Red
        Write-Host "  Asegurate de marcar 'Add Python to PATH' durante la instalacion." -ForegroundColor Red
        Write-Host ""
        Read-Host "Presiona Enter para salir"
        exit 1
    }
}

# ── 2. Actualizar pip ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/4] Actualizando pip..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip --quiet
Write-Host "      pip listo." -ForegroundColor Green

# ── 3. Instalar dependencias del proyecto ────────────────────────────
Write-Host ""
Write-Host "[3/4] Instalando dependencias (requirements.txt)..." -ForegroundColor Yellow
Set-Location $ProjectDir
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR instalando dependencias." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "      Dependencias instaladas." -ForegroundColor Green

# ── 4. Instalar navegador Chromium para Playwright ───────────────────
Write-Host ""
Write-Host "[4/4] Instalando Chromium para Playwright..." -ForegroundColor Yellow
& $python -m playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR instalando Chromium." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}
Write-Host "      Chromium instalado." -ForegroundColor Green

# ── Listo ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Instalacion completada exitosamente!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Para iniciar el monitor ejecuta:" -ForegroundColor Cyan
Write-Host "    python run.py" -ForegroundColor White
Write-Host ""
Write-Host "  Luego abre en tu browser:" -ForegroundColor Cyan
Write-Host "    http://localhost:8000" -ForegroundColor White
Write-Host ""
Read-Host "Presiona Enter para salir"
