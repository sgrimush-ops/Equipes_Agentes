# Resumo dos Projetos - Pasta Aplicativos

Este documento serve como referência rápida para o sistema de agentes sobre os projetos que o usuário executa localmente. Ele mapeia os subdiretórios encontrados em `C:\Users\Alessandro.soares.BAKLIZI\Downloads\Todos_Projetos\Equipes_Agentes\Aplicativos\`.

## 1. BancoDadosSW
* **Propósito:** Conversão e extração de dados brutos provenientes de sistemas baseados em banco de dados/Totvs.
* **Principais Arquivos:** `convert_txt_to_excel.py`, arquivos de texto de origem (ex: `banco_de_dados_*.txt`).
* **Funcionamento:** Converte bases em `.txt` para arquivos Excel tabulados.

## 2. ExcluiColuna
* **Propósito:** Limpeza e remoção de colunas em excesso de bases de dados.
* **Principais Arquivos:** `ap.py`, `convert.py`, arquivos `abc.xlsx`.
* **Funcionamento:** Reduz o escopo de planilhas CSV/Excel retirando o desnecessário.

## 3. GAM (Gerenciador de Automações e Macros)
* **Propósito:** Aplicação de automação de interface com o usuário (RPA).
* **Principais Arquivos:** `main.py` (Interface Tkinter baseada em sequências JSON), e diversos scripts orientados à ação em `actions/*.py` e `core/*.py`.
* **Funcionalidades:** Possui dezenas de automações, como:
  - `acao_digitar_pedido_CD_016.py`
  - `acao_bloquear_tela.py`, `acao_suspender_pc.py`
  - Módulos de calibração de clique e ações no sistema Consinco.

## 4. Pendencias
* **Propósito:** Consolidação de relatórios fragmentados gerados por loja.
* **Principais Arquivos:** `consolidado.py`, `converter_pdfs.py`, `resumo.py`.
* **Funcionamento:** Pega múltiplos relatórios `.xlsx` (ex: `Loja *.xlsx`), concatena-os através do Pandas e gera um `consolidado.csv` final ordenado.

## 5. consumo
* **Propósito:** Conversão para formato estruturado columnar (Parquet).
* **Principais Arquivos:** `ap.py`, `check_parquet.py`.
* **Funcionamento:** Lê bases de consumo Excel e converte para `consumo.parquet` visando desempenho de dados massivos.

## 6. cruzamento
* **Propósito:** Núcleo de cruzamento inteligente baseando-se em bases Parquet.
* **Principais Arquivos:** `ap.py`, `processamento.py`, `consulta_codigo.py`, `update_gerencial_v2.py`.
* **Funcionamento:** Lê `.parquet` do diretório `bd` e efetua conciliações gerenciais organizadas.

## 7. mix
* **Propósito:** Trabalha estritamente com dados do Mix de produtos/lojas de forma integrada.
* **Principais Arquivos:** `convert_to_parquet.py`, `inspect_parquet.py`.
* **Funcionamento:** Transformação dos dados do Mix de produtos em `.parquet`.

## 8. ruptura
* **Propósito:** Análise de rupturas e geração inteligente de Dashboards Dinâmicos baseados no Mix ativo das filiais.
* **Principais Arquivos:** `rp.py` (Execução Principal), `gerar_dashboard_comprador.py`.
* **Funcionamento:** Lê diretamente a volumosa tabela `query.parquet`. Classifica a "Culpa" da ruptura entre [Ruptura originada no CD] vs [Ruptura Operacional/Logística da Loja] conferindo o mix e os saldos do CD. Consolida essas métricas em um painel HTML único, interativo e sem servidor, gerando dezenas de instâncias gráficas Plotly em formato de abas (visão de cada filial) gerenciadas por um Select Dropdown em JavaScript, e contendo matrizes numéricas com hiperlinks para exibir listas detalhadas customizadas por situação e por comprador.

## 9. export / temporario / trabalho
* **Propósito:** Diretórios auxiliares para exportação final ou arquivos `tmp` (temporários).

## 10. integracao_google
* **Propósito:** Orquestração de acessos à nuvem usando APIs oficiais REST.
* **Principais Arquivos:** `ap.py`, `autenticacao_google.py`, `modulo_drive.py`, `modulo_gmail.py`, `modulo_appsheet.py`.
* **Funcionamento:** Mantém a autenticação OAuth persistente de Google Drive e Gmail (via `token.json` e `credentials.json`) e executa endpoints do AppSheet (via App Id e Access Key em `.env`).

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

---
> **Nota de Contexto:** Estes projetos seguem `rules.md` deste ecossistema (usam Pandas, pathlib, openpyxl, com try-excepts e isolamentos em Parquet e automação via GAM).
