# Aprendizados e Padrões - APP Baklizi WMS

Este documento registra as correções críticas realizadas no desenvolvimento do APP Baklizi WMS para evitar que os mesmos erros sejam cometidos novamente. Siga rigorosamente essas diretrizes ao atuar no projeto.

## 1. Servidor e Uvicorn (Evitar Quedas no Upload)
**O Erro:** Ao usar `uvicorn.run(..., reload=True)`, o servidor monitorava todo o diretório raiz. Qualquer upload de arquivo de dados (`.parquet`, `.csv`, `.xls`) salvo nas pastas `data/` ou `bdados/` fazia o Uvicorn reiniciar o servidor imediatamente, quebrando a requisição do usuário (o frontend ficava travado no "Fazendo upload..." por conta da queda da conexão).
**A Solução / Regra:** 
- NUNCA use `reload=True` sem restrições. 
- Sempre utilize o parâmetro `reload_dirs=["api", "static", "services", "utils"]` no `uvicorn.run()` (dentro de `server.py`) para garantir que o Uvicorn assista apenas os arquivos de código, ignorando bancos de dados e parquets.

## 2. Experiência de Usuário e Notificações (Pop-ups Modais)
**O Erro:** A função `registrar_atualizacao()` da `system_service.py` força um pop-up na tela de todos os usuários conectados pedindo para atualizar a página (F5). Ao colocar essa função no final de um endpoint de upload de arquivos (`admin.py`), o próprio administrador que fez o upload era interrompido abruptamente pela mensagem, atrapalhando a experiência (dando a falsa impressão de que o sistema caiu).
**A Solução / Regra:**
- Não invoque `registrar_atualizacao()` em endpoints acionados diretamente por ação manual do administrador (como upload de planilhas locais). 
- O backend deve apenas retornar a resposta de sucesso para o frontend, e o frontend se encarrega de atualizar o status na tela silenciosamente (ex: barra superior atualiza o horário com base em nova checagem no `/status`).

## 3. Arquivos Grandes e Git
**O Erro:** Arquivos de banco de dados (`baklizi.db`) e planilhas gigantes de exportação (ex: templates CSV de mais de 100MB) tentavam subir para o GitHub durante comandos de commit automatizados (como `Commint_Push.py`), estourando o limite de tamanho do GitHub. Além disso, a pasta `APP_Bak` se comportou como um submódulo, impedindo commits da raiz.
**A Solução / Regra:**
- Bancos de dados (`*.db`, `*-wal`, `*-shm`, `*.corrompido`) e planilhas massivas de consumo devem sempre estar adicionados explicitamente no `.gitignore` (`bdados/*.db`, `doc/templates_appsheet/*.csv`).
- Se houver conflitos no push de `APP_Bak`, resolva-os diretamente dentro da pasta `Aplicativos/APP_Bak`.

## 4. Interpolação no JavaScript (Sintaxe HTML)
**O Erro:** Montagem de grandes blocos HTML dentro de requisições `fetch` no `app.js` usando aspas duplas `""` ou simples `''` quebrando o código caso houvessem quebras de linha (`SyntaxError`).
**A Solução / Regra:**
- Ao renderizar HTML dinâmico ou concatenar strings longas no JS, use ESTRITAMENTE *Template Literals* (crases: ```` ` ````).

## 5. UI de Módulos Incompletos
**O Erro:** Colocar descrições longas parecendo módulos funcionais na UI para áreas que não possuem rotas configuradas (ex: `pleno.parquet` e `query.parquet` na tela do Free Shop) gera frustração no usuário e falsas expectativas.
**A Solução / Regra:**
- Remova da tela (esconda no HTML) qualquer bloco ou botão que ainda não tenha implementação real de Backend conectada, mantendo a interface o mais limpa e focada no que funciona.
