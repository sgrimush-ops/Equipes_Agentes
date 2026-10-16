# Guia de Instalação e Ativação do Hermes no Antigravity do Servidor

Este documento foi criado para você **copiar e colar diretamente no chat do Antigravity do seu servidor**. 

Ao colar o prompt da **Seção 1**, o Antigravity do servidor configurará toda a estrutura de pastas, scripts Python, templates e a Skill de orquestração automaticamente, sem você precisar criar nenhum arquivo manualmente.

---

## 📋 SEÇÃO 1: Mega-Prompt de Configuração Automática
> **Instrução**: Copie todo o bloco abaixo (de `### INÍCIO DO PROMPT` até `### FIM DO PROMPT`) e cole no chat do Antigravity do seu servidor.

```markdown
### INÍCIO DO PROMPT

Olá Antigravity! Preciso que você configure neste workspace a infraestrutura completa de orquestração e fila integrada com o Hermes Agent (arquitetura Agent OS desacoplada).

Execute de forma autônoma as seguintes etapas:

1. Crie os seguintes diretórios no projeto:
   - `orquestracao/tarefas/pendentes/`
   - `orquestracao/tarefas/em_execucao/`
   - `orquestracao/tarefas/concluidas/`
   - `orquestracao/tarefas/falhas/`
   - `orquestracao/templates/`
   - `orquestracao/scripts/`
   - `.agents/skills/orquestracao_hermes/`

2. Crie o arquivo `orquestracao/scripts/despachante_hermes.py` com o seguinte código (garantindo encoding UTF-8 no Windows):
```python
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

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
        conteudo = f"# Tarefa: {titulo}\n- **ID**: {timestamp}_{slug}\n- **Origem**: {origem}\n- **Status**: Pendente\n\n## Objetivo\n{descricao}\n"

    caminho_arquivo.write_text(conteudo, encoding="utf-8")
    print(f"✅ Tarefa criada com sucesso: {caminho_arquivo}")
    return caminho_arquivo

def listar_tarefas():
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
    if not arquivo_path.exists():
        print(f"❌ Arquivo não encontrado: {arquivo_path}")
        return
    conteudo = arquivo_path.read_text(encoding="utf-8")
    bloco_resultado = f"\n\n---\n\n## 🏁 Relatório de Execução (Concluído pelo Antigravity)\n- **Data**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n- **Status**: Concluído com Sucesso\n\n### 📝 Resumo da Entrega:\n{relatorio}\n"
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
    p_criar = subparsers.add_parser("criar", help="Cria uma nova tarefa")
    p_criar.add_argument("--titulo", required=True, help="Título da tarefa")
    p_criar.add_argument("--tipo", default="sql", choices=["sql", "automacao", "dados"])
    p_criar.add_argument("--descricao", default="")
    p_criar.add_argument("--prioridade", default="Média", choices=["Baixa", "Média", "Alta"])
    p_listar = subparsers.add_parser("listar", help="Lista as tarefas")
    args = parser.parse_args()
    if args.comando == "criar":
        criar_tarefa(args.titulo, args.tipo, args.descricao, args.prioridade)
    elif args.comando == "listar":
        listar_tarefas()
    else:
        parser.print_help()
```

3. Crie o arquivo de template `orquestracao/templates/modelo_tarefa_sql.md`:
```markdown
# Tarefa: [Título da Demanda SQL]

- **ID**: {TIMESTAMP}_{SLUG}
- **Origem**: Hermes Agent
- **Data de Criação**: {DATA_HORA}
- **Tipo**: SQL / Consulta Consinco
- **Prioridade**: Alta | Média | Baixa
- **Status**: Pendente

---

## 🎯 Objetivo de Negócio
Descreva de forma clara o que o usuário ou a rotina precisa analisar.

## 📋 Especificações e Parâmetros
- **Tabelas / Módulos de Interesse**: (ex: MRL_PRODUTOEMPRESA, MRL_CUSTODIA, MAP_PRODUTO)
- **Tela de Destino**: Consulta Criação / Var-F7 / Relatório Externo
- **Filtros Obrigatórios**:
  - Filiais: :LS1 ou :LT1
  - Período: :DT1 a :DT2
- **Regras Específicas**: (Sem comentários no SQL, utilizar /*+ MATERIALIZE */ em CTEs, limitar listas Var-F7 a 145 caracteres)

## 📦 Entrega Esperada
1. Arquivo .sql pronto para importação.
2. Arquivo .md explicativo da parametrização das variáveis da tela Var - F7.

---

## 🏁 Relatório de Execução (Preenchido pelo Antigravity ao concluir)
*Aguardando processamento...*
```

4. Crie o template `orquestracao/templates/modelo_tarefa_automacao.md`:
```markdown
# Tarefa: [Título da Demanda de Automação / Script]

- **ID**: {TIMESTAMP}_{SLUG}
- **Origem**: Hermes Agent
- **Data de Criação**: {DATA_HORA}
- **Tipo**: Script / Automação / Dashboard / Limpeza de Dados
- **Prioridade**: Alta | Média | Baixa
- **Status**: Pendente

---

## 🎯 Objetivo
Descreva o que o script ou a automação deve realizar.

## 📋 Especificações
- **Entrada (Inputs)**: Caminho do arquivo CSV, Excel, PDF ou endpoint de API.
- **Transformações Necessárias**: Regras de negócio, filtros, conversão de tipos.
- **Saída (Outputs)**: Arquivo tratado, dashboard HTML único ou script executável.

## 📦 Entrega Esperada
1. Código em Python documentado e testado.
2. Instruções de execução rápida ou agendamento cron.

---

## 🏁 Relatório de Execução (Preenchido pelo Antigravity ao concluir)
*Aguardando processamento...*
```

5. Crie a Skill do Antigravity em `.agents/skills/orquestracao_hermes/SKILL.md`:
```markdown
---
name: orquestracao_hermes
description: "Gerencia e executa tarefas recebidas da fila de integração entre o Hermes Agent e o Antigravity (leitura de tarefas pendentes, execução técnica e conclusão documentada)."
---

# Skill: Orquestração Hermes Agent <-> Google Antigravity

Esta skill orienta o Antigravity na execução automatizada ou sob demanda de tarefas delegadas pelo Hermes Agent através da fila de memória compartilhada em `orquestracao/tarefas/`.

## 📂 Diretórios Oficiais da Fila
- Pendentes: `orquestracao/tarefas/pendentes/`
- Em Execução: `orquestracao/tarefas/em_execucao/`
- Concluídas: `orquestracao/tarefas/concluidas/`
- Falhas: `orquestracao/tarefas/falhas/`

## 🔄 Protocolo de Execução
Sempre que solicitado a processar tarefas da fila:
1. Verifique `orquestracao/tarefas/pendentes/`.
2. Mova a tarefa selecionada para `orquestracao/tarefas/em_execucao/`.
3. Execute as alterações técnicas exigidas.
4. Mova o arquivo para `orquestracao/tarefas/concluidas/` registrando o resumo da entrega e arquivos gerados.
```

6. Por fim, execute um teste rápido criando uma tarefa piloto com o comando:
`python orquestracao/scripts/despachante_hermes.py criar --titulo "Teste de Conexao Servidor" --tipo "sql" --descricao "Validando instalacao no servidor"`
E exiba o status da fila com:
`python orquestracao/scripts/despachante_hermes.py listar`

Confirme para mim quando a infraestrutura estiver 100% pronta!

### FIM DO PROMPT
```

---

## 💡 Como Usar no Servidor Após Colar o Prompt

Assim que o Antigravity do servidor rodar o prompt acima, tudo estará ativo. Você poderá operar o servidor da seguinte forma:

1. **Para o Hermes Agent (ou robô/cron do servidor) criar tarefas**:
   ```bash
   python orquestracao/scripts/despachante_hermes.py criar --titulo "Nome da Tarefa" --tipo "sql" --descricao "Detalhes do que fazer"
   ```

2. **Para o Antigravity no servidor resolver as tarefas**:
   Basta digitar no chat do Antigravity:
   > *"Processe as tarefas pendentes da fila do Hermes"*
