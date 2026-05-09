"""
Resumo de E-mails com IA (Gemini)
==================================
Uso:
    python resumo_email.py              # interface web local (padrao)
    python resumo_email.py --limite 20
    python resumo_email.py --so-nao-lidos
    python resumo_email.py --terminal   # saida no terminal
"""

import base64
import re
import argparse
import time
import json
import os
import html
import webbrowser
import urllib.parse
import urllib.request
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from autenticacao_google import get_google_credentials

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _decodificar_header(valor):
    from email.header import decode_header as _dh
    partes = _dh(valor)
    resultado = []
    for dados, charset in partes:
        if isinstance(dados, bytes):
            resultado.append(dados.decode(charset or "utf-8", errors="replace"))
        else:
            resultado.append(dados)
    return "".join(resultado)


def _extrair_texto_plain(payload):
    if isinstance(payload, list):
        for parte in payload:
            texto = _extrair_texto_plain(parte)
            if texto:
                return texto
        return ""
    mime_type = payload.get("mimeType", "")
    corpo = payload.get("body", {})
    if mime_type == "text/plain" and corpo.get("data"):
        dados = base64.urlsafe_b64decode(corpo["data"] + "==")
        return dados.decode("utf-8", errors="replace")
    if mime_type.startswith("multipart/"):
        for parte in payload.get("parts", []):
            texto = _extrair_texto_plain(parte)
            if texto:
                return texto
    return ""


def _limpar_texto(texto, max_chars=3000):
    linhas = texto.splitlines()
    linhas_uteis = [l.strip() for l in linhas if len(l.strip()) > 2]
    texto_limpo = " ".join(linhas_uteis)
    texto_limpo = re.sub(r" {2,}", " ", texto_limpo)
    return texto_limpo[:max_chars]


def _resumir_com_gemini(assunto, remetente, corpo):
    try:
        from google import genai as gai
        client = gai.Client(api_key=GEMINI_API_KEY)
        prompt = (
            "Voce e um assistente pessoal. Resuma o e-mail abaixo em portugues do Brasil "
            "em no maximo 3 frases objetivas. Nao use bullet points, escreva em paragrafo unico.\n\n"
            f"Assunto: {assunto}\n"
            f"Remetente: {remetente}\n\n"
            f"Corpo:\n{corpo}"
        )
        resposta = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )
        texto = resposta.text.strip()
        time.sleep(1)
        return texto
    except ImportError:
        return "[Instale 'google-genai': pip install google-genai]"
    except Exception as exc:
        return f"[Erro ao gerar resumo: {exc}]"


def _resumir_sem_ia(corpo):
    if not corpo:
        return "(sem conteudo legivel)"
    return corpo[:250].strip() + ("..." if len(corpo) > 250 else "")


def _falha_ia(texto):
    return texto.startswith("[Erro ao gerar resumo:") or texto.startswith("[Instale 'google-genai'")


def _traduzir_ptbr(texto):
    if not texto:
        return texto

    try:
        query = urllib.parse.quote(texto)
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=auto&tl=pt&dt=t&q={query}"
        )
        with urllib.request.urlopen(url, timeout=12) as resposta:
            payload = resposta.read().decode("utf-8", errors="replace")

        dados = json.loads(payload)
        partes = dados[0] if dados and isinstance(dados, list) else []
        traduzido = "".join(parte[0] for parte in partes if parte and isinstance(parte, list))
        return traduzido.strip() if traduzido else texto
    except Exception:
        return texto


def _mover_para_lixeira(message_id):
    cred = get_google_credentials()
    service = build("gmail", "v1", credentials=cred)
    try:
        service.users().messages().trash(userId="me", id=message_id).execute()
    except HttpError as exc:
        texto = str(exc)
        if "insufficientPermissions" in texto or "Insufficient Permission" in texto:
            raise RuntimeError(
                "Permissao insuficiente para excluir e-mail. Feche o app, apague o arquivo token.json "
                "em Aplicativos/integracao_google/ e execute novamente para reautorizar."
            ) from exc
        raise


def _coletar_resumos(limite=20, so_nao_lidos=False, page_token="", usar_ia=None, traduzir=True, manutencao_rapida=False):
    if usar_ia is None:
        usar_ia = bool(GEMINI_API_KEY)
    cred = get_google_credentials()
    service = build("gmail", "v1", credentials=cred)
    labels = ["INBOX"]
    if so_nao_lidos:
        labels.append("UNREAD")

    req = service.users().messages().list(userId="me", labelIds=labels, maxResults=limite)
    if page_token:
        req = req.pageToken(page_token)
    resultado = req.execute()
    mensagens = resultado.get("messages", [])
    next_page_token = resultado.get("nextPageToken", "")

    resumos = []
    for idx, msg_ref in enumerate(mensagens, start=1):
        formato = "metadata" if manutencao_rapida else "full"
        msg = service.users().messages().get(userId="me", id=msg_ref["id"], format=formato).execute()
        headers = msg.get("payload", {}).get("headers", [])
        assunto   = "Sem Assunto"
        remetente = "Desconhecido"
        data_hora = ""
        for h in headers:
            nome = h["name"].lower()
            if nome == "subject":
                assunto = _decodificar_header(h["value"])
            elif nome == "from":
                remetente = _decodificar_header(h["value"])
            elif nome == "date":
                data_hora = h["value"]
        if manutencao_rapida:
            snippet = (msg.get("snippet") or "").strip()
            resumo = snippet if snippet else "(sem resumo rapido)"
        else:
            corpo_raw = _extrair_texto_plain(msg.get("payload", {}))
            corpo_limpo = _limpar_texto(corpo_raw)
            resumo = _resumir_com_gemini(assunto, remetente, corpo_limpo) if usar_ia else _resumir_sem_ia(corpo_limpo)
            if usar_ia and _falha_ia(resumo):
                resumo_local = _resumir_sem_ia(corpo_limpo)
                resumo = f"{resumo_local} [fallback local]"

        if traduzir:
            assunto_pt = _traduzir_ptbr(assunto)
            resumo_pt = _traduzir_ptbr(resumo)
        else:
            assunto_pt = assunto
            resumo_pt = resumo

        resumos.append(
            {
                "indice": idx,
                "data_hora": data_hora,
                "remetente": remetente,
                "assunto": assunto_pt,
                "resumo": resumo_pt,
                "message_id": msg_ref["id"],
            }
        )

    return {
        "modo": "IA Gemini" if usar_ia else "Texto direto (sem chave Gemini)",
        "limite": limite,
        "so_nao_lidos": so_nao_lidos,
        "page_token": page_token,
        "next_page_token": next_page_token,
        "itens": resumos,
    }


def _mostrar_terminal(dados):
    limite = dados["limite"]
    so_nao_lidos = dados["so_nao_lidos"]

    print(f"\n{'='*60}")
    print(f"  RESUMO DE E-MAILS  |  Ultimos {limite} {'(nao lidos)' if so_nao_lidos else ''}")
    print(f"  Modo: {dados['modo']}")
    print(f"{'='*60}\n")

    if not dados["itens"]:
        print("Nenhum e-mail encontrado.")
        return

    for item in dados["itens"]:
        print(f"[{item['indice']:02d}] {item['data_hora']}")
        print(f"  De      : {item['remetente']}")
        print(f"  Assunto : {item['assunto']}")
        print(f"  Resumo  : {item['resumo']}")
        print(f"{'-'*60}\n")


def resumir_emails(limite=10, so_nao_lidos=False):
    dados = _coletar_resumos(limite=limite, so_nao_lidos=so_nao_lidos)
    _mostrar_terminal(dados)


def _renderizar_html(dados, mensagem=""):
    page_token = dados.get("page_token", "")
    next_page_token = dados.get("next_page_token", "")
    link_recentes = f"/?limit={dados['limite']}&nao_lidos={1 if dados['so_nao_lidos'] else 0}"
    link_atualizar = (
        f"/?limit={dados['limite']}&nao_lidos={1 if dados['so_nao_lidos'] else 0}"
        f"&token={urllib.parse.quote(page_token)}"
    )
    link_antigos = ""
    if next_page_token:
        link_antigos = (
            f"/?limit={dados['limite']}&nao_lidos={1 if dados['so_nao_lidos'] else 0}"
            f"&token={urllib.parse.quote(next_page_token)}"
        )

    itens_html = []
    for item in dados["itens"]:
        card = f"""
        <section class='card'>
            <div class='topo-card'>
                <label class='check-wrap'>
                    <input class='check-item' type='checkbox' name='ids' value='{html.escape(item['message_id'])}' onchange='atualizarBotaoLote()'>
                    <span>Selecionar</span>
                </label>
                <div class='meta'>[{item['indice']:02d}] {html.escape(item['data_hora'])}</div>
                <a class='btn-excluir' href='/delete?id={urllib.parse.quote(item['message_id'])}&limit={dados['limite']}&nao_lidos={1 if dados['so_nao_lidos'] else 0}&token={urllib.parse.quote(page_token)}'>Excluir</a>
            </div>
            <h3>{html.escape(item['assunto'])}</h3>
            <p><strong>De:</strong> {html.escape(item['remetente'])}</p>
            <p><strong>Resumo:</strong> {html.escape(item['resumo'])}</p>
        </section>
        """
        itens_html.append(card)

    if not itens_html:
        itens_html.append("<p class='vazio'>Nenhum e-mail encontrado.</p>")

    aviso = f"<div class='msg'>{html.escape(mensagem)}</div>" if mensagem else ""
    return f"""
<!doctype html>
<html lang='pt-BR'>
<head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>Resumo de E-mails</title>
    <style>
        :root {{
            --bg: #0b1220;
            --card: #172033;
            --text: #e5e7eb;
            --muted: #9ca3af;
            --accent: #38bdf8;
            --danger: #ef4444;
            --ok: #22c55e;
        }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; background: radial-gradient(circle at 20% 20%, #1f2937, var(--bg)); color: var(--text); }}
        header {{ position: sticky; top: 0; z-index: 10; background: rgba(11,18,32,.92); backdrop-filter: blur(4px); padding: 16px 20px; border-bottom: 1px solid #263042; }}
        .linha {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
        h1 {{ margin: 0; font-size: 28px; }}
        .sub {{ color: var(--muted); font-size: 14px; }}
        .acoes {{ margin-left: auto; display: flex; gap: 8px; }}
        .btn {{ border: 0; border-radius: 10px; padding: 10px 14px; font-weight: 700; cursor: pointer; text-decoration: none; color: white; display: inline-block; }}
        .btn-full {{ background: #2563eb; }}
        .btn-refresh {{ background: #0ea5e9; }}
        .btn-home {{ background: #334155; }}
        .btn-more {{ background: #7c3aed; }}
        .btn-batch {{ background: #b91c1c; }}
        .btn-batch:disabled {{ opacity: .5; cursor: not-allowed; }}
        .msg {{ margin: 16px 20px; padding: 12px 14px; background: rgba(34,197,94,.14); border: 1px solid rgba(34,197,94,.45); border-radius: 10px; color: #dcfce7; }}
        main {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: linear-gradient(180deg, #1f2937, var(--card)); border: 1px solid #2a364a; border-radius: 14px; padding: 14px; margin-bottom: 14px; }}
        .topo-card {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; }}
        .meta {{ color: var(--accent); font-weight: 700; font-size: 13px; }}
        .btn-excluir {{ background: var(--danger); color: white; text-decoration: none; padding: 8px 12px; border-radius: 10px; font-weight: 700; }}
        .check-wrap {{ display: flex; gap: 6px; align-items: center; color: #cbd5e1; font-size: 13px; }}
        .acoes-lote {{ margin: 12px 20px 0; display: flex; gap: 10px; align-items: center; }}
        h3 {{ margin: 8px 0; font-size: 20px; }}
        p {{ margin: 6px 0; line-height: 1.5; }}
        .vazio {{ color: var(--muted); font-size: 18px; }}
    </style>
</head>
<body>
    <header>
        <div class='linha'>
            <div>
                <h1>Resumo de E-mails</h1>
                <div class='sub'>Modo: {html.escape(dados['modo'])} | Quantidade: {len(dados['itens'])}</div>
                <div class='sub'>Visualizacao rapida para manutencao (mais desempenho para excluir em lote).</div>
            </div>
            <div class='acoes'>
                <a class='btn btn-home' href='{link_recentes}'>Mais recentes</a>
                {f"<a class='btn btn-more' href='{link_antigos}'>Mais antigos</a>" if link_antigos else ""}
                <a class='btn btn-refresh' href='{link_atualizar}'>Atualizar</a>
                <button class='btn btn-full' onclick='document.documentElement.requestFullscreen()'>Tela Cheia</button>
            </div>
        </div>
    </header>
    {aviso}
    <form id='lote-form' method='post' action='/delete-batch'>
        <input type='hidden' name='limit' value='{dados['limite']}'>
        <input type='hidden' name='nao_lidos' value='{1 if dados['so_nao_lidos'] else 0}'>
        <input type='hidden' name='token' value='{html.escape(page_token)}'>
        <div class='acoes-lote'>
            <label class='check-wrap'>
                <input id='check-all' type='checkbox' onchange='marcarTodos(this.checked)'>
                <span>Marcar todos na página</span>
            </label>
            <button id='btn-batch' class='btn btn-batch' type='submit' disabled>Excluir selecionados</button>
        </div>
    <main>
        {''.join(itens_html)}
    </main>
    </form>
    <script>
        function itens() {{ return Array.from(document.querySelectorAll('.check-item')); }}
        function atualizarBotaoLote() {{
            const selecionados = itens().filter(i => i.checked).length;
            const btn = document.getElementById('btn-batch');
            btn.disabled = selecionados === 0;
            btn.textContent = selecionados > 0 ? `Excluir selecionados (${selecionados})` : 'Excluir selecionados';
        }}
        function marcarTodos(marcar) {{
            itens().forEach(i => i.checked = marcar);
            atualizarBotaoLote();
        }}
        document.getElementById('lote-form').addEventListener('submit', function (ev) {{
            const selecionados = itens().filter(i => i.checked).length;
            if (selecionados === 0) {{
                ev.preventDefault();
                return;
            }}
            if (!confirm(`Deseja mover ${selecionados} e-mail(s) para a lixeira?`)) {{
                ev.preventDefault();
            }}
        }});
    </script>
</body>
</html>
"""


def iniciar_interface_web(limite=20, so_nao_lidos=False, porta=8765):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _fmt, *_args):
            return

        def _contexto(self, q):
            limite_req = int(q.get("limit", [str(limite)])[0])
            nao_lidos_req = q.get("nao_lidos", ["1" if so_nao_lidos else "0"])[0] == "1"
            token_req = q.get("token", [""])[0]
            return limite_req, nao_lidos_req, token_req

        def do_GET(self):
            try:
                parsed = urlparse(self.path)
                rota = parsed.path
                q = parse_qs(parsed.query)
                limite_req, nao_lidos_req, token_req = self._contexto(q)

                if rota == "/delete":
                    msg_id = q.get("id", [""])[0]
                    if msg_id:
                        _mover_para_lixeira(msg_id)
                    destino = (
                        f"/?limit={limite_req}&nao_lidos={1 if nao_lidos_req else 0}"
                        f"&token={urllib.parse.quote(token_req)}&msg="
                        + urllib.parse.quote("E-mail movido para a lixeira.")
                    )
                    self.send_response(302)
                    self.send_header("Location", destino)
                    self.end_headers()
                    return

                dados = _coletar_resumos(
                    limite=limite_req,
                    so_nao_lidos=nao_lidos_req,
                    page_token=token_req,
                    usar_ia=False,
                    traduzir=False,
                    manutencao_rapida=True,
                )
                msg = q.get("msg", [""])[0]
                pagina = _renderizar_html(dados, mensagem=msg)
                conteudo = pagina.encode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(conteudo)))
                self.end_headers()
                self.wfile.write(conteudo)
            except Exception as exc:
                erro = f"<h1>Erro</h1><pre>{html.escape(str(exc))}</pre>".encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(erro)))
                self.end_headers()
                self.wfile.write(erro)

        def do_POST(self):
            try:
                parsed = urlparse(self.path)
                if parsed.path != "/delete-batch":
                    self.send_response(404)
                    self.end_headers()
                    return

                tamanho = int(self.headers.get("Content-Length", "0"))
                corpo = self.rfile.read(tamanho).decode("utf-8", errors="replace")
                q = parse_qs(corpo)
                limite_req, nao_lidos_req, token_req = self._contexto(q)
                ids = q.get("ids", [])

                excluidos = 0
                for msg_id in ids:
                    if msg_id:
                        _mover_para_lixeira(msg_id)
                        excluidos += 1

                msg = urllib.parse.quote(f"{excluidos} e-mail(s) movido(s) para a lixeira.")
                destino = (
                    f"/?limit={limite_req}&nao_lidos={1 if nao_lidos_req else 0}"
                    f"&token={urllib.parse.quote(token_req)}&msg={msg}"
                )
                self.send_response(302)
                self.send_header("Location", destino)
                self.end_headers()
            except Exception as exc:
                erro = f"<h1>Erro</h1><pre>{html.escape(str(exc))}</pre>".encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(erro)))
                self.end_headers()
                self.wfile.write(erro)

    servidor = HTTPServer(("127.0.0.1", porta), Handler)
    url = f"http://127.0.0.1:{porta}/?limit={limite}&nao_lidos={1 if so_nao_lidos else 0}"
    print(f"Interface web iniciada em: {url}")
    webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resumo de e-mails com Gemini")
    parser.add_argument("--limite", type=int, default=20)
    parser.add_argument("--so-nao-lidos", action="store_true")
    parser.add_argument("--terminal", action="store_true", help="Exibe no terminal em vez da interface web")
    parser.add_argument("--porta", type=int, default=8765, help="Porta da interface web local")
    args = parser.parse_args()
    if args.terminal:
        resumir_emails(limite=args.limite, so_nao_lidos=args.so_nao_lidos)
    else:
        iniciar_interface_web(limite=args.limite, so_nao_lidos=args.so_nao_lidos, porta=args.porta)
