"""
verificar_drivers_updates.py
Verifica a saúde e atualização dos drivers do PC (Windows 10/11) e integra
verificação/atualização de pacotes e utilitários via `winget upgrade --all`.
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def configurar_utf8() -> None:
    """Garante codificação UTF-8 no stdout e stderr no Windows."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def executar_powershell(script: str, timeout: int = 120) -> tuple[int, str, str]:
    """Executa um bloco PowerShell com saída em UTF-8."""
    comando = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "$OutputEncoding = [System.Text.Encoding]::UTF8; "
        f"{script}"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", f"Tempo limite excedido ({timeout}s) ao executar PowerShell."
    except Exception as exc:
        return 1, "", str(exc)


def parse_json_ps(texto: str) -> list[dict[str, Any]]:
    """Converte saída JSON do PowerShell (objeto único, lista ou vazio) em lista."""
    if not texto:
        return []
    dados = json.loads(texto)
    if isinstance(dados, dict):
        return [dados]
    if isinstance(dados, list):
        return dados
    return []


def verificar_dispositivos_com_erro() -> tuple[list[dict[str, Any]], str]:
    """Busca dispositivos com falha no Gerenciador de Dispositivos."""
    script = (
        "Get-CimInstance Win32_PnPEntity | "
        "Where-Object { $_.ConfigManagerErrorCode -ne 0 } | "
        "Select-Object Name, DeviceID, ConfigManagerErrorCode | "
        "ConvertTo-Json -Compress"
    )
    code, out, err = executar_powershell(script, timeout=60)
    if code != 0:
        return [], err or "Falha ao consultar Win32_PnPEntity."
    try:
        return parse_json_ps(out), ""
    except json.JSONDecodeError as exc:
        return [], f"Erro ao interpretar JSON de dispositivos: {exc}"


def listar_drivers_instalados() -> tuple[list[dict[str, Any]], str]:
    """Obtém inventário de drivers assinados instalados via CIM."""
    script = (
        "Get-CimInstance Win32_PnPSignedDriver | "
        "Where-Object { $_.DeviceName } | "
        "Select-Object DeviceName, Manufacturer, DriverVersion, "
        "@{N='DriverDate';E={if($_.DriverDate){$_.DriverDate.ToString('yyyy-MM-dd')}else{'N/A'}}} | "
        "ConvertTo-Json -Compress"
    )
    code, out, err = executar_powershell(script, timeout=90)
    if code != 0:
        return [], err or "Falha ao consultar Win32_PnPSignedDriver."
    try:
        drivers = parse_json_ps(out)
        drivers.sort(key=lambda d: (d.get("DriverDate") == "N/A", d.get("DriverDate") or "9999-99-99"))
        return drivers, ""
    except json.JSONDecodeError as exc:
        return [], f"Erro ao interpretar JSON de drivers: {exc}"


def verificar_updates_drivers_wu() -> tuple[list[dict[str, Any]], str]:
    """Consulta o Windows Update (COM) por atualizações de drivers pendentes."""
    script = (
        "$session = New-Object -ComObject Microsoft.Update.Session; "
        "$searcher = $session.CreateUpdateSearcher(); "
        "$result = $searcher.Search(\"IsInstalled=0 and Type='Driver'\"); "
        "$lista = @(); "
        "foreach ($u in $result.Updates) { "
        "  $lista += [PSCustomObject]@{ "
        "    Title = $u.Title; "
        "    DriverModel = $u.DriverModel; "
        "    DriverManufacturer = $u.DriverManufacturer; "
        "    DriverClass = $u.DriverClass; "
        "    DriverVerDate = if ($u.DriverVerDate) { $u.DriverVerDate.ToString('yyyy-MM-dd') } else { 'N/A' } "
        "  } "
        "}; "
        "$lista | ConvertTo-Json -Compress"
    )
    code, out, err = executar_powershell(script, timeout=180)
    if code != 0:
        return [], err or "Não foi possível consultar o Windows Update (verifique conexão/serviço wuauserv)."
    try:
        return parse_json_ps(out), ""
    except json.JSONDecodeError as exc:
        return [], f"Erro ao interpretar resposta do Windows Update: {exc}"


def winget_disponivel() -> bool:
    """Verifica se o utilitário `winget` está instalado e acessível no PATH."""
    return shutil.which("winget") is not None


def listar_winget_upgrade() -> tuple[int, str]:
    """Executa `winget upgrade` para listar aplicativos e pacotes desatualizados."""
    try:
        proc = subprocess.run(
            ["winget", "upgrade", "--include-unknown"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        saida = (proc.stdout or "").strip()
        if not saida and proc.stderr:
            saida = proc.stderr.strip()
        return proc.returncode, saida
    except Exception as exc:
        return 1, f"Erro ao executar winget upgrade: {exc}"


def executar_winget_upgrade_all() -> int:
    """Executa `winget upgrade --all` exibindo o progresso em tempo real."""
    print("\n>>> Executando: winget upgrade --all --include-unknown --accept-source-agreements --accept-package-agreements")
    proc = subprocess.run(
        [
            "winget",
            "upgrade",
            "--all",
            "--include-unknown",
            "--accept-source-agreements",
            "--accept-package-agreements",
        ]
    )
    return proc.returncode


def formatar_relatorio(
    dispositivos_erro: list[dict[str, Any]],
    erro_disp: str,
    drivers: list[dict[str, Any]],
    erro_drv: str,
    updates_wu: list[dict[str, Any]],
    erro_wu: str,
    winget_ok: bool,
    saida_winget: str,
) -> str:
    """Monta o relatório completo em texto legível."""
    linhas: list[str] = []
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    linhas.append("=" * 72)
    linhas.append(f"VERIFICAÇÃO DE DRIVERS E ATUALIZAÇÕES DO PC - {agora}")
    linhas.append("=" * 72)

    linhas.append("\n[1] DISPOSITIVOS COM ERRO NO GERENCIADOR DE DISPOSITIVOS")
    if erro_disp:
        linhas.append(f"  [!] Aviso: {erro_disp}")
    elif not dispositivos_erro:
        linhas.append("  [OK] Nenhum dispositivo com código de erro encontrado.")
    else:
        for d in dispositivos_erro:
            linhas.append(
                f"  [ERRO {d.get('ConfigManagerErrorCode')}] {d.get('Name')} ({d.get('DeviceID')})"
            )

    linhas.append("\n[2] ATUALIZAÇÕES DE DRIVERS PENDENTES NO WINDOWS UPDATE")
    if erro_wu:
        linhas.append(f"  [!] Não foi possível consultar o Windows Update: {erro_wu}")
    elif not updates_wu:
        linhas.append("  [OK] Nenhuma atualização de driver pendente no Windows Update.")
    else:
        linhas.append(f"  [!] {len(updates_wu)} atualização(ões) de driver disponível(is):")
        for u in updates_wu:
            linhas.append(
                f"    - {u.get('Title')} | Fabricante: {u.get('DriverManufacturer')} | Data: {u.get('DriverVerDate')}"
            )

    linhas.append("\n[3] RESUMO DE DRIVERS INSTALADOS (WIN32_PNPSIGNEDDRIVER)")
    if erro_drv:
        linhas.append(f"  [!] Aviso: {erro_drv}")
    else:
        ano_limite = datetime.now().year - 3
        antigos = [
            d for d in drivers
            if d.get("DriverDate") not in (None, "N/A") and int(str(d["DriverDate"])[:4]) <= ano_limite
        ]
        linhas.append(f"  Total de drivers listados: {len(drivers)}")
        linhas.append(f"  Drivers com data <= {ano_limite} (mais de 3 anos): {len(antigos)}")
        if antigos:
            linhas.append("  Top 15 drivers mais antigos:")
            for d in antigos[:15]:
                linhas.append(
                    f"    - {d.get('DriverDate')} | v{d.get('DriverVersion')} | "
                    f"{d.get('DeviceName')} ({d.get('Manufacturer')})"
                )

    linhas.append("\n[4] VERIFICAÇÃO DE PACOTES VIA WINGET (winget upgrade)")
    if not winget_ok:
        linhas.append("  [!] `winget` não encontrado no PATH deste computador.")
    else:
        linhas.append(saida_winget or "  (Sem saída do winget)")

    return "\n".join(linhas)


def salvar_relatorio_arquivo(conteudo: str) -> Path:
    """Salva o relatório em `logs/relatorio_drivers_<timestamp>.txt`."""
    pasta_logs = Path(__file__).resolve().parent.parent / "logs"
    pasta_logs.mkdir(parents=True, exist_ok=True)
    nome = f"relatorio_drivers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    caminho = pasta_logs / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def main() -> int:
    configurar_utf8()

    parser = argparse.ArgumentParser(
        description="Verifica drivers do Windows (Gerenciador + Windows Update) e atualizações via winget."
    )
    parser.add_argument(
        "--sem-upgrade",
        action="store_true",
        help="Apenas verifica e lista sem executar `winget upgrade --all`.",
    )
    parser.add_argument(
        "--pular-wu",
        action="store_true",
        help="Pula a consulta online de drivers no Windows Update (mais rápido).",
    )
    parser.add_argument(
        "--apenas-resumo",
        action="store_true",
        help="Alias de --sem-upgrade: apenas exibe o resumo sem atualizar.",
    )
    parser.add_argument(
        "--salvar-relatorio",
        action="store_true",
        help="Salva o relatório completo em arquivo .txt na pasta logs/.",
    )
    args = parser.parse_args()

    print("1/4 Verificando dispositivos com erro no Gerenciador de Dispositivos...")
    dispositivos_erro, erro_disp = verificar_dispositivos_com_erro()

    if args.pular_wu:
        updates_wu, erro_wu = [], "Consulta ao Windows Update pulada via --pular-wu."
    else:
        print("2/4 Consultando atualizações de drivers no Windows Update (pode levar alguns segundos)...")
        updates_wu, erro_wu = verificar_updates_drivers_wu()

    print("3/4 Inventariando drivers instalados...")
    drivers, erro_drv = listar_drivers_instalados()

    winget_ok = winget_disponivel()
    saida_winget = ""
    if winget_ok:
        print("4/4 Consultando atualizações disponíveis via winget...")
        _, saida_winget = listar_winget_upgrade()
    else:
        print("4/4 `winget` não disponível no sistema.")

    relatorio = formatar_relatorio(
        dispositivos_erro,
        erro_disp,
        drivers,
        erro_drv,
        updates_wu,
        erro_wu,
        winget_ok,
        saida_winget,
    )
    print("\n" + relatorio)

    if args.salvar_relatorio:
        caminho = salvar_relatorio_arquivo(relatorio)
        print(f"\n[OK] Relatório salvo em: {caminho}")

    if winget_ok and not (args.sem_upgrade or args.apenas_resumo):
        executar_winget_upgrade_all()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
