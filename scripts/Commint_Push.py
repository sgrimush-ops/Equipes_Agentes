"""
Commint_Push.py
---------------
Script para realizar git add (incluindo exclusões), commit e push
no repositório atual e em submódulos aninhados (ex: Aplicativos/APP_Bak).
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


def run(cmd: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    """Executa comando git dentro do diretório especificado ou raiz do repositório."""
    target_cwd = cwd or REPO
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", cwd=target_cwd
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def find_submodules() -> list[str]:
    """Descobre submódulos / sub-repositórios Git dentro do repositório principal."""
    submodules = []
    for root, dirs, _ in os.walk(REPO):
        if os.path.abspath(root) == os.path.abspath(REPO):
            continue
        if ".git" in dirs:
            submodules.append(root)
            dirs.remove(".git")
        # Evita descer excessivamente na árvore de diretórios
        depth = os.path.relpath(root, REPO).count(os.sep)
        if depth >= 3:
            dirs.clear()
    return submodules


def sync_submodules(msg: str):
    """Sincroniza submódulos/sub-repositórios antes de commitar na raiz."""
    subs = find_submodules()
    for sub in subs:
        sub_rel = os.path.relpath(sub, REPO).replace("\\", "/")
        code, out_status, _ = run(["git", "status", "--short"], cwd=sub)
        has_sub_changes = bool(out_status)

        if has_sub_changes:
            print(f"\n📦 Submódulo detectado com alterações: {sub_rel}")
            print(out_status)
            run(["git", "add", "--all"], cwd=sub)
            code_c, out_c, err_c = run(["git", "commit", "-m", msg], cwd=sub)
            if code_c == 0:
                print(f"✅ Commit realizado no submódulo {sub_rel}")
            else:
                print(f"⚠️ Aviso no commit do submódulo {sub_rel}: {err_c or out_c}")

        # Verifica se há commits pendentes de push no submódulo
        code_a, out_a, _ = run(["git", "rev-list", "@{u}..HEAD", "--count"], cwd=sub)
        commits_ahead = int(out_a) if code_a == 0 and out_a.isdigit() else (1 if has_sub_changes else 0)

        if commits_ahead > 0:
            print(f"🚀 Enviando commits do submódulo {sub_rel} para o GitHub...")
            code_p, out_p, err_p = run(["git", "push"], cwd=sub)
            if code_p == 0:
                print(f"✅ Push do submódulo {sub_rel} concluído com sucesso!")
            else:
                print(f"⚠️ Erro no push do submódulo {sub_rel}:\n{err_p or out_p}")


def main():
    print(f"📁 Raiz do Repositório Git: {REPO}\n")
    msg = f"Atualização automática - {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    # 1. Sincroniza submódulos primeiro (evita 'modified content, untracked content' na raiz)
    sync_submodules(msg)

    # 2. Verifica alterações locais pendentes na raiz
    code, out_status, err_status = run(["git", "status", "--short"])
    has_changes = bool(out_status)

    if has_changes:
        print("\n=== 📝 Alterações detectadas para commit ===")
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
        print("\nℹ️ Nenhuma alteração pendente para commit local.")

    # 3. Verifica se há commits locais pendentes de envio (ahead)
    code, out_ahead, _ = run(["git", "rev-list", "@{u}..HEAD", "--count"])
    commits_ahead = int(out_ahead) if code == 0 and out_ahead.isdigit() else (1 if has_changes else 0)

    if not has_changes and commits_ahead == 0:
        print("\n🟢 O repositório local já está 100% atualizado e sincronizado com o GitHub.")
        return

    # 4. Executa git push no repositório principal
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