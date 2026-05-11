"""
Commint_Push.py
---------------
Script para realizar git add (incluindo exclusões), commit e push
no repositório atual. Mensagem automática com data/hora.
"""

import subprocess
import sys
import os
from datetime import datetime


REPO = r"c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes"


def run(cmd: list[str]) -> tuple[int, str, str]:
    """Executa comando git dentro do diretório do repositório (cwd)."""
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", cwd=REPO
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    # Mostra status atual
    code, out, err = run(["git", "status", "--short"])
    if out:
        print("=== Alterações detectadas ===")
        print(out)
    else:
        print("Nenhuma alteração pendente. Nada a commitar.")
        return

    # Mensagem automática com data/hora (sem input)
    msg = f"Atualização automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    print(f"\n📝 Commit: {msg}")

    # git add --all  (inclui novos, modificados E deletados)
    code, out, err = run(["git", "add", "--all"])
    if code != 0:
        print(f"Erro no git add:\n{err}")
        sys.exit(code)
    print("✅ git add --all concluído.")

    # git commit
    code, out, err = run(["git", "commit", "-m", msg])
    if code != 0:
        print(f"Erro no git commit:\n{err}")
        sys.exit(code)
    print(f"✅ Commit realizado:\n{out}")

    # git push
    code, out, err = run(["git", "push"])
    if code != 0:
        print(f"Erro no git push:\n{err}")
        sys.exit(code)
    print(f"✅ Push concluído:\n{out or err}")


if __name__ == "__main__":
    main()
    # limpar terminal
    os.system("cls")
