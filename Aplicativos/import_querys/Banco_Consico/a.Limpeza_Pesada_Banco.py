"""
Limpeza_Pesada_Banco.py
-----------------------
Script para enxugar o volume de dados das tabelas oficiais (.txt) no ERP Consinco.
Mantém intacto o cabeçalho e as 5 primeiras linhas de dados (total de até 6 linhas),
eliminando o excedente e reduzindo drasticamente o tamanho dos arquivos.

Filtro:
  - Aplica-se a arquivos .txt que contenham underline (_) no nome.
  - Ignora estritamente tabelas de dicionário/arquitetura:
      * TABELAS_CONSICO_OFICIAIS.txt
      * TODAS_COLUNAS_CONSICO_OFICIAIS.txt
"""

import os
import sys
from pathlib import Path

# Garante suporte adequado a UTF-8 no console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Arquivos que NUNCA devem ser limpos / reduzidos (Dicionários Oficiais)
ARQUIVOS_IGNORADOS = {
    "TABELAS_CONSICO_OFICIAIS.txt",
    "TODAS_COLUNAS_CONSICO_OFICIAIS.txt",
}


def formatar_tamanho(bytes_size: int) -> str:
    """Formata o tamanho em bytes para KB ou MB amigável."""
    if bytes_size >= 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    elif bytes_size >= 1024:
        return f"{bytes_size / 1024:.2f} KB"
    return f"{bytes_size} bytes"


def processar_arquivo(caminho_arquivo: Path) -> dict:
    """
    Lê o arquivo, mantém o cabeçalho e as 5 primeiras linhas de dados (até 6 linhas),
    e sobrescreve o arquivo mantendo a estrutura binária/codificação original intacta.
    """
    tamanho_antes = caminho_arquivo.stat().st_size
    
    # Conta o total de linhas antes
    total_linhas_antes = 0
    with open(caminho_arquivo, "rb") as f:
        for _ in f:
            total_linhas_antes += 1

    # Lê até 6 linhas (1 cabeçalho + 5 linhas de dados)
    linhas_mantidas = []
    with open(caminho_arquivo, "rb") as f:
        for _ in range(6):
            linha = f.readline()
            if not linha:
                break
            linhas_mantidas.append(linha)

    # Garante que a última linha tenha quebra de linha se necessário
    if linhas_mantidas and not linhas_mantidas[-1].endswith((b"\n", b"\r")):
        linhas_mantidas[-1] = linhas_mantidas[-1] + b"\n"

    # Sobrescreve o arquivo com as linhas preservadas
    with open(caminho_arquivo, "wb") as f:
        f.writelines(linhas_mantidas)

    tamanho_depois = caminho_arquivo.stat().st_size
    total_linhas_depois = len(linhas_mantidas)

    return {
        "arquivo": caminho_arquivo.name,
        "linhas_antes": total_linhas_antes,
        "linhas_depois": total_linhas_depois,
        "tamanho_antes": tamanho_antes,
        "tamanho_depois": tamanho_depois,
        "economia_bytes": tamanho_antes - tamanho_depois,
    }


def main():
    diretorio_atual = Path(__file__).resolve().parent
    print("=" * 80)
    print("🧹 LIMPEZA PESADA DE BANCO - ERP CONSINCO")
    print(f"📁 Diretório: {diretorio_atual}")
    print("🎯 Alvo: Arquivos .txt contendo '_' no nome")
    print(f"🛡️ Ignorando dicionários: {', '.join(sorted(ARQUIVOS_IGNORADOS))}")
    print("📋 Regra: Manter 1 cabeçalho + 5 primeiras linhas de dados (máx. 6 linhas)")
    print("=" * 80)

    # Identifica os arquivos alvo excluindo os ignorados
    arquivos_alvo = [
        f for f in diretorio_atual.glob("*.txt")
        if "_" in f.name and f.is_file() and f.name not in ARQUIVOS_IGNORADOS
    ]
    arquivos_alvo.sort(key=lambda x: x.name)

    if not arquivos_alvo:
        print("⚠️ Nenhum arquivo .txt para processamento encontrado.")
        return

    print(f"\n🔍 Encontrados {len(arquivos_alvo)} arquivos para processamento.\n")
    print(f"{'Arquivo':<35} | {'Linhas':<14} | {'Tamanho Antes':<14} | {'Tamanho Depois':<14}")
    print("-" * 84)

    total_bytes_antes = 0
    total_bytes_depois = 0
    resultados = []

    for arq in arquivos_alvo:
        try:
            res = processar_arquivo(arq)
            resultados.append(res)
            total_bytes_antes += res["tamanho_antes"]
            total_bytes_depois += res["tamanho_depois"]

            linhas_str = f"{res['linhas_antes']} -> {res['linhas_depois']}"
            tam_antes_str = formatar_tamanho(res["tamanho_antes"])
            tam_depois_str = formatar_tamanho(res["tamanho_depois"])

            print(f"{res['arquivo']:<35} | {linhas_str:<14} | {tam_antes_str:<14} | {tam_depois_str:<14}")
        except Exception as e:
            print(f"❌ Erro ao processar {arq.name}: {e}")

    economia_total = total_bytes_antes - total_bytes_depois
    percentual_economia = (economia_total / total_bytes_antes * 100) if total_bytes_antes > 0 else 0

    print("=" * 84)
    print("📊 RESUMO GERAL DA LIMPEZA")
    print(f"📦 Total de arquivos processados : {len(resultados)}")
    print(f"🛡️ Dicionários preservados       : {len(ARQUIVOS_IGNORADOS)}")
    print(f"💾 Volume anterior               : {formatar_tamanho(total_bytes_antes)}")
    print(f"✨ Volume atual (enxuto)          : {formatar_tamanho(total_bytes_depois)}")
    print(f"📉 Economia de espaço            : {formatar_tamanho(economia_total)} ({percentual_economia:.2f}%)")
    print("=" * 84)
    print("✅ Operação concluída com sucesso! Tabelas reduzidas e dicionários protegidos.")


if __name__ == "__main__":
    main()
