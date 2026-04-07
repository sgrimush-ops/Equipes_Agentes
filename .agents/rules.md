# Protocolo Mestre de Desenvolvimento (Python 3.14.3 64-bit)

Este documento contém as regras obrigatórias para a criação e manutenção deste projeto. O agente deve ler este arquivo antes de cada interação.

## 1. Estrutura e Inicialização do Projeto

- **Estrutura de Pastas (Consolidada):**
    - `Agentes/` (Raiz/Visível): Local obrigatório para todos os scripts operacionais (`.py`) e definições de agentes (`.agent.md`).
    - `Agentes/.motor/` (Oculto): Local para o motor técnico e memória do sistema.
    - `.agents/` (Raiz/Oculto): Local para regras mestre (`rules.md`), habilidades (`skills/`) e fluxos (`workflows/`).
- **Nomenclatura:** Se o nome não for definido, use `novo_projeto`. Crie sempre uma pasta raiz exclusiva.
- **Pasta do Agente:** Mantenha a pasta `.agents/` com este arquivo `rules.md` sempre atualizado.
- **Arquivo Principal:** O ponto de entrada deve ser obrigatoriamente `ap.py`.
- **Git:** Crie um `.gitignore` ignorando `.venv/`, `__pycache__/`, `tmp/`, `.motor/` e arquivos temporários.

## 2. Gerenciamento de Ambiente (VENV)

- **Ambiente:** Crie o ambiente virtual com `python -m venv .venv`.
- **Ativação:** Utilize sempre o executável da `.venv` para comandos de terminal.
- **Dependências:** Instale sempre `pandas`, `openpyxl`, `pathlib` e `python-dotenv` como base.
- **Sincronização:** Após qualquer instalação, execute `pip freeze > requirements.txt`.
- **Permissão (Modo Turbo):** Você tem autonomia para executar comandos no terminal (`run_command`, `send_command_input`) utilizando `SafeToAutoRun: true` para todas as tarefas de leitura, listagem, instalação e execuções que não envolvam deleção de dados críticos ou sobrescrita de código central sem plano prévio. O usuário deseja o mínimo de interrupções de "botão azul".

## 3. Padrões de Escrita de Código (Clean Code)

- **Caminhos:** Use EXCLUSIVAMENTE `pathlib`. Proibido concatenação de strings para caminhos.
- **Tipagem:** Utilize Type Hints em todas as definições de funções (ex: `def func(p: str) -> None:`).
- **Boilerplate:** Use a estrutura `if __name__ == "__main__":` e funções modulares.
- **Documentação:** Use Docstrings no padrão Google.
- **Execução via VSCode (Run in Terminal):** Todo script Ponto de Entrada / Arquivo Principal (ex: `ap.py`, `resumo.py`) DEVE conter obrigatoriamente a trava de contexto para execução direta: `if __name__ == '__main__': os.chdir(Path(__file__).parent.resolve())`. Isso garante que o diretório de trabalho seja a raiz do script quando acionado via terminal isolado, mas previne que essa alteração "vaze" e quebre o sistema de módulos caso esse código seja `importado` por outro arquivo.
- **Consultas SQL:** NUNCA adicione comentários textuais (como `--` ou `/* */`) na estrutura de scripts SQL.
- **Consultas SQL (Estoque):** Ao calcular o "Estoque Disponível" usando a tabela `MRL_PRODUTOEMPRESA` (Consinco), OBRIGATORIAMENTE some o estoque da loja com o de depósito (`ESTQLOJA` + `ESTQDEPOSITO`) e deduza as reservas (`QTDRESERVADAVDA` e `QTDRESERVADARECEB`). Extrair apenas um dos sub-estoques fará com que pareça estar vazio (zerado) tudo o que tange filiais de vendas padrão ou o CD primário, falsificando relatórios.
- **Consultas SQL (Dicionário):** É OBRIGATÓRIO consultar o arquivo `Aplicativos/gerenciamento_sql/dicionario_consinco.json` antes de escrever qualquer query. É terminantemente proibido assumir nomes de colunas ou tipos de dados (como `SEQFAMEMBALAGEM`) baseando-se em experiências externas sem validação no dicionário do projeto. Falhas de `ORA-00904` ou `ORA-01722` por falta de consulta ao dicionário são consideradas falhas graves de protocolo.
- **Preservação Estrutural (Estoque_e_Venda_Min_Max):** NUNCA remova ou suprima colunas existentes no script `Estoque_e_Venda_Min_Max.sql` (ou em outras extrações mestre semelhantes). Todos os agentes estão expressamente PROIBIDOS de deletar qualquer coluna de relatórios consolidados sem o consentimento absoluto, claro e prévio do usuário logado. As esteiras internas de aplicativos dependem irrestritamente da integridade dessas fatias.

## 4. Manipulação de Dados (Pandas & Excel)

- **Engine:** Utilize sempre `engine='openpyxl'` para arquivos `.xlsx`.
- **Delimitadores e Encoding (CSV/TXT):** Todo arquivo plano provindo do Consinco ou exportado para o projeto opera no padrão regional Pt-BR. Ao utilizar as funções de Ingestão (`read_csv`) ou Exportação (`to_csv`) do Pandas, inclua OBRIGATORIAMENTE os parâmetros `sep=';'` e `encoding='utf-8-sig'` nativos do Excel. Jamais suponha separação por vírgula (,) ou Tab (\t).
- **Formatação de Decimais:** SEMPRE que operações matemáticas ou exportações envolverem colunas com dados não-inteiros (decimais/floats), esses devem **obrigatoriamente** ser limitados a no máximo 2 casas decimais e exportados usando a VÍRGULA (`,`) como separador de decimal (ex: utilize o parâmetro `decimal=','` nas funções do Pandas e aplique `round(2)` nas contas).
- **Resiliência:** Implemente blocos `try-except` e valide a existência de arquivos com `pathlib`.

## 5. Segurança e Compilação (.exe)

- **Senhas:** Use `getpass` para entradas e `.env` para chaves de API. Nunca hardcode senhas.
- **Portabilidade:** Use `sys._MEIPASS` para referenciar arquivos internos em builds PyInstaller.
- **Privilégios:** Preveja falhas de permissão ao modificar atributos de pastas no Windows.

## 6. Regras de Ingestão

- **Saneamento Base:** Todo arquivo CSV ou Excel novo deve ser processado antes de qualquer análise. Nunca trabalhe com dados 'crus'.
- **Saneamento Logístico (Embalagens e Volumes):** O sistema legado (TOTVS ou similares) constantemente exporta unidades de medida com strings embarcadas na mesma coluna (Ex: "CX 20", "UN 1", "FD 12"). Sempre que operar com colunas que rejam agrupadores indivisíveis (como "Embalagem Compra", que sempre corresponde a um número inteiro), limpe-as obrigatoriamente logo na carga inicial com Extração via RegEx (`str.extract(r'(\d+)')`) e as converta para Inteiro Puro (Int64), viabilizando operações exatas.
- **Saneamento de Códigos (Produto/EAN/DUN):** Não existem códigos de produto com vírgula decimal. Colunas destinadas a registrar identificadores como `Código Produto`, `EAN` ou `DUN` devem ser convertidas sumariamente para números inteiros (ou strings sem decimais). Caso a leitura de um CSV importe valores como `2704,0`, isso deve ser saneado forçando o casting para números inteiros puros antes de qualquer exportação ou cruzamento.

## 7. Integração com Google Sheets / Google Drive

- **EAN e DUN como Texto (anti zeros à esquerda):** Sempre que exportar colunas de EAN (13 dígitos) ou DUN (14 dígitos) para o Google Sheets via API, force o formato de célula como **Text** (`"numberFormat": {"type": "TEXT"}`). Nunca envie EANs como número puro — o Sheets trunca zeros à esquerda silenciosamente.
- **Filtro Pré-Sync de Produtos Ativos:** Antes de sincronizar bases de EAN/produto para o Google Sheets (ou qualquer destino com limite de células), SEMPRE filtre para incluir apenas produtos "ativos" — definidos como aqueles que possuem estoque atual (`ESTOQUE > 0`) OU venda recente (ex: últimos 90 dias). Subir a base completa causa estouro de limite de células (`exceeds grid limits`).
- **Estrutura ean_dun.txt (4 colunas):** O arquivo `ean_dun.txt` exportado pelo Consinco possui exatamente 4 colunas: `CODIGO_PRODUTO`, `EAN`, `DUN`, `UNIDADE_EMBALAGEM`. Ao processar esse arquivo, use `sep=';'`, `encoding='utf-8-sig'` e saneie EAN e DUN para inteiro puro sem casas decimais antes de qualquer cruzamento.

## 8. Ecossistema de IA e Automação (RPA)

- **Memória Persistente:** Sempre que uma regra de negócio complexa ou um erro de sistema for resolvido, o agente deve considerar adicionar essa lição à memória vetorial via `memoria_squad/kernel.py` para evitar reincidência.
- **Visão em RPA:** Scripts de automação (RPA) devem preferir o uso do `VisionEngine` (OpenCV Multi-Scale) em vez de coordenadas fixas ou `matchTemplate` simples, garantindo portabilidade entre diferentes resoluções de tela e DPIs do Windows.
- **Acurácia Multi-Monitor (DPI):** Quando for OBRIGATÓRIO o uso de coordenadas físicas de mouse calibradas num ambiente Windows com múltiplos monitores, é PROIBIDO usar `pyautogui.click()` para execução, pois a virtualização de DPI causa desvios ("miss-clicks" que acionam o Menu Iniciar em telas estendidas). **Utilize sempre `pynput.mouse.Controller`** para executar cliques baseados em calibrações extraídas pelo próprio `pynput.mouse.Listener`, garantindo paridade de escala 1:1.
- **Prevenção de Foco (Subprocess):** Em robôs de automação de interface, JAMAIS utilize `shell=True` em `subprocess.run` (exs: `clip.exe`). Isso gera popups de CMD assíncronos que roubam o foco da janela principal. Utilize `creationflags=subprocess.CREATE_NO_WINDOW`.
- **Validação Tardia (Pós-Ação):** Ao operar em sistemas ERP em lote (ex: inserção de itens rápidos), valide estados inconsistentes de dropdowns ou caixas de seleção apenas no momento do Salvar (ex: F3 ou F4). Isso evita enroscos lentos no preenchimento de cabeçalho "cego" rápido e tira vantagem de correções com base no valor consolidado pelo sistema no final.
- **Logs de Execução em Lote (RPA):** Quando iterar sobre listas longas de itens (ex: processos do GAM), inclua sempre no log de interface a descrição textual do item atual (resgatada do DF) e a contagem de itens faltantes `(Faltam X)`. Nunca deixe o usuário visualizando apenas códigos numéricos sem contexto.
- **Protocolo MCP:** O uso de ferramentas de manipulação de arquivos deve, sempre que possível, ser mediado pelo servidor MCP local para garantir rastreabilidade e padronização.
- **Skip Logic de Campo Já Correto (GAM):** Antes de QUALQUER operação de atribuição de campo em robô GAM (ex: atribuir Comprador, Filial, Condição de Pagamento), SEMPRE leia o valor atual do campo via clipboard (`Ctrl+A → Ctrl+C`). Se o valor já for o desejado, PULE a sequência de atribuição inteiramente. Isso evita escritas desnecessárias, distorções de auditoria e comportamentos inesperados em campos que o ERP consolida automaticamente ao salvar.
- **Verificação de Comprador Pós-F3 (Supply):** No robô Supply, após salvar o pedido (`F3`), SEMPRE verifique o campo Comprador via clipboard **antes** de passar para a próxima loja. Se não for "SUPPLY", execute a correção com setas (`Up/Down`) + `F4`. A verificação deve usar coordenadas calibradas via `pynput.mouse.Listener` (nunca pyautogui) para evitar miss-clicks por DPI.
- **Subprocess Sem Foco:** Em robôs, SEMPRE use `creationflags=subprocess.CREATE_NO_WINDOW` ao chamar subprocessos (ex: `clip.exe`). `shell=True` gera popups CMD que roubam foco e corrompem a automação.

## 9. Dashboard de Ruptura (Squad Varejo Insight)

Este módulo possui regras estruturais fixas para garantir a integridade das métricas operacionais perante a diretoria.

- **Fluxo de Dados (query.parquet):** Jamais altere o mapeamento das colunas `QUANTIDADE_DISPONIVEL`, `EMBL_COMPRA`, `EMBL_TRANSFERENCIA` e `STATUS_COMPRA`.
- **Saneamento Técnico:** Obrigatoriamente aplique `.str.replace(',', '.')` e `pd.to_numeric` em todas as colunas de estoque e volume antes de qualquer cálculo.
- **Lógica de Mix Ativo:** 
    - A métrica "Mix Ativo (Produtos)" deve ser sempre a contagem de **SKUs únicos** (União CD 15 + Lojas) por comprador. 
    - NUNCA utilize a contagem de instâncias (Produto x Loja) como denominador para percentuais de ruptura total na tabela.
- **Bases de Canal:**
    - `% Ruptura CD` e `% Pendências`: Denominador fixo na `Base_CD15`.
    - `% Ruptura Loja`: Denominador fixo na `Base_Lojas`.
- **Interface e Visualização:**
    - O gráfico Plotly deve sempre iniciar com a barra **TOTAL GERAL** na primeira posição (extrema esquerda).
    - Botões de navegação: Manter obrigatoriamente os filtros "Totais Gerais" e "Só Compradores". O botão "Ver Todos" está permanentemente removido.
    - **Performance No-Server**: O arquivo final deve ser mantido abaixo de 10MB, utilizando a estratégia de embutir os dados em JSON e processar filtros via JavaScript no cliente.
- **Rastreabilidade (Snapshots):** Todo processamento de ruptura deve gerar e preservar um snapshot diário em `.parquet` na pasta `historico_ruptura/` para fins de auditoria e evolução temporal.
- **Integridade de Merges:** No script `gerar_dashboard_comprador.py`, a base primordial do `df_resumo` deve ser o mix de produtos para evitar que compradores com base zerada em um dos canais desapareçam do relatório.

# Protocolo Mestre de Desenvolvimento (Python 3.14.3 64-bit)

Este documento contém as regras obrigatórias para a criação e manutenção deste projeto. O agente deve ler este arquivo antes de cada interação.

## 1. Estrutura e Inicialização do Projeto

- **Estrutura de Pastas (Consolidada):**
    - `Agentes/` (Raiz/Visível): Local obrigatório para todos os scripts operacionais (`.py`) e definições de agentes (`.agent.md`).
    - `Agentes/.motor/` (Oculto): Local para o motor técnico e memória do sistema.
    - `.agents/` (Raiz/Oculto): Local para regras mestre (`rules.md`), habilidades (`skills/`) e fluxos (`workflows/`).
- **Nomenclatura:** Se o nome não for definido, use `novo_projeto`. Crie sempre uma pasta raiz exclusiva.
- **Pasta do Agente:** Mantenha a pasta `.agents/` com este arquivo `rules.md` sempre atualizado.
- **Arquivo Principal:** O ponto de entrada deve ser obrigatoriamente `ap.py`.
- **Git:** Crie um `.gitignore` ignorando `.venv/`, `__pycache__/`, `tmp/`, `.motor/` e arquivos temporários.

## 2. Gerenciamento de Ambiente (VENV)

- **Ambiente:** Crie o ambiente virtual com `python -m venv .venv`.
- **Ativação:** Utilize sempre o executável da `.venv` para comandos de terminal.
- **Dependências:** Instale sempre `pandas`, `openpyxl`, `pathlib` e `python-dotenv` como base.
- **Sincronização:** Após qualquer instalação, execute `pip freeze > requirements.txt`.
- **Permissão (Modo Turbo):** Você tem autonomia para executar comandos no terminal (`run_command`, `send_command_input`) utilizando `SafeToAutoRun: true` para todas as tarefas de leitura, listagem, instalação e execuções que não envolvam deleção de dados críticos ou sobrescrita de código central sem plano prévio. O usuário deseja o mínimo de interrupções de "botão azul".

## 3. Padrões de Escrita de Código (Clean Code)

- **Caminhos:** Use EXCLUSIVAMENTE `pathlib`. Proibido concatenação de strings para caminhos.
- **Tipagem:** Utilize Type Hints em todas as definições de funções (ex: `def func(p: str) -> None:`).
- **Boilerplate:** Use a estrutura `if __name__ == "__main__":` e funções modulares.
- **Documentação:** Use Docstrings no padrão Google.
- **Execução via VSCode (Run in Terminal):** Todo script Ponto de Entrada / Arquivo Principal (ex: `ap.py`, `resumo.py`) DEVE conter obrigatoriamente a trava de contexto para execução direta: `if __name__ == '__main__': os.chdir(Path(__file__).parent.resolve())`. Isso garante que o diretório de trabalho seja a raiz do script quando acionado via terminal isolado, mas previne que essa alteração "vaze" e quebre o sistema de módulos caso esse código seja `importado` por outro arquivo.
- **Consultas SQL:** NUNCA adicione comentários textuais (como `--` ou `/* */`) na estrutura de scripts SQL.
- **Consultas SQL (Estoque):** Ao calcular o "Estoque Disponível" usando a tabela `MRL_PRODUTOEMPRESA` (Consinco), OBRIGATORIAMENTE some o estoque da loja com o de depósito (`ESTQLOJA` + `ESTQDEPOSITO`) e deduza as reservas (`QTDRESERVADAVDA` e `QTDRESERVADARECEB`). Extrair apenas um dos sub-estoques fará com que pareça estar vazio (zerado) tudo o que tange filiais de vendas padrão ou o CD primário, falsificando relatórios.
- **Consultas SQL (Dicionário):** É OBRIGATÓRIO consultar o arquivo `Aplicativos/gerenciamento_sql/dicionario_consinco.json` antes de escrever qualquer query. É terminantemente proibido assumir nomes de colunas ou tipos de dados (como `SEQFAMEMBALAGEM`) baseando-se em experiências externas sem validação no dicionário do projeto. Falhas de `ORA-00904` ou `ORA-01722` por falta de consulta ao dicionário são consideradas falhas graves de protocolo.
- **Preservação Estrutural (Estoque_e_Venda_Min_Max):** NUNCA remova ou suprima colunas existentes no script `Estoque_e_Venda_Min_Max.sql` (ou em outras extrações mestre semelhantes). Todos os agentes estão expressamente PROIBIDOS de deletar qualquer coluna de relatórios consolidados sem o consentimento absoluto, claro e prévio do usuário logado. As esteiras internas de aplicativos dependem irrestritamente da integridade dessas fatias.

## 4. Manipulação de Dados (Pandas & Excel)

- **Engine:** Utilize sempre `engine='openpyxl'` para arquivos `.xlsx`.
- **Delimitadores e Encoding (CSV/TXT):** Todo arquivo plano provindo do Consinco ou exportado para o projeto opera no padrão regional Pt-BR. Ao utilizar as funções de Ingestão (`read_csv`) ou Exportação (`to_csv`) do Pandas, inclua OBRIGATORIAMENTE os parâmetros `sep=';'` e `encoding='utf-8-sig'` nativos do Excel. Jamais suponha separação por vírgula (,) ou Tab (\t).
- **Formatação de Decimais:** SEMPRE que operações matemáticas ou exportações envolverem colunas com dados não-inteiros (decimais/floats), esses devem **obrigatoriamente** ser limitados a no máximo 2 casas decimais e exportados usando a VÍRGULA (`,`) como separador de decimal (ex: utilize o parâmetro `decimal=','` nas funções do Pandas e aplique `round(2)` nas contas).
- **Resiliência:** Implemente blocos `try-except` e valide a existência de arquivos com `pathlib`.

## 5. Segurança e Compilação (.exe)

- **Senhas:** Use `getpass` para entradas e `.env` para chaves de API. Nunca hardcode senhas.
- **Portabilidade:** Use `sys._MEIPASS` para referenciar arquivos internos em builds PyInstaller.
- **Privilégios:** Preveja falhas de permissão ao modificar atributos de pastas no Windows.

## 6. Regras de Ingestão

- **Saneamento Base:** Todo arquivo CSV ou Excel novo deve ser processado antes de qualquer análise. Nunca trabalhe com dados 'crus'.
- **Saneamento Logístico (Embalagens e Volumes):** O sistema legado (TOTVS ou similares) constantemente exporta unidades de medida com strings embarcadas na mesma coluna (Ex: "CX 20", "UN 1", "FD 12"). Sempre que operar com colunas que rejam agrupadores indivisíveis (como "Embalagem Compra", que sempre corresponde a um número inteiro), limpe-as obrigatoriamente logo na carga inicial com Extração via RegEx (`str.extract(r'(\d+)')`) e as converta para Inteiro Puro (Int64), viabilizando operações exatas.
- **Saneamento de Códigos (Produto/EAN/DUN):** Não existem códigos de produto com vírgula decimal. Colunas destinadas a registrar identificadores como `Código Produto`, `EAN` ou `DUN` devem ser convertidas sumariamente para números inteiros (ou strings sem decimais). Caso a leitura de um CSV importe valores como `2704,0`, isso deve ser saneado forçando o casting para números inteiros puros antes de qualquer exportação ou cruzamento.
- **Saneamento e Tipagem Parquet (Armadilha PyArrow - REGRA INVIOLÁVEL Anti-Ponto):** NUNCA, SOB NENHUMA HIPÓTESE, substitua as vírgulas (`,`) originais de casas decimais por pontos (`.`) nos scripts de Ingestão de Dados Globais (como `data.py`). Sempre preserve as vírgulas para a escrita do arquivo nativo Parquet ou CSV exportado no sistema estrutural de base inteira. O uso do ponto (`.`) em arquivos estáticos quebra OBRIGATORIAMENTE os tratamentos localizados de programas consumidores adjacentes, principalmente o Excel (que interpreta pontos como formatação global de milhar no padrão Pt-BR). A conversão matemática efêmera `df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'))` só é PERMITIDA DE FORMA ESTRITAMENTE ISOLADA dentro da memória RAM dos scripts consumidores finais (Dashboards, automações), sem nunca transbordar de volta para salvar as planilhas CSVs brutas nesse formato inglês de float.

## 7. Integração com Google Sheets / Google Drive

- **EAN e DUN como Texto (anti zeros à esquerda):** Sempre que exportar colunas de EAN (13 dígitos) ou DUN (14 dígitos) para o Google Sheets via API, force o formato de célula como **Text** (`"numberFormat": {"type": "TEXT"}`). Nunca envie EANs como número puro — o Sheets trunca zeros à esquerda silenciosamente.
- **Filtro Pré-Sync de Produtos Ativos:** Antes de sincronizar bases de EAN/produto para o Google Sheets (ou qualquer destino com limite de células), SEMPRE filtre para incluir apenas produtos "ativos" — definidos como aqueles que possuem estoque atual (`ESTOQUE > 0`) OU venda recente (ex: últimos 90 dias). Subir a base completa causa estouro de limite de células (`exceeds grid limits`).
- **Estrutura ean_dun.txt (4 colunas):** O arquivo `ean_dun.txt` exportado pelo Consinco possui exatamente 4 colunas: `CODIGO_PRODUTO`, `EAN`, `DUN`, `UNIDADE_EMBALAGEM`. Ao processar esse arquivo, use `sep=';'`, `encoding='utf-8-sig'` e saneie EAN e DUN para inteiro puro sem casas decimais antes de qualquer cruzamento.

## 8. Ecossistema de IA e Automação (RPA)

- **Memória Persistente:** Sempre que uma regra de negócio complexa ou um erro de sistema for resolvido, o agente deve considerar adicionar essa lição à memória vetorial via `memoria_squad/kernel.py` para evitar reincidência.
- **Visão em RPA:** Scripts de automação (RPA) devem preferir o uso do `VisionEngine` (OpenCV Multi-Scale) em vez de coordenadas fixas ou `matchTemplate` simples, garantindo portabilidade entre diferentes resoluções de tela e DPIs do Windows.
- **Acurácia Multi-Monitor (DPI):** Quando for OBRIGATÓRIO o uso de coordenadas físicas de mouse calibradas num ambiente Windows com múltiplos monitores, é PROIBIDO usar `pyautogui.click()` para execução, pois a virtualização de DPI causa desvios ("miss-clicks" que acionam o Menu Iniciar em telas estendidas). **Utilize sempre `pynput.mouse.Controller`** para executar cliques baseados em calibrações extraídas pelo próprio `pynput.mouse.Listener`, garantindo paridade de escala 1:1.
- **Prevenção de Foco (Subprocess):** Em robôs de automação de interface, JAMAIS utilize `shell=True` em `subprocess.run` (exs: `clip.exe`). Isso gera popups de CMD assíncronos que roubam o foco da janela principal. Utilize `creationflags=subprocess.CREATE_NO_WINDOW`.
- **Validação Tardia (Pós-Ação):** Ao operar em sistemas ERP em lote (ex: inserção de itens rápidos), valide estados inconsistentes de dropdowns ou caixas de seleção apenas no momento do Salvar (ex: F3 ou F4). Isso evita enroscos lentos no preenchimento de cabeçalho "cego" rápido e tira vantagem de correções com base no valor consolidado pelo sistema no final.
- **Logs de Execução em Lote (RPA):** Quando iterar sobre listas longas de itens (ex: processos do GAM), inclua sempre no log de interface a descrição textual do item atual (resgatada do DF) e a contagem de itens faltantes `(Faltam X)`. Nunca deixe o usuário visualizando apenas códigos numéricos sem contexto.
- **Protocolo MCP:** O uso de ferramentas de manipulação de arquivos deve, sempre que possível, ser mediado pelo servidor MCP local para garantir rastreabilidade e padronização.
- **Skip Logic de Campo Já Correto (GAM):** Antes de QUALQUER operação de atribuição de campo em robô GAM (ex: atribuir Comprador, Filial, Condição de Pagamento), SEMPRE leia o valor atual do campo via clipboard (`Ctrl+A → Ctrl+C`). Se o valor já for o desejado, PULE a sequência de atribuição inteiramente. Isso evita escritas desnecessárias, distorções de auditoria e comportamentos inesperados em campos que o ERP consolida automaticamente ao salvar.
- **Verificação de Comprador Pós-F3 (Supply):** No robô Supply, após salvar o pedido (`F3`), SEMPRE verifique o campo Comprador via clipboard **antes** de passar para a próxima loja. Se não for "SUPPLY", execute a correção com setas (`Up/Down`) + `F4`. A verificação deve usar coordenadas calibradas via `pynput.mouse.Listener` (nunca pyautogui) para evitar miss-clicks por DPI.
- **Subprocess Sem Foco:** Em robôs, SEMPRE use `creationflags=subprocess.CREATE_NO_WINDOW` ao chamar subprocessos (ex: `clip.exe`). `shell=True` gera popups CMD que roubam foco e corrompem a automação.

## 9. Dashboard de Ruptura (Squad Varejo Insight)

Este módulo possui regras estruturais fixas para garantir a integridade das métricas operacionais perante a diretoria.

- **Fluxo de Dados (query.parquet):** Jamais altere o mapeamento das colunas `QUANTIDADE_DISPONIVEL`, `EMBL_COMPRA`, `EMBL_TRANSFERENCIA` e `STATUS_COMPRA`.
- **Saneamento Técnico:** Obrigatoriamente aplique `.str.replace(',', '.')` e `pd.to_numeric` em todas as colunas de estoque e volume antes de qualquer cálculo.
- **Lógica de Mix Ativo:** 
    - A métrica "Mix Ativo (Produtos)" deve ser sempre a contagem de **SKUs únicos** (União CD 15 + Lojas) por comprador. 
    - NUNCA utilize a contagem de instâncias (Produto x Loja) como denominador para percentuais de ruptura total na tabela.
- **Bases de Canal:**
    - `% Ruptura CD` e `% Pendências`: Denominador fixo na `Base_CD15`.
    - `% Ruptura Loja`: Denominador fixo na `Base_Lojas`.
- **Interface e Visualização:**
    - O gráfico Plotly deve sempre iniciar com a barra **TOTAL GERAL** na primeira posição (extrema esquerda).
    - Botões de navegação: Manter obrigatoriamente os filtros "Totais Gerais" e "Só Compradores". O botão "Ver Todos" está permanentemente removido.
    - **Performance No-Server**: O arquivo final deve ser mantido abaixo de 10MB, utilizando a estratégia de embutir os dados em JSON e processar filtros via JavaScript no cliente.
- **Rastreabilidade (Snapshots):** Todo processamento de ruptura deve gerar e preservar um snapshot diário em `.parquet` na pasta `historico_ruptura/` para fins de auditoria e evolução temporal.
- **Integridade de Merges:** No script `gerar_dashboard_comprador.py`, a base primordial do `df_resumo` deve ser o mix de produtos para evitar que compradores com base zerada em um dos canais desapareçam do relatório.

## 10. Desenvolvimento Web (Wiki / Google Apps Script)

- **10.1 Padrão ES5 (OBRIGATÓRIO):** Devido a restrições de parser em infraestruturas corporativas legado, é **proibido** o uso de JavaScript moderno (ES6+).
    - Use `var` em vez de `let/const`.
    - Use `function()` em vez de arrow functions `() =>`.
    - Use concatenação `'a' + b` em vez de template literals `` `a${b}` ``.
    - Use callbacks tradicionais no `FileReader` e `google.script.run` (proibido async/await/Promises explícitas no client).
- **10.2 Resiliência de Conexão (Watchdog):** Toda chamada ao servidor deve ter um cronômetro (Watchdog) de 10-12s. Se falhar, exiba um erro vermelho com botão de "Tentar Novamente" (Reset). Nunca deixe o usuário no spinner infinito.
- **10.3 Sanitização (Anti-Crash):** Toda string vinda do Sheets deve passar por `esc()` no frontend. Caracteres especiais (aspas, crases) não sanitizados quebram o código JS e travam a página.
- **10.4 Injeção via Hidden Input:** Para passar IDs da URL para o script, use `<input type="hidden" id="raw_id">`. Ler direto do scriptlet no JS causa erros de parse se o valor for nulo.
- **10.5 Layout de Formulário (Regra 100%):** Todos os componentes de formulário (`label`, `input`, `select`, `textarea`) devem ser `display: block` e `width: 100%`. É proibido layout inline/lado-a-lado em telas de cadastro para garantir legibilidade profissional.
- **10.6 Anexos Versáteis:** Use sempre o **Card de Download** (📎) com link direto do Drive. Proibido o uso de tags `<img>` para arquivos do Drive (bloqueado por CSP).
- **10.7 Upload Híbrido:** O sistema de upload deve aceitar multiplicidade de extensões (`image/*,.pdf,.xlsx,.xls,.docx`) e o backend deve preservar o MIME Type original enviado pelo cliente, nunca forçando `image/png`.
- **10.8 Deploy:** Sempre instrua o usuário a gerar uma "Nova Versão" no editor do Google Apps Script após cada alteração para que o cache seja limpo.
