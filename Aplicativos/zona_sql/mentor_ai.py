"""
Módulo do Mentor IA (Ollama) para a Zona SQL ERP Totvs Consinco.
Integra modelos locais (Hermes 3, Gemma 4, Llama 3, etc.) com a base de conhecimento
e regras de performance do Totvs Consinco / Oracle.
"""

import os
import json
import urllib.request
import urllib.error
import time
import re

OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = "qwen2.5-coder:1.5b"

SYSTEM_PROMPT_CONSINCO = """Você é o Mentor IA Especialista em SQL Oracle do ERP Totvs Consinco.
Responda sempre em Português do Brasil de forma didática, direta e concisa.

### REGRAS CRÍTICAS DE PERFORMANCE E VALIDAÇÃO TOTVS CONSINCO:
1. PROIBIÇÃO DE COMENTÁRIOS NO SQL: NUNCA use comentários de linha (--) ou bloco (/* */) no meio do SQL gerado, pois o validador Delphi/Consinco quebra o comando ao remover quebras de linha.
2. CTE MATERIALIZADA: Sempre use /*+ MATERIALIZE */ logo após o SELECT de uma CTE (ex: WITH PROD AS (SELECT /*+ MATERIALIZE */ ...)).
3. BYPASS VALIDADOR: Ao usar WITH, envolva sempre em um SELECT fantasma: SELECT * FROM ( WITH ... SELECT ... ).
4. SEM ARITMÉTICA FORA DE CASE: Aritmética deve ficar dentro de cada THEN e ELSE do CASE.
5. ALINHAMENTO UNION ALL: Todos os blocos do UNION ALL devem possuir o mesmo número e ordem posicional de colunas.
6. TABELAS OFICIAIS REAIS DO SISTEMA:
- MAP_PRODUTO (SEQPRODUTO, DESCCOMPLETA, DESCREDUZIDA, SEQFAMILIA, STATUS)
- MAP_FAMILIA (SEQFAMILIA, FAMILIA, PESAVEL, ALIQUOTAICMS)
- MAP_CATEGORIA (SEQCATEGORIA, CATEGORIA, NIVELHIERARQUIA, SEQCATEGORIAPAI)
- MAP_FAMDIVCATEG (SEQFAMILIA, NRODIVISAO, SEQCATEGORIA)
- MAP_FAMFORNEC (SEQFAMILIA, SEQPESSOA, PRINCIPAL='S')
- MAP_PRODCODIGO (SEQPRODUTO, CODACESSO, TIPCODIGO, QTDEMBALAGEM)
- MAX_EMPRESA (NROEMPRESA, NOMERAZAO, FANTASIA, RAZAOSOCIAL, CGC) - Lojas 1 a 18, CD 16 e CD 50
- MAX_COMPRADOR (NROCOMPRADOR, APELIDO, NOME)
- GE_PESSOA (SEQPESSOA, NOMERAZAO, FANTASIA, CGCCPF)
- MRL_PRODUTOEMPRESA (SEQPRODUTO, NROEMPRESA, ESTQLOJA, ESTQDEPOSITO, PRCBASE, CMULTCUSLIQUIDOEMP, STATUSCOMPRA)
- MRL_PRODEMPSEG (SEQPRODUTO, NROEMPRESA, PRECOVALIDNORMAL, PRECOVALIDPROMOC, STATUSVENDA)
7. FLUXO OFICIAL DE CARGA E UPDATE DE PONTAS (MRL_PONTOEXTRAPRODUTOEMPRESA):
- EXTRAÇÃO (9 COLUNAS EXATAS):
  SELECT PEPE.SEQPONTOEXTRA, PE.DESCRICAO, PEPE.SEQPRODUTO, PROD.DESCCOMPLETA, PEPE.NROEMPRESA, PEPE.ESTQMINIMO, PEPE.ESTQMAXIMO, PEPE.DTAVIGENCIAINICIO, PEPE.DTAVIGENCIAFIM
  FROM MRL_PONTOEXTRA PE
  INNER JOIN MRL_PONTOEXTRAPRODUTO PEP ON PEP.SEQPONTOEXTRA = PE.SEQPONTOEXTRA
  INNER JOIN MRL_PONTOEXTRAPRODUTOEMPRESA PEPE ON PEPE.SEQPONTOEXTRA = PEP.SEQPONTOEXTRA AND PEPE.SEQPRODUTO = PEP.SEQPRODUTO
  INNER JOIN MAP_PRODUTO PROD ON PROD.SEQPRODUTO = PEPE.SEQPRODUTO
  ORDER BY PEPE.SEQPONTOEXTRA, PEPE.NROEMPRESA, PEPE.SEQPRODUTO;
- EDIÇÃO CSV: Usuário altera ESTQMINIMO, ESTQMAXIMO e datas (YYYY-MM-DD).
- UPDATE NO CONSINCO: Gerar UPDATE com WHERE por (SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA) ou MERGE INTO finalizando com COMMIT;. Garantir antes o vínculo na capa MRL_PONTOEXTRAPRODUTO.
8. RESPOSTAS COMPLETAS E CONCLUSIVAS: Desenvolva toda a sua explicação de forma clara, didática e termine sempre seu raciocínio com uma conclusão. Nunca deixe frases ou blocos de código abertos pela metade, feche sempre com ```.

Responda com clareza, explicando o conceito e fornecendo o código SQL no bloco ```sql ... ```."""

class OllamaMentorService:
    def __init__(self, base_url=OLLAMA_BASE_URL, default_model=DEFAULT_MODEL):
        self.base_url = base_url.rstrip("/")
        self.current_model = default_model

    def check_status(self):
        """Verifica se o servidor Ollama está online e quais modelos estão disponíveis."""
        start = time.time()
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": "ZonaSQL-Mentor/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                
                # Se o modelo atual não estiver instalado, selecionar hermes3 ou o primeiro disponível
                if models:
                    if "hermes3:latest" in models and self.current_model not in models:
                        self.current_model = "hermes3:latest"
                    elif self.current_model not in models:
                        self.current_model = models[0]

                latency_ms = round((time.time() - start) * 1000, 1)
                return {
                    "online": True,
                    "models": models,
                    "current_model": self.current_model,
                    "latency_ms": latency_ms,
                    "endpoint": self.base_url
                }
        except Exception as e:
            return {
                "online": False,
                "models": [],
                "current_model": self.current_model,
                "latency_ms": 0,
                "error": str(e),
                "endpoint": self.base_url
            }

    def set_model(self, model_name):
        """Define o modelo ativo do Ollama."""
        status = self.check_status()
        if model_name in status.get("models", []):
            self.current_model = model_name
            return True, f"Modelo alterado para {model_name}"
        elif status.get("online"):
            self.current_model = model_name
            return True, f"Modelo definido como {model_name}"
        return False, "Ollama offline"

    def _call_generate(self, prompt, system_prompt=None, temperature=0.2, timeout=240, max_tokens=2048):
        """Executa a chamada HTTP para /api/generate do Ollama com multi-threading em CPU e buffer ampliado de 2048 tokens."""
        url = f"{self.base_url}/api/generate"
        threads = max(2, (os.cpu_count() or 4) - 2)
        payload = {
            "model": self.current_model,
            "prompt": prompt,
            "system": system_prompt or SYSTEM_PROMPT_CONSINCO,
            "stream": False,
            "keep_alive": "30m",
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_ctx": 4096,
                "num_predict": max_tokens,
                "num_thread": threads
            }
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "ZonaSQL-Mentor/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()

    def chat(self, user_message, current_sql="", history=None):
        """Conversação interativa com o Mentor IA."""
        status = self.check_status()
        if not status.get("online"):
            return {
                "success": False,
                "error": "Ollama não está respondendo em http://127.0.0.1:11434. Verifique se o serviço está em execução.",
                "online": False
            }

        start_time = time.time()
        
        context_parts = []
        if current_sql and current_sql.strip():
            context_parts.append(f"--- SQL ATUAL NO EDITOR DO USUÁRIO ---\n{current_sql.strip()}\n--------------------------------------")

        if history and isinstance(history, list):
            context_parts.append("--- HISTÓRICO DA CONVERSA RECENTE ---")
            for h in history[-4:]:
                role = "Usuário" if h.get("role") == "user" else "Mentor IA"
                context_parts.append(f"{role}: {h.get('content', '')}")
            context_parts.append("-------------------------------------")

        context_str = "\n\n".join(context_parts)
        full_prompt = f"{context_str}\n\nPergunta do Usuário: {user_message}\n\nResposta do Mentor IA:" if context_str else f"Pergunta do Usuário: {user_message}\n\nResposta do Mentor IA:"

        try:
            response_text = self._call_generate(full_prompt, temperature=0.3)
            
            # Extrair blocos de SQL sugeridos se houver
            extracted_sql = None
            sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, flags=re.DOTALL | re.IGNORECASE)
            if sql_match:
                extracted_sql = sql_match.group(1).strip()

            elapsed = round(time.time() - start_time, 2)
            return {
                "success": True,
                "response": response_text,
                "extracted_sql": extracted_sql,
                "model": self.current_model,
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro na inferência do modelo {self.current_model}: {str(e)}"
            }

    def explain_and_fix_error(self, sql, error_msg, binds=None):
        """Diagnostica erros de execução Oracle/Consinco e gera a correção automática."""
        status = self.check_status()
        if not status.get("online"):
            return {
                "success": False,
                "error": "Ollama não está respondendo. Inicie o Ollama para depuração com IA."
            }

        start_time = time.time()
        
        prompt = f"""O usuário executou a seguinte consulta SQL no simulador Oracle Consinco:

```sql
{sql}
```

E o banco de dados retornou o seguinte erro:
"{error_msg}"

Parâmetros Bind (se houver): {json.dumps(binds or {})}

Por favor, faça:
1. EXPLICAÇÃO DIDÁTICA: Explique de forma muito clara e concisa em português brasileiro exatamente por que esse erro aconteceu (qual coluna, tabela, JOIN ou sintaxe causou o problema no padrão Consinco/Oracle).
2. O QUE APRENDER: Qual é a boa prática ou regra que evita esse erro no futuro.
3. SQL CORRIGIDO: Forneça a consulta SQL corrigida e completa em um bloco ```sql ... ``` (LEMBRE-SE: NUNCA insira comentários com -- dentro do SQL!)."""

        try:
            response_text = self._call_generate(prompt, temperature=0.1)
            
            # Extrair o SQL corrigido
            fixed_sql = None
            sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, flags=re.DOTALL | re.IGNORECASE)
            if sql_match:
                fixed_sql = sql_match.group(1).strip()

            elapsed = round(time.time() - start_time, 2)
            return {
                "success": True,
                "explanation": response_text,
                "fixed_sql": fixed_sql,
                "original_sql": sql,
                "error_analyzed": error_msg,
                "model": self.current_model,
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao analisar com IA: {str(e)}"
            }

    def text_to_sql(self, natural_language_request):
        """Transforma um pedido em linguagem natural em SQL Consinco/Oracle com explicação."""
        status = self.check_status()
        if not status.get("online"):
            return {
                "success": False,
                "error": "Ollama offline. Inicie o Ollama para gerar SQL por IA."
            }

        start_time = time.time()
        
        prompt = f"""Converta a seguinte solicitação de negócio em uma consulta SQL Oracle otimizada para o ERP Totvs Consinco:

Solicitação do Usuário: "{natural_language_request}"

Requisitos Obrigatórios:
1. Use as tabelas e colunas oficiais do Consinco (ex: MAP_PRODUTO, MRL_PRODUTOEMPRESA, MAX_EMPRESA, MRL_PONTOEXTRAPRODUTOEMPRESA, FI_TITULO, etc.).
2. NUNCA use comentários de linha (--) no SQL.
3. Palavras-chave SQL em MAIÚSCULAS.
4. Apresente o código completo dentro de ```sql ... ```.
5. Explique resumidamente como a consulta funciona (quais tabelas e filtros foram usados)."""

        try:
            response_text = self._call_generate(prompt, temperature=0.2)
            
            sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, flags=re.DOTALL | re.IGNORECASE)
            generated_sql = sql_match.group(1).strip() if sql_match else ""

            elapsed = round(time.time() - start_time, 2)
            return {
                "success": True,
                "generated_sql": generated_sql,
                "explanation": response_text,
                "request": natural_language_request,
                "model": self.current_model,
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao gerar SQL com IA: {str(e)}"
            }

    def find_table(self, intent_or_keyword):
        """Localiza a tabela e as colunas certas a partir de uma dúvida de negócio."""
        status = self.check_status()
        if not status.get("online"):
            return {
                "success": False,
                "error": "Ollama offline."
            }

        start_time = time.time()
        
        prompt = f"""O usuário quer saber onde encontrar a seguinte informação no banco de dados Totvs Consinco:
"{intent_or_keyword}"

Indique com clareza:
1. Qual(is) tabela(s) armazena(m) esse dado (ex: MAP_PRODUTO, MRL_PRODUTOEMPRESA, FI_TITULO, MRL_PONTOEXTRA, etc.).
2. Quais colunas principais devem ser selecionadas.
3. Como fazer o JOIN com outras tabelas essenciais (como MAX_EMPRESA para lojas ou GE_PESSOA para fornecedores).
4. Um exemplo prático e limpo de consulta SQL dentro de ```sql ... ``` (sem comentários --)."""

        try:
            response_text = self._call_generate(prompt, temperature=0.2)
            
            sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, flags=re.DOTALL | re.IGNORECASE)
            sample_sql = sql_match.group(1).strip() if sql_match else ""

            elapsed = round(time.time() - start_time, 2)
            return {
                "success": True,
                "answer": response_text,
                "sample_sql": sample_sql,
                "query": intent_or_keyword,
                "model": self.current_model,
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao buscar tabela com IA: {str(e)}"
            }

# Instância global singleton
ollama_mentor = OllamaMentorService()
