"""
Commint_Push.py
---------------
Script exclusivo para realizar git add, commit e push
no repositório deste computador (Equipes_Agentes).
Não possui comunicação nem vínculo com nenhum repositório externo.
Mensagem automática com data/hora.
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
    """Identifica a raiz real do repositório Git local dinamicamente."""
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


def run(cmd: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    """Executa comando git dentro da raiz do repositório local."""
    target_cwd = cwd or REPO
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", cwd=target_cwd
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def main():
    print("=" * 60)
    print("   SINCRONIZADOR GIT - REPOSITÓRIO LOCAL EQUIPES_AGENTES")
    print("=" * 60)
    print(f"📁 Raiz do Repositório: {REPO}\n")
    msg = f"Atualização automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    # 1. Verifica alterações locais pendentes na raiz
    code, out_status, err_status = run(["git", "status", "--short"])
    has_changes = bool(out_status)

    if has_changes:
        print("=== 📝 Alterações detectadas para commit ===")
        print(out_status)
        print(f"\n💬 Mensagem do Commit: {msg}")

        # git add --all
        code, out, err = run(["git", "add", "--all"])
        if code != 0:
            print(f"❌ Erro no git add:\n{err}")
            sys.exit(code)
        print("✅ git add --all concluído com sucesso.")

        # Verifica se realmente há arquivos no stage antes de commitar
        code_diff, _, _ = run(["git", "diff", "--cached", "--quiet"])
        if code_diff != 0:  # exit code 1 significa que há diferenças staged
            code, out, err = run(["git", "commit", "-m", msg])
            if code != 0:
                print(f"❌ Erro no git commit:\nSTDOUT: {out}\nSTDERR: {err}")
                sys.exit(code)
            print(f"✅ Commit realizado com sucesso:\n{out}")
        else:
            print("ℹ️ Nenhuma alteração adicionada à área de stage.")
    else:
        print("ℹ️ Nenhuma alteração de arquivo pendente para commit local.")

    # 2. Verifica se há commits locais pendentes de envio (ahead)
    code, out_ahead, _ = run(["git", "rev-list", "@{u}..HEAD", "--count"])
    commits_ahead = int(out_ahead) if code == 0 and out_ahead.isdigit() else (1 if has_changes else 0)

    if not has_changes and commits_ahead == 0:
        print("\n🟢 O repositório local já está 100% sincronizado com o GitHub.")
        return

    # 3. Executa git push exclusivamente no repositório Equipes_Agentes
    print("\n🚀 Enviando commits para o repositório Equipes_Agentes no GitHub...")
    code, out, err = run(["git", "push"])
    if code != 0:
        print(f"❌ Erro no git push:\n{err or out}")
        print("\n⚠️ O push não foi concluído. Verifique os erros acima.")
        sys.exit(code)

    print(f"✅ Push concluído com sucesso!\n{out or err}")
    print("\n🎉 Repositório Equipes_Agentes sincronizado com êxito!")


if __name__ == "__main__":
    main()