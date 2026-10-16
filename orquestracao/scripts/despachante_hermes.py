"""
despachante_hermes.py
Utilitário para criação e gerenciamento de tarefas na fila compartilhada
entre o Hermes Agent e o Google Antigravity.
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Garantir UTF-8 no stdout/stderr no Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent
DIR_PENDENTES = BASE_DIR / "tarefas" / "pendentes"
DIR_EXECUCAO = BASE_DIR / "tarefas" / "em_execucao"
DIR_CONCLUIDAS = BASE_DIR / "tarefas" / "concluidas"
DIR_FALHAS = BASE_DIR / "tarefas" / "falhas"
DIR_TEMPLATES = BASE_DIR / "templates"

for d in [DIR_PENDENTES, DIR_EXECUCAO, DIR_CONCLUIDAS, DIR_FALHAS]:
    d.mkdir(parents=True, exist_ok=True)


def gerar_slug(texto: str) -> str:
    import re
    texto = texto.lower()
    texto = re.sub(r"[^\w\s-]", "", texto)
    return re.sub(r"[-\s]+", "_", texto).strip("-_")


def criar_tarefa(titulo: str, tipo: str = "sql", descricao: str = "", prioridade: str = "Média", origem: str = "Hermes Agent") -> Path:
    """Cria um novo arquivo de tarefa na pasta pendentes."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = gerar_slug(titulo)[:35]
    nome_arquivo = f"{timestamp}_{slug}.md"
    caminho_arquivo = DIR_PENDENTES / nome_arquivo

    template_file = DIR_TEMPLATES / ("modelo_tarefa_sql.md" if tipo.lower() == "sql" else "modelo_tarefa_automacao.md")
    
    if template_file.exists():
        conteudo = template_file.read_text(encoding="utf-8")
        conteudo = conteudo.replace("{TIMESTAMP}_{SLUG}", f"{timestamp}_{slug}")
        conteudo = conteudo.replace("{DATA_HORA}", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        conteudo = conteudo.replace("[Título da Demanda SQL]", titulo)
        conteudo = conteudo.replace("[Título da Demanda de Automação / Script]", titulo)
        conteudo = conteudo.replace("Hermes Agent", origem)
        if descricao:
            conteudo = conteudo.replace("Descreva de forma clara o que o usuário ou a rotina precisa analisar.", descricao)
            conteudo = conteudo.replace("Descreva o que o script ou a automação deve realizar.", descricao)
    else:
        conteudo = f"""# Tarefa: {titulo}
- **ID**: {timestamp}_{slug}
- **Origem**: {origem}
- **Data de Criação**: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
- **Tipo**: {tipo}
- **Prioridade**: {prioridade}
- **Status**: Pendente

---

## 🎯 Objetivo
{descricao}

---

## 🏁 Relatório de Execução (Preenchido pelo Antigravity ao concluir)
*Aguardando processamento...*
"""

    caminho_arquivo.write_text(conteudo, encoding="utf-8")
    print(f"✅ Tarefa criada com sucesso: {caminho_arquivo}")
    return caminho_arquivo


def listar_tarefas():
    """Lista tarefas em cada estágio."""
    print("\n📋 === STATUS DA FILA DE TAREFAS ===")
    
    def _mostrar(diretorio, rotulo):
        arquivos = list(diretorio.glob("*.md"))
        print(f"\n📂 {rotulo} ({len(arquivos)}):")
        for f in sorted(arquivos):
            print(f"  - {f.name}")

    _mostrar(DIR_PENDENTES, "Pendentes")
    _mostrar(DIR_EXECUCAO, "Em Execução")
    _mostrar(DIR_CONCLUIDAS, "Concluídas")
    _mostrar(DIR_FALHAS, "Falhas")
    print("===================================\n")


def marcar_concluida(arquivo_path: Path, relatorio: str, arquivos_gerados: list = None):
    """Move uma tarefa para concluída e adiciona o relatório de entrega."""
    if not arquivo_path.exists():
        print(f"❌ Arquivo não encontrado: {arquivo_path}")
        return

    conteudo = arquivo_path.read_text(encoding="utf-8")
    bloco_resultado = f"""

---

## 🏁 Relatório de Execução (Concluído pelo Antigravity)
- **Data de Finalização**: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
- **Status**: Concluído com Sucesso

### 📝 Resumo da Entrega:
{relatorio}
"""
    if arquivos_gerados:
        bloco_resultado += "\n### 📁 Arquivos Gerados / Modificados:\n"
        for arq in arquivos_gerados:
            bloco_resultado += f"- `{arq}`\n"

    conteudo = conteudo.replace("*Aguardando processamento...*", bloco_resultado.strip())
    
    destino = DIR_CONCLUIDAS / arquivo_path.name
    destino.write_text(conteudo, encoding="utf-8")
    arquivo_path.unlink()
    print(f"🎉 Tarefa finalizada e arquivada em: {destino}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Despachante Hermes <-> Antigravity")
    subparsers = parser.add_subparsers(dest="comando")

    # Comando criar
    p_criar = subparsers.add_parser("criar", help="Cria uma nova tarefa")
    p_criar.add_argument("--titulo", required=True, help="Título da tarefa")
    p_criar.add_argument("--tipo", default="sql", choices=["sql", "automacao", "dados"], help="Tipo de tarefa")
    p_criar.add_argument("--descricao", default="", help="Descrição detalhada do objetivo")
    p_criar.add_argument("--prioridade", default="Média", choices=["Baixa", "Média", "Alta"], help="Prioridade")

    # Comando listar
    p_listar = subparsers.add_parser("listar", help="Lista as tarefas em todas as filas")

    args = parser.parse_args()

    if args.comando == "criar":
        criar_tarefa(args.titulo, args.tipo, args.descricao, args.prioridade)
    elif args.comando == "listar":
        listar_tarefas()
    else:
        parser.print_help()
