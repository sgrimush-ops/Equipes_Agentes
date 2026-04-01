# Resumo dos Projetos - Pasta Aplicativos

Este documento serve como referência rápida para o sistema de agentes sobre os projetos que o usuário executa localmente. Ele mapeia os subdiretórios encontrados em `C:\Users\Alessandro.soares.BAKLIZI\Downloads\Todos_Projetos\Equipes_Agentes\Aplicativos\`.

## 1. BancoDadosSW
* **Propósito:** Conversão e extração de dados brutos provenientes de sistemas baseados em banco de dados/Totvs.
* **Principais Arquivos:** `convert_txt_to_excel.py`, arquivos de texto de origem (ex: `banco_de_dados_*.txt`).
* **Funcionamento:** Converte bases em `.txt` para arquivos Excel tabulados.

## 2. GAM (Gerenciador de Automações e Macros)
* **Propósito:** Aplicação de automação de interface com o usuário (RPA) com alta performance.
* **Principais Arquivos:** `main.py` (Interface Tkinter baseada em sequências JSON), e diversos scripts orientados à ação em `actions/*.py` e `core/*.py`.
* **Funcionalidades:** Possui dezenas de automações otimizadas (ex: Supply e Mix) com:
  - Baixa latência de execução e detecção robusta de colunas em inputs.
  - Logs de interface enriquecidos com descrições das planilhas e tracking visual em tempo real de itens faltantes.
  - `acao_digitar_pedido_CD_016.py`, `acao_digitar_pedido_supply.py`
  - Módulos de calibração de clique e integração com Visão OpenCV.
  - **Skip Logic (Buyer):** Antes de atribuir comprador, lê o campo atual via clipboard. Se já for "SUPPLY", pula a atribuição.
  - **Verificação Pós-F3:** Após salvar, verifica comprador via clipboard e corrige se necessário antes de avançar lojas.
  - **pynput obrigatório:** Todos os cliques calibrados usam `pynput.mouse.Controller` (nunca pyautogui) para evitar miss-clicks em ambientes multi-monitor.

## 3. Pendencias
* **Propósito:** Consolidação de relatórios fragmentados gerados por loja.
* **Principais Arquivos:** `consolidado.py`, `converter_pdfs.py`, `resumo.py`.
* **Funcionamento:** Pega múltiplos relatórios `.xlsx` (ex: `Loja *.xlsx`), concatena-os através do Pandas e gera um `consolidado.csv` final ordenado.

## 4. consumo
* **Propósito:** Conversão para formato estruturado columnar (Parquet).
* **Principais Arquivos:** `ap.py`, `check_parquet.py`.
* **Funcionamento:** Lê bases de consumo Excel e converte para `consumo.parquet` visando desempenho de dados massivos.

## 5. cruzamento
* **Propósito:** Núcleo de cruzamento inteligente baseando-se em bases Parquet.
* **Principais Arquivos:** `ap.py`, `processamento.py`, `consulta_codigo.py`, `update_gerencial_v2.py`.
* **Funcionamento:** Lê `.parquet` do diretório `bd` e efetua conciliações gerenciais organizadas.

## 6. mix
* **Propósito:** Trabalha estritamente com dados do Mix de produtos/lojas de forma integrada.
* **Principais Arquivos:** `convert_to_parquet.py`, `inspect_parquet.py`.
* **Funcionamento:** Transformação dos dados do Mix de produtos em `.parquet`.

## 7. ruptura
* **Propósito:** Análise de rupturas e geração inteligente de Dashboards Dinâmicos baseados no Mix ativo das filiais.
* **Principais Arquivos:** `rp.py` (Execução Principal), `gerar_dashboard_comprador.py`.
* **Funcionamento:** Lê a tabela `query.parquet`. Classifica a "Culpa" da ruptura entre [CD] vs [Loja]. Consolida métricas em um painel HTML **No-Server (<10MB)**, interativo e autossuficiente (JSON embutido), com filtros dinâmicos via JavaScript (Loja e Comprador) e geração automática de **snapshots históricos** diários para rastreabilidade de performance.

## 8. import_querys (Pipeline de Dados e Sincronização)
* **Propósito:** Núcleo de ingestão e sincronização de dados mestres (EAN, DUN, Estoque, Venda) com Google Sheets e AppSheet.
* **Principais Arquivos:** `barras.py`, `sync_google_sheet.py`, `sync_appsheet.py`, `sync_projetobak.py`.
* **Funcionamento:** 
  - **barras.py:** Lê `ean_dun.txt` (4 colunas), saneia EAN/DUN para inteiro puro, filtra produtos ativos e salva em `ean_dun.parquet`.
  - **sync_google_sheet.py:** Envia dados filtrados para Google Sheets, forçando EAN/DUN como **Texto** (preserva zeros à esquerda).
  - **sync_projetobak.py:** Automatiza o push de `query.parquet` para o repositório remoto ProjetoBak.
* **Regra Crítica:** Dataset deve ser filtrado para produtos ativos (Estoque > 0 ou Venda Recente) antes do upload para evitar erro `exceeds grid limits`.

## 9. integracao_google
* **Propósito:** Orquestração de autenticação OAuth2 para serviços Google.
* **Principais Arquivos:** `autenticacao_google.py`, `modulo_drive.py`, `modulo_gmail.py`.
* **Funcionamento:** Mantém a autenticação persistente via `token.json` e fornece wrappers para manipulação de arquivos e e-mails.

## 10. export / temporario / trabalho
* **Propósito:** Diretórios auxiliares para exportação final ou arquivos `tmp`.

## 11. gerenciamento_sql
* **Propósito:** Ambiente assistido para estruturação e geração de queries (Oracle SQL) para o ERP TOTVS Consinco.
* **Principais Arquivos:** `ap.py`, `dicionario_consinco.json` e a hierarquia da pasta `querys/`.
* **Funcionamento:** O usuário aciona o agente neste diretório fornecendo filtros e tabelas. O agente utiliza a skill `gerar_consultas_consinco` e o dicionário de dados local para formatar queries de acordo com o padrão TOTVS SGI (Client) salvando-as de imediato prontas para uso.

## 12. memoria_squad
* **Propósito:** Camada de inteligência persistente da Squad usando Banco de Dados Vetorial.
* **Principais Arquivos:** `kernel.py`, `seed_memory.py`.
* **Funcionamento:** Armazena e recupera conhecimentos, regras e lições aprendidas via busca semântica (ChromaDB), garantindo que a Squad "aprenda" com o tempo.

## 13. mcp_squad
* **Propósito:** Conectividade oficial via Model Context Protocol (MCP).
* **Principais Arquivos:** `office_server.py`.
* **Funcionamento:** Provê interface padronizada para que agentes externos e scripts locais manipulem arquivos Excel e CSV de forma segura e estruturada.

## 14. min_e_max
* **Propósito:** Cálculo e parametrização de estoques mínimos e máximos da rede.
* **Principais Arquivos:** `acao_ajustar_estoque.py`, `acao_preparar_manual_supply.py`.
* **Funcionamento:** Lógica para garantir a fluidez do abastecimento baseando-se em vendas e coberturas.
* **Regra Crítica (Min/Max):** As colunas de Min/Max no Consinco são **baseadas em CAIXAS** (unidade de embalagem), não em unidades avulsas. Ao comparar estoque disponível (em unidades) com Min/Max, SEMPRE converta para a mesma unidade multiplicando Min/Max pelo fator da embalagem (`EMBL_COMPRA`). Nunca compare unidades vs caixas diretamente.

---
> **Nota de Contexto:** Estes projetos seguem `rules.md` deste ecossistema (usam Pandas, pathlib, openpyxl, com try-excepts e isolamentos em Parquet e automação via GAM).
