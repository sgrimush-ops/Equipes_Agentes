"""
executor_ollama.py
Motor Híbrido de Orquestração (IA Online Antigravity -> IA Local Ollama)
com Ciclo de Aprendizado Contínuo (Memória Anti-Reincidência de Erros).

Fluxo Híbrido:
1. A IA Online (Antigravity) planeja a arquitetura/lógica rapidamente.
2. A IA Online delega o trabalho braçal para o Ollama local via `executar`.
3. O Ollama gera o código/SQL/documentação injetando todas as lições aprendidas.
4. A IA Online revisa o resultado, corrige se necessário e executa `ensinar`
   para que o Ollama nunca repita o mesmo erro.
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.error
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Garantir UTF-8 no stdout/stderr no Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORIA_JSON = BASE_DIR / "memoria_aprendizado_ollama.json"
MEMORIA_MD = BASE_DIR / "LICOES_OLLAMA.md"
DIR_PENDENTES = BASE_DIR / "tarefas" / "pendentes"
DIR_EXECUCAO = BASE_DIR / "tarefas" / "em_execucao"
DIR_CONCLUIDAS = BASE_DIR / "tarefas" / "concluidas"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

# Roteamento inteligente de modelos instalados localmente por categoria
MODELOS_POR_CATEGORIA = {
    "sql": "gemma4:latest",
    "var_f7": "hermes3:latest",
    "python": "gemma4:latest",
    "codigo_rapido": "qwen2.5-coder:1.5b",
    "dados": "hermes3:latest",
    "geral": "hermes3:latest",
}

PROMPTS_BASE_CATEGORIA = {
    "sql": (
        "Você é o Executor Local Especialista em SQL Oracle para o ERP Totvs Consinco.\n"
        "Gere APENAS o código SQL solicitado, sem introduções conversacionais.\n"
        "REGRAS INVIOLÁVEIS:\n"
        "1. NUNCA inclua comentários de linha (--) ou de bloco (/* */), EXCETO o hint obrigatório /*+ MATERIALIZE */.\n"
        "2. Sempre que usar CTE (WITH), coloque /*+ MATERIALIZE */ após o SELECT da CTE e envolva toda a query em SELECT * FROM ( WITH ... SELECT ... ).\n"
        "3. Nunca coloque operadores matemáticos fora de blocos CASE com parênteses: aplique a conta dentro do THEN e do ELSE.\n"
        "4. Toda coluna não agregada no SELECT deve estar no GROUP BY (prevenção de ORA-00979).\n"
        "5. Para vendas consolidadas por período/loja, use MRL_CUSTODIA (VLRTOTALVDA, QTDVDA, DTAENTRADASAIDA)."
    ),
    "var_f7": (
        "Você é o Executor Local Especialista em Documentação de Variáveis da Tela Consulta Criação (Var - F7) do ERP Totvs Consinco.\n"
        "Gere a documentação em Markdown (.md) estruturada passo a passo para o cadastro das variáveis (:DT1, :DT2, :LT1, :LS1, :NR1, etc.).\n"
        "REGRAS INVIOLÁVEIS:\n"
        "1. O comando SQL de qualquer lista de seleção (:LS1, :LS2) NUNCA pode ultrapassar 145 caracteres.\n"
        "2. Nunca use SYS.ODCIVARCHAR2LIST em listas LSx (use SELECT DECODE(LEVEL,1,'OP1',2,'OP2') FROM DUAL CONNECT BY LEVEL<=N)."
    ),
    "python": (
        "Você é o Executor Local Especialista em Python 3.14 (Pandas, Automação RPA, FastAPI) do ecossistema Equipes_Agentes.\n"
        "REGRAS INVIOLÁVEIS:\n"
        "1. Use sempre pathlib.Path para caminhos (proibido concatenar strings de caminho).\n"
        "2. Em leitura/escrita de CSV Consinco, use sempre sep=';' e encoding='utf-8-sig'.\n"
        "3. Em arquivos de configuração, código ou JSON/MD, use sempre encoding='utf-8' puro (sem BOM).\n"
        "4. Em RPA multi-monitor, use pynput.mouse.Controller para cliques calibrados (nunca pyautogui.click)."
    ),
    "dados": (
        "Você é o Executor Local de Saneamento e Análise de Dados do Varejo.\n"
        "Responda em Português do Brasil de forma objetiva e estruturada."
    ),
    "geral": (
        "Você é o Executor Técnico Local (Ollama) trabalhando sob coordenação da IA Online (Antigravity).\n"
        "Execute exatamente o briefing técnico recebido, sem rodeios e em Português do Brasil."
    ),
}

LICOES_INICIAIS = [
    {
        "id": 1,
        "data": "2026-11-13 17:50:00",
        "categoria": "sql",
        "erro_observado": "Uso de comentários '--' no código SQL que quebram o parser de linha única do Totvs Consinco.",
        "regra_aprendida": "Proibição absoluta de '--' em qualquer ponto do arquivo .sql. O único comentário permitido é o hint /*+ MATERIALIZE */.",
        "exemplo_errado": "-- Filtro de loja\nWHERE NROEMPRESA = 1",
        "exemplo_correto": "WHERE NROEMPRESA = 1"
    },
    {
        "id": 2,
        "data": "2026-11-13 17:50:00",
        "categoria": "sql",
        "erro_observado": "Query começando diretamente com WITH causa o erro 'A instrução SQL informada, não é uma consulta' no Consinco.",
        "regra_aprendida": "Sempre envelopar queries que usam CTE (WITH) dentro de um SELECT * FROM ( WITH CTE AS (SELECT /*+ MATERIALIZE */ ...) SELECT ... ).",
        "exemplo_errado": "WITH BASE AS (SELECT SEQPRODUTO FROM MAP_PRODUTO) SELECT * FROM BASE",
        "exemplo_correto": "SELECT * FROM (\n    WITH BASE AS (\n        SELECT /*+ MATERIALIZE */ SEQPRODUTO FROM CONSINCO.MAP_PRODUTO\n    )\n    SELECT * FROM BASE\n)"
    },
    {
        "id": 3,
        "data": "2026-11-13 17:50:00",
        "categoria": "var_f7",
        "erro_observado": "SQL da Lista (LS1/LS2) maior que 145 caracteres ou usando SYS.ODCIVARCHAR2LIST (que trunca em 3 letras no Delphi).",
        "regra_aprendida": "Manter SQL da lista abaixo de 145 caracteres em linha única e usar DECODE(LEVEL,...) FROM DUAL CONNECT BY LEVEL<=N para opções fixas.",
        "exemplo_errado": "SELECT COLUMN_VALUE FROM TABLE(SYS.ODCIVARCHAR2LIST('TODOS', 'ATIVOS'))",
        "exemplo_correto": "SELECT DECODE(LEVEL,1,'TODOS',2,'ATIVOS') FROM DUAL CONNECT BY LEVEL<=2"
    }
]


def carregar_memoria() -> Dict[str, Any]:
    """Carrega o banco de lições aprendidas pelo Ollama."""
    if not MEMORIA_JSON.exists():
        dados = {"total_execucoes": 0, "total_licoes": len(LICOES_INICIAIS), "licoes": LICOES_INICIAIS}
        salvar_memoria(dados)
        return dados
    try:
        return json.loads(MEMORIA_JSON.read_text(encoding="utf-8"))
    except Exception:
        dados = {"total_execucoes": 0, "total_licoes": len(LICOES_INICIAIS), "licoes": LICOES_INICIAIS}
        return dados


def salvar_memoria(dados: Dict[str, Any]) -> None:
    """Salva as lições no JSON e sincroniza o arquivo Markdown legível."""
    MEMORIA_JSON.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    sincronizar_markdown_licoes(dados)


def sincronizar_markdown_licoes(dados: Dict[str, Any]) -> None:
    """Gera o relatório legível de todas as correções ensinadas pela IA Online ao Ollama."""
    licoes = dados.get("licoes", [])
    linhas = [
        "# 🧠 Memória de Aprendizado Contínuo — IA Local (Ollama)",
        "",
        f"- **Total de Tarefas Executadas pelo Ollama**: `{dados.get('total_execucoes', 0)}`",
        f"- **Total de Lições Ensinadas pela IA Online**: `{len(licoes)}`",
        f"- **Última Atualização**: `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`",
        "",
        "> Este arquivo é sincronizado automaticamente pelo `executor_ollama.py`. Toda lição registrada aqui é injetada no prompt de sistema do Ollama para evitar que erros corrigidos pela IA Online se repitam.",
        "",
        "---",
        ""
    ]
    for lic in licoes:
        linhas.extend([
            f"### 📌 Lição #{lic.get('id')} — Categoria: `{lic.get('categoria', 'geral').upper()}` ({lic.get('data', '')})",
            f"- **Erro Identificado na Revisão**: {lic.get('erro_observado', '')}",
            f"- **Regra Definitiva Aprendida**: **{lic.get('regra_aprendida', '')}**",
        ])
        if lic.get("exemplo_errado"):
            linhas.append(f"- ❌ **Como NÃO fazer**: `{lic.get('exemplo_errado')}`")
        if lic.get("exemplo_correto"):
            linhas.append(f"- ✅ **Como FAZER**: `{lic.get('exemplo_correto')}`")
        linhas.append("")

    MEMORIA_MD.write_text("\n".join(linhas), encoding="utf-8")


def montar_system_prompt(categoria: str) -> str:
    """Combina o prompt base da categoria com todas as lições aprendidas pertinentes."""
    cat = categoria.lower()
    base = PROMPTS_BASE_CATEGORIA.get(cat, PROMPTS_BASE_CATEGORIA["geral"])
    memoria = carregar_memoria()
    licoes = [
        l for l in memoria.get("licoes", [])
        if l.get("categoria", "").lower() in (cat, "geral", "todas")
    ]
    if not licoes:
        return base

    bloco_licoes = ["\n\n### ⚠️ LIÇÕES APRENDIDAS ANTERIORMENTE (PROIBIDO REPETIR ESTES ERROS):"]
    for idx, lic in enumerate(licoes, start=1):
        linha = f"{idx}. [ERRO EVITADO]: {lic['erro_observado']} -> [REGRA OBRIGATÓRIA]: {lic['regra_aprendida']}"
        if lic.get("exemplo_correto"):
            linha += f" (Padrão Correto: {lic['exemplo_correto']})"
        bloco_licoes.append(linha)

    return base + "\n" + "\n".join(bloco_licoes)


def extrair_bloco_codigo(texto: str, categoria: str) -> str:
    """Extrai o código de dentro de blocos markdown ```sql ... ``` ou ```python ... ``` e sanitiza."""
    padrao = re.compile(r"```(?:sql|python|oracle|plsql)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
    matches = padrao.findall(texto)
    resultado = matches[0].strip() if matches else texto.strip()

    # Sanitização automática de segurança para SQL Consinco (remove comentários -- se o modelo escapar algum)
    if categoria.lower() == "sql":
        linhas_limpas = []
        for linha in resultado.splitlines():
            # Remove comentários de fim de linha --
            linha_sem_comentario = re.sub(r"--.*$", "", linha).rstrip()
            if linha_sem_comentario.strip():
                linhas_limpas.append(linha_sem_comentario)
        resultado = "\n".join(linhas_limpas)

    return resultado


def chamar_ollama(
    prompt: str,
    categoria: str = "geral",
    modelo: Optional[str] = None,
    temperatura: float = 0.15,
    num_ctx: int = 4096,
    num_predict: int = 2048,
    timeout: int = 180
) -> Dict[str, Any]:
    """Envia a tarefa planejada pela IA Online para execução no Ollama local."""
    cat = categoria.lower()
    modelo_escolhido = modelo or MODELOS_POR_CATEGORIA.get(cat, "hermes3:latest")
    system_prompt = montar_system_prompt(cat)

    payload = {
        "model": modelo_escolhido,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {
            "temperature": temperatura,
            "num_ctx": num_ctx,
            "num_predict": num_predict
        }
    }

    inicio = time.time()
    req = urllib.request.Request(
        f"{OLLAMA_URL.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados_resp = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"Falha ao conectar no Ollama em {OLLAMA_URL}: {e}")

    duracao = round(time.time() - inicio, 2)
    conteudo = dados_resp.get("message", {}).get("content", "").strip()
    tokens_prompt = dados_resp.get("prompt_eval_count", 0)
    tokens_gerados = dados_resp.get("eval_count", 0)

    # Atualiza contador de execuções na memória
    memoria = carregar_memoria()
    memoria["total_execucoes"] = memoria.get("total_execucoes", 0) + 1
    salvar_memoria(memoria)

    return {
        "sucesso": True,
        "modelo": modelo_escolhido,
        "categoria": cat,
        "duracao_segundos": duracao,
        "tokens_locais_economizados": tokens_prompt + tokens_gerados,
        "tokens_prompt": tokens_prompt,
        "tokens_gerados": tokens_gerados,
        "resposta_bruta": conteudo
    }


def executar_tarefa_hibrida(
    prompt: str,
    categoria: str = "geral",
    modelo: Optional[str] = None,
    caminho_saida: Optional[str] = None,
    extrair_codigo: bool = False,
    contexto_arquivo: Optional[str] = None
) -> Dict[str, Any]:
    """Executa um briefing da IA Online no Ollama e opcionalmente grava o arquivo de saída."""
    prompt_final = prompt
    if contexto_arquivo:
        arq_ctx = Path(contexto_arquivo)
        if arq_ctx.exists():
            conteudo_ctx = arq_ctx.read_text(encoding="utf-8", errors="replace")
            prompt_final = f"{prompt}\n\n=== CONTEÚDO DO ARQUIVO DE REFERÊNCIA ({arq_ctx.name}) ===\n{conteudo_ctx}"

    print(f"🤖 [Ollama Local] Iniciando execução | Categoria: {categoria.upper()} | Modelo: {modelo or MODELOS_POR_CATEGORIA.get(categoria.lower(), 'hermes3:latest')}...")
    resultado = chamar_ollama(prompt=prompt_final, categoria=categoria, modelo=modelo)

    texto_final = resultado["resposta_bruta"]
    if extrair_codigo or (caminho_saida and Path(caminho_saida).suffix.lower() in (".sql", ".py")):
        texto_final = extrair_bloco_codigo(texto_final, categoria)

    if caminho_saida:
        out_path = Path(caminho_saida)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(texto_final, encoding="utf-8")
        print(f"💾 [Ollama Local] Arquivo gerado em: {out_path}")

    print(
        f"✅ [Ollama Local] Concluído em {resultado['duracao_segundos']}s | "
        f"Tokens processados localmente (economia online): {resultado['tokens_locais_economizados']}"
    )
    resultado["texto_final"] = texto_final
    return resultado


def ensinar_licao(
    categoria: str,
    erro_observado: str,
    regra_aprendida: str,
    exemplo_errado: str = "",
    exemplo_correto: str = ""
) -> Dict[str, Any]:
    """Registra uma correção feita pela IA Online para que o Ollama nunca repita o erro."""
    memoria = carregar_memoria()
    licoes = memoria.get("licoes", [])
    novo_id = (max((l.get("id", 0) for l in licoes), default=0) + 1)

    nova_licao = {
        "id": novo_id,
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "categoria": categoria.lower(),
        "erro_observado": erro_observado.strip(),
        "regra_aprendida": regra_aprendida.strip(),
        "exemplo_errado": exemplo_errado.strip(),
        "exemplo_correto": exemplo_correto.strip()
    }

    licoes.append(nova_licao)
    memoria["licoes"] = licoes
    memoria["total_licoes"] = len(licoes)
    salvar_memoria(memoria)

    print(f"🎓 [Aprendizado Contínuo] Nova lição #{novo_id} registrada na categoria '{categoria.upper()}'!")
    print(f"   ↳ Regra: {regra_aprendida}")
    print(f"   ↳ Memória atualizada em: {MEMORIA_MD}")
    return nova_licao


def listar_licoes(categoria: Optional[str] = None) -> None:
    """Exibe no terminal todas as lições ativas na memória do Ollama."""
    memoria = carregar_memoria()
    licoes = memoria.get("licoes", [])
    if categoria:
        licoes = [l for l in licoes if l.get("categoria", "").lower() == categoria.lower()]

    print(f"\n🧠 === MEMÓRIA DE APRENDIZADO DO OLLAMA ({len(licoes)} lições) ===")
    print(f"📊 Total de execuções locais acumuladas: {memoria.get('total_execucoes', 0)}\n")
    for l in licoes:
        print(f"  [#{l['id']}] ({l['categoria'].upper()}) {l['data']}")
        print(f"      ❌ Erro:  {l['erro_observado']}")
        print(f"      ✅ Regra: {l['regra_aprendida']}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executor Híbrido Ollama + Ciclo de Aprendizado Contínuo")
    subparsers = parser.add_subparsers(dest="comando")

    # Subcomando: executar
    p_exec = subparsers.add_parser("executar", help="Delega uma tarefa planejada pela IA Online para o Ollama local")
    p_exec.add_argument("--prompt", required=True, help="Briefing técnico detalhado definido pela IA Online")
    p_exec.add_argument("--categoria", default="geral", choices=["sql", "var_f7", "python", "codigo_rapido", "dados", "geral"])
    p_exec.add_argument("--modelo", default=None, help="Forçar modelo específico (ex: gemma4:latest, hermes3:latest, qwen2.5-coder:1.5b)")
    p_exec.add_argument("--saida", default=None, help="Caminho do arquivo onde salvar o resultado (.sql, .md, .py)")
    p_exec.add_argument("--extrair-codigo", action="store_true", help="Extrai apenas o conteúdo dentro de blocos ``` ```")
    p_exec.add_argument("--contexto", default=None, help="Caminho de um arquivo local para anexar como contexto ao Ollama")

    # Subcomando: ensinar
    p_ens = subparsers.add_parser("ensinar", help="Ensina ao Ollama uma correção feita pela IA Online para não repetir o erro")
    p_ens.add_argument("--categoria", required=True, choices=["sql", "var_f7", "python", "codigo_rapido", "dados", "geral"])
    p_ens.add_argument("--erro", required=True, help="Descrição do erro que o Ollama cometeu no rascunho")
    p_ens.add_argument("--regra", required=True, help="Regra definitiva para nunca mais repetir o erro")
    p_ens.add_argument("--errado", default="", help="Trecho de exemplo errado (opcional)")
    p_ens.add_argument("--correto", default="", help="Trecho de exemplo corrigido pela IA Online (opcional)")

    # Subcomando: licoes
    p_lic = subparsers.add_parser("licoes", help="Lista todas as lições aprendidas pelo Ollama")
    p_lic.add_argument("--categoria", default=None, help="Filtrar por categoria")

    args = parser.parse_args()

    if args.comando == "executar":
        res = executar_tarefa_hibrida(
            prompt=args.prompt,
            categoria=args.categoria,
            modelo=args.modelo,
            caminho_saida=args.saida,
            extrair_codigo=args.extrair_codigo,
            contexto_arquivo=args.contexto
        )
        if not args.saida:
            print("\n=== RESPOSTA DO OLLAMA ===\n")
            print(res["texto_final"])
    elif args.comando == "ensinar":
        ensinar_licao(
            categoria=args.categoria,
            erro_observado=args.erro,
            regra_aprendida=args.regra,
            exemplo_errado=args.errado,
            exemplo_correto=args.correto
        )
    elif args.comando == "licoes":
        listar_licoes(args.categoria)
    else:
        parser.print_help()
