"""
Módulo do Mentor IA para a Zona SQL ERP Totvs Consinco.
Integra modelos ultrarrápidos em nuvem (Google Gemini 2.5 Flash, 2.0 Flash, 1.5 Flash)
e modelos locais via Ollama (Qwen 2.5 Coder, Hermes 3, Gemma 4) com a base de conhecimento
e regras de performance do Totvs Consinco / Oracle.
"""

import os
import json
import urllib.request
import urllib.error
import time
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "gemini_config.json")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-3.5-flash"
]
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:1.5b"

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
- MRL_PONTOEXTRA (SEQPONTOEXTRA, DESCRICAO, STATUS)
- MRL_PONTOEXTRAPRODUTO (SEQPONTOEXTRA, SEQPRODUTO, STATUS)
- MRL_PONTOEXTRAPRODUTOEMPRESA (SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA, ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM, QTDDIASSUGESTAO, STATUS)
- MRL_CUSTODIA (SEQPRODUTO, NROEMPRESA, DTAENTRADASAIDA, QTDVDA, VLRTOTALVDA, CODGERALOPER)
- MRL_PRODVENDADIA (SEQPRODUTO, NROEMPRESA, DTAVENDA, QTDVENDA, VLRVENDA)
- FI_TITULO (SEQTITULO, NROEMPRESA, SEQPESSOA, DTOVENCIMENTO, VLRORIGINAL, VLRLIQUIDO, STATUS)
- MSU_PEDIDOSUPRIM (NROPEDIDOSUPRIM, NROEMPRESA, SEQPESSOA, DTAPEDIDO, SITUACAOPEDIDO)
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


class UnifiedMentorService:
    def __init__(self, ollama_base_url=OLLAMA_BASE_URL):
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.config = self._load_config()
        
        # Define modelo padrão: Sempre Gemini 2.5 Flash
        self.current_model = self.config.get("preferred_model", DEFAULT_GEMINI_MODEL)

    def _load_config(self):
        """Carrega as configurações locais persistidas."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_config(self):
        """Salva as configurações locais em arquivo JSON."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MentorAI] Erro ao salvar config: {e}")

    def get_gemini_key(self):
        """Retorna a chave da API do Gemini obtida do ambiente ou do arquivo de configuração."""
        return (
            os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or self.config.get("gemini_api_key", "").strip()
        )

    def set_gemini_key(self, api_key):
        """Atualiza e salva a chave da API do Gemini."""
        self.config["gemini_api_key"] = api_key.strip()
        if api_key.strip():
            self.config["preferred_model"] = DEFAULT_GEMINI_MODEL
            self.current_model = DEFAULT_GEMINI_MODEL
        self._save_config()
        return True, "Chave Gemini API salva com sucesso!"

    def is_gemini_model(self, model_name=None):
        """Verifica se o modelo informado (ou atual) é da família Google Gemini."""
        m = (model_name or self.current_model).lower()
        return "gemini" in m

    def check_ollama_status(self):
        """Verifica se o servidor Ollama está online e quais modelos estão disponíveis."""
        start = time.time()
        try:
            url = f"{self.ollama_base_url}/api/tags"
            req = urllib.request.Request(url, headers={"User-Agent": "ZonaSQL-Mentor/2.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_models = [m.get("name") for m in data.get("models", [])]
                # Filtrar modelos indesejados (ex: hermes3)
                models = [m for m in raw_models if "hermes" not in m.lower()]
                latency_ms = round((time.time() - start) * 1000, 1)
                return {
                    "online": True,
                    "models": models,
                    "latency_ms": latency_ms
                }
        except Exception as e:
            return {
                "online": False,
                "models": [],
                "latency_ms": 0,
                "error": str(e)
            }

    def check_status(self):
        """Verifica o status consolidado de ambos os provedores (Gemini Flash e Ollama)."""
        ollama_status = self.check_ollama_status()
        gemini_key = self.get_gemini_key()
        has_gemini = bool(gemini_key)

        is_gemini = self.is_gemini_model()
        is_online = (is_gemini and has_gemini) or ollama_status["online"]

        # Lista unificada de modelos disponíveis
        available_models = []
        if has_gemini:
            for gm in GEMINI_MODELS:
                available_models.append({
                    "id": gm,
                    "name": f"✨ {gm} (Google Cloud - Flash)",
                    "provider": "gemini"
                })
        else:
            for gm in GEMINI_MODELS:
                available_models.append({
                    "id": gm,
                    "name": f"🔑 {gm} (Requer Chave API)",
                    "provider": "gemini",
                    "requires_key": True
                })

        for om in ollama_status.get("models", []):
            available_models.append({
                "id": om,
                "name": f"🖥️ {om} (Ollama Local)",
                "provider": "ollama"
            })

        latency_ms = 0
        if is_gemini and has_gemini:
            latency_ms = self.config.get("last_gemini_latency_ms", 180)
        elif ollama_status["online"]:
            latency_ms = ollama_status["latency_ms"]

        masked_key = ""
        if gemini_key:
            masked_key = gemini_key[:6] + "..." + gemini_key[-4:] if len(gemini_key) > 10 else "***"

        return {
            "online": is_online,
            "provider": "gemini" if is_gemini else "ollama",
            "current_model": self.current_model,
            "has_gemini_key": has_gemini,
            "masked_gemini_key": masked_key,
            "gemini_models": GEMINI_MODELS,
            "ollama_online": ollama_status["online"],
            "ollama_models": ollama_status.get("models", []),
            "all_models": available_models,
            "latency_ms": latency_ms,
            "endpoint": "Google Gemini API" if is_gemini else self.ollama_base_url
        }

    def set_model(self, model_name):
        """Define o modelo ativo do Mentor (Gemini ou Ollama)."""
        self.current_model = model_name
        self.config["preferred_model"] = model_name
        self._save_config()

        if self.is_gemini_model(model_name):
            if not self.get_gemini_key():
                return False, f"Modelo {model_name} selecionado, mas a Chave de API do Gemini ainda não foi informada."
            return True, f"Mentor conectado ao {model_name} (Google Gemini Flash - Nuvem de Alta Velocidade)"
        
        return True, f"Mentor configurado para o modelo local {model_name} (Ollama)"

    # -------------------------------------------------------------
    # Invocação do Google Gemini Flash REST API
    # -------------------------------------------------------------
    def _call_gemini(self, prompt, system_prompt=None, temperature=0.2, timeout=120, model=None, history=None):
        """Executa chamada direta à API REST do Google Gemini Flash com retry inteligente."""
        api_key = self.get_gemini_key()
        if not api_key:
            raise ValueError("Chave de API do Gemini não configurada. Adicione sua chave para usar o Gemini Flash.")

        model_name = model or self.current_model
        if not self.is_gemini_model(model_name) or model_name not in GEMINI_MODELS:
            model_name = DEFAULT_GEMINI_MODEL

        # URL oficial da API Gemini v1beta generateContent
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        # Montagem dos contents com histórico
        contents = []
        if history and isinstance(history, list):
            for h in history[-6:]:
                role = "user" if h.get("role") == "user" else "model"
                txt = h.get("content", "").strip()
                if txt:
                    contents.append({
                        "role": role,
                        "parts": [{"text": txt}]
                    })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_prompt or SYSTEM_PROMPT_CONSINCO}]
            },
            "generationConfig": {
                "temperature": temperature,
                "topP": 0.95,
                "maxOutputTokens": 4096
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ZonaSQL-Consinco/2.0"
            }
        )

        last_error = None
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return "Não foi possível gerar resposta do Gemini Flash."
                    
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
                    return ""
            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8")
                try:
                    err_json = json.loads(err_body)
                    msg = err_json.get("error", {}).get("message", err_body)
                except Exception:
                    msg = err_body
                if he.code in (429, 503) and attempt == 0:
                    time.sleep(1.5)
                    continue
                raise RuntimeError(f"Erro na API do Gemini ({he.code}): {msg}")
            except Exception as e:
                last_error = e
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                raise RuntimeError(f"Erro de conexão com Gemini Flash: {str(e)}")

        raise RuntimeError(f"Erro de conexão com Gemini Flash: {str(last_error)}")

    # -------------------------------------------------------------
    # Invocação do Ollama Local
    # -------------------------------------------------------------
    def _call_ollama(self, prompt, system_prompt=None, temperature=0.2, timeout=180, max_tokens=2048):
        """Executa a chamada HTTP para /api/generate do Ollama local."""
        url = f"{self.ollama_base_url}/api/generate"
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
            headers={"Content-Type": "application/json", "User-Agent": "ZonaSQL-Mentor/2.0"}
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()

    # -------------------------------------------------------------
    # Roteador de Inferência (Gemini vs Ollama)
    # -------------------------------------------------------------
    def _generate(self, prompt, system_prompt=None, temperature=0.2, history=None):
        """Roteia a geração para o Gemini Flash ou Ollama de acordo com o modelo selecionado."""
        if self.is_gemini_model():
            return self._call_gemini(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                history=history
            )
        else:
            return self._call_ollama(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature
            )

    def test_gemini_connection(self, api_key=None, model=None):
        """Testa se uma chave da API do Gemini está válida e mede a latência."""
        target_key = api_key or self.get_gemini_key()
        if not target_key:
            return {"success": False, "error": "Nenhuma chave informada para teste."}

        target_model = model or DEFAULT_GEMINI_MODEL
        if target_model not in GEMINI_MODELS:
            target_model = DEFAULT_GEMINI_MODEL

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={target_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": "Responda apenas com a palavra OK."}]}],
            "generationConfig": {"maxOutputTokens": 10, "temperature": 0.0}
        }

        start = time.time()
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                elapsed_ms = round((time.time() - start) * 1000, 1)
                self.config["last_gemini_latency_ms"] = elapsed_ms
                self._save_config()
                return {
                    "success": True,
                    "latency_ms": elapsed_ms,
                    "model": target_model,
                    "message": f"Conexão com {target_model} realizada com sucesso em {elapsed_ms}ms!"
                }
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8")
            try:
                msg = json.loads(err_body).get("error", {}).get("message", err_body)
            except Exception:
                msg = err_body
            return {"success": False, "error": f"Erro HTTP {he.code}: {msg}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------
    # Métodos de Negócio do Mentor Consinco
    # -------------------------------------------------------------
    def chat(self, user_message, current_sql="", history=None):
        """Conversação interativa com o Mentor IA."""
        if self.is_gemini_model() and not self.get_gemini_key():
            return {
                "success": False,
                "requires_key": True,
                "error": "Chave da API Google Gemini não configurada. Por favor, insira sua chave gratuita do Google AI Studio para ativar o Gemini Flash."
            }

        start_time = time.time()
        
        context_parts = []
        if current_sql and current_sql.strip():
            context_parts.append(f"--- SQL ATUAL NO EDITOR DO USUÁRIO ---\n{current_sql.strip()}\n--------------------------------------")

        if not self.is_gemini_model() and history and isinstance(history, list):
            context_parts.append("--- HISTÓRICO DA CONVERSA RECENTE ---")
            for h in history[-4:]:
                role = "Usuário" if h.get("role") == "user" else "Mentor IA"
                context_parts.append(f"{role}: {h.get('content', '')}")
            context_parts.append("-------------------------------------")

        context_str = "\n\n".join(context_parts)
        full_prompt = f"{context_str}\n\nPergunta do Usuário: {user_message}\n\nResposta do Mentor IA:" if context_str else f"Pergunta do Usuário: {user_message}\n\nResposta do Mentor IA:"

        try:
            response_text = self._generate(
                prompt=full_prompt,
                temperature=0.3,
                history=history if self.is_gemini_model() else None
            )
            
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
                "provider": "gemini" if self.is_gemini_model() else "ollama",
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro na inferência do modelo {self.current_model}: {str(e)}"
            }

    def explain_and_fix_error(self, sql, error_msg, binds=None):
        """Diagnostica erros de execução Oracle/Consinco e gera a correção automática."""
        if self.is_gemini_model() and not self.get_gemini_key():
            return {
                "success": False,
                "requires_key": True,
                "error": "Chave da API Google Gemini não configurada. Por favor, insira sua chave gratuita do Google AI Studio para ativar o Gemini Flash."
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
            response_text = self._generate(prompt, temperature=0.1)
            
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
                "provider": "gemini" if self.is_gemini_model() else "ollama",
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao analisar com IA: {str(e)}"
            }

    def text_to_sql(self, natural_language_request):
        """Transforma um pedido em linguagem natural em SQL Consinco/Oracle com explicação."""
        if self.is_gemini_model() and not self.get_gemini_key():
            return {
                "success": False,
                "requires_key": True,
                "error": "Chave da API Google Gemini não configurada. Por favor, insira sua chave gratuita do Google AI Studio para ativar o Gemini Flash."
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
            response_text = self._generate(prompt, temperature=0.2)
            
            sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, flags=re.DOTALL | re.IGNORECASE)
            generated_sql = sql_match.group(1).strip() if sql_match else ""

            elapsed = round(time.time() - start_time, 2)
            return {
                "success": True,
                "generated_sql": generated_sql,
                "explanation": response_text,
                "request": natural_language_request,
                "model": self.current_model,
                "provider": "gemini" if self.is_gemini_model() else "ollama",
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao gerar SQL com IA: {str(e)}"
            }

    def find_table(self, intent_or_keyword):
        """Localiza a tabela e as colunas certas a partir de uma dúvida de negócio."""
        if self.is_gemini_model() and not self.get_gemini_key():
            return {
                "success": False,
                "requires_key": True,
                "error": "Chave da API Google Gemini não configurada. Por favor, insira sua chave gratuita do Google AI Studio para ativar o Gemini Flash."
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
            response_text = self._generate(prompt, temperature=0.2)
            
            sql_match = re.search(r"```sql\s*(.*?)\s*```", response_text, flags=re.DOTALL | re.IGNORECASE)
            sample_sql = sql_match.group(1).strip() if sql_match else ""

            elapsed = round(time.time() - start_time, 2)
            return {
                "success": True,
                "answer": response_text,
                "sample_sql": sample_sql,
                "query": intent_or_keyword,
                "model": self.current_model,
                "provider": "gemini" if self.is_gemini_model() else "ollama",
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro ao buscar tabela com IA: {str(e)}"
            }

# Instância global singleton do Mentor
ollama_mentor = UnifiedMentorService()
