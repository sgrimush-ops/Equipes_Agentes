Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$credTarget = Join-Path $projectDir "credentials.json"
$downloadsDir = Join-Path $env:USERPROFILE "Downloads"

function Abrir-PaginasGoogleCloud {
    $urls = @(
        "https://console.cloud.google.com/apis/library/gmail.googleapis.com",
        "https://console.cloud.google.com/apis/library/drive.googleapis.com",
        "https://console.cloud.google.com/apis/library/sheets.googleapis.com",
        "https://console.cloud.google.com/apis/library/script.googleapis.com",
        "https://console.cloud.google.com/apis/credentials"
    )

    foreach ($url in $urls) {
        Start-Process $url | Out-Null
    }
}

function Tentar-CopiarCredencialBaixada {
    if (Test-Path $credTarget) {
        return $true
    }

    if (-not (Test-Path $downloadsDir)) {
        return $false
    }

    $arquivoBaixado = Get-ChildItem -Path $downloadsDir -Filter "client_secret*.json" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $arquivoBaixado) {
        return $false
    }

    Copy-Item -Path $arquivoBaixado.FullName -Destination $credTarget -Force
    Write-Host "Credencial copiada automaticamente para: $credTarget"
    return $true
}

Write-Host "Preparando autenticacao OAuth do Gmail..."

$okCredencial = Tentar-CopiarCredencialBaixada

if (-not $okCredencial) {
    Write-Host ""
    Write-Host "Nao encontrei credentials.json e nem client_secret*.json em Downloads."
    Write-Host "Abri as paginas do Google Cloud para voce habilitar APIs e baixar o JSON OAuth Desktop."
    Write-Host "Depois de baixar, execute este mesmo script novamente."
    Write-Host ""

    Abrir-PaginasGoogleCloud
    Start-Process $downloadsDir | Out-Null
    Start-Process $projectDir | Out-Null
    exit 1
}

$pythonExe = "C:/Users/usr/AppData/Local/Programs/Python/Python314/python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$appScript = Join-Path $projectDir "resumo_email.py"

Write-Host "Iniciando app para voce apenas autorizar no navegador..."
& $pythonExe $appScript