param(
    [int]$Puerto = 8000
)

$conexiones = Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue
if (-not $conexiones) {
    exit 0
}

$pids = $conexiones.OwningProcess | Sort-Object -Unique
foreach ($processId in $pids) {
    try {
        $proceso = Get-Process -Id $processId -ErrorAction Stop
        if ($proceso.ProcessName -match 'python|uvicorn') {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Write-Host "[INFO] Proceso $processId detenido (puerto $Puerto)."
        }
    } catch {
        Write-Host "[AVISO] No se pudo detener el proceso $processId : $_"
    }
}
