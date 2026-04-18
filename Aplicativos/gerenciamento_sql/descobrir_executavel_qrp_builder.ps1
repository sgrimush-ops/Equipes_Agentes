$processos = Get-CimInstance Win32_Process |
  Where-Object {
    $_.Name -match 'gupta|report|builder|sqlw|team|opentext|notepad\+\+'
    -or $_.CommandLine -match 'QRP|Gupta|Report Builder|OpenText|RelABCCompradorUltCompraCD|RelProdlojaComp'
  } |
  Select-Object Name, ProcessId, ExecutablePath, CommandLine

if (-not $processos) {
  Write-Output 'Nenhum processo candidato ao editor QRP foi encontrado.'
  Write-Output 'Abra o arquivo .QRP no OpenText Gupta Report Builder e execute este script novamente.'
  exit 1
}

$processos | Format-List | Out-String | Write-Output