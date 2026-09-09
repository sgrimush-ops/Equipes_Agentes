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

# Garante suporte a UTF-8 no terminal Windows (prevenindo UnicodeEncodeError com emojis/acentos)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def get_repo_root() -> str:
    """Identifica a raiz real do repositório Git dinamicamente."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    res = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=script_dir,
    )
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return os.path.dirname(script_dir)



REPO = get_repo_root()


def run(cmd: list[str]) -> tuple[int, str, str]:
    """Executa comando git dentro do diretório raiz do repositório (cwd)."""
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", cwd=REPO
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    print(f"📁 Raiz do Repositório Git: {REPO}\n")

    # 1. Verifica alterações locais pendentes
    code, out_status, err_status = run(["git", "status", "--short"])
    has_changes = bool(out_status)

    if has_changes:
        print("=== 📝 Alterações detectadas para commit ===")
        print(out_status)

        msg = f"Atualização automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        print(f"\n💬 Mensagem do Commit: {msg}")

        # git add --all
        code, out, err = run(["git", "add", "--all"])
        if code != 0:
            print(f"❌ Erro no git add:\n{err}")
            sys.exit(code)
        print("✅ git add --all concluído com sucesso.")

        # git commit
        code, out, err = run(["git", "commit", "-m", msg])
        if code != 0:
            print(f"❌ Erro no git commit:\nSTDOUT: {out}\nSTDERR: {err}")
            sys.exit(code)
        print(f"✅ Commit realizado com sucesso:\n{out}")
    else:
        print("ℹ️ Nenhuma alteração pendente para commit local.")

    # 2. Verifica se há commits locais pendentes de envio (ahead)
    code, out_ahead, _ = run(["git", "rev-list", "@{u}..HEAD", "--count"])
    commits_ahead = int(out_ahead) if code == 0 and out_ahead.isdigit() else (1 if has_changes else 0)

    if not has_changes and commits_ahead == 0:
        print("\n🟢 O repositório local já está 100% atualizado e sincronizado com o GitHub.")
        return

    # 3. Executa git push
    print(f"\n🚀 Enviando commits para o GitHub...")
    code, out, err = run(["git", "push"])
    if code != 0:
        print(f"❌ Erro no git push:\n{err or out}")
        print("\n⚠️ O push não foi concluído. Verifique os erros acima.")
        sys.exit(code)

    print(f"✅ Push concluído com sucesso!\n{out or err}")
    print("\n🎉 Commit e Push finalizados com êxito no GitHub!")


if __name__ == "__main__":
    main()
   