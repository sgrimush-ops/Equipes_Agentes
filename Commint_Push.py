"""
Commint_Push.py
---------------
Script para realizar git add (incluindo exclusões), commit e push
no repositório atual, com mensagem informada pelo usuário.
"""

import subprocess
import sys


def run(cmd: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    repo = r"c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes"

    # Mostra status atual
    code, out, err = run(["git", "-C", repo, "status", "--short"])
    if out:
        print("=== Alterações detectadas ===")
        print(out)
    else:
        print("Nenhuma alteração pendente. Nada a commitar.")
        return

    # Solicita mensagem de commit (Enter = usa mensagem padrão)
    from datetime import datetime
    padrao = f"Atualização automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    print()
    msg = input(f"Mensagem do commit [{padrao}]: ").strip()
    if not msg:
        msg = padrao

    # git add -A  (inclui arquivos novos, modificados e deletados)
    code, out, err = run(["git", "-C", repo, "add", "-A"])
    if code != 0:
        print(f"Erro no git add:\n{err}")
        sys.exit(code)
    print("git add -A concluído.")

    # git commit
    code, out, err = run(["git", "-C", repo, "commit", "-m", msg])
    if code != 0:
        print(f"Erro no git commit:\n{err}")
        sys.exit(code)
    print(f"Commit realizado:\n{out}")

    # git push
    code, out, err = run(["git", "-C", repo, "push"])
    if code != 0:
        print(f"Erro no git push:\n{err}")
        sys.exit(code)
    print(f"Push concluído:\n{out or err}")


if __name__ == "__main__":
    main()
