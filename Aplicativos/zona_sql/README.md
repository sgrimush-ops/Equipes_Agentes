# ⚡ ZONA SQL - Simulador & Mentor Consinco (Oracle ERP)

Um ambiente interativo e autônomo para **treinamento prático, desenvolvimento de consultas, aprendizado das regras do ERP Totvs Consinco / Oracle e carga/atualização de tabelas via planilha**.

---

## 🎯 Por que a Zona SQL foi criada?
Sites comuns de SQL (como W3Schools ou SQLiteOnline) utilizam esquemas genéricos (`Customers`, `Orders`, `Products`) que **não refletem o mundo real do ERP Consinco**, nem preparam você para os desafios críticos do dia a dia (como *hints* `/*+ MATERIALIZE */`, cálculo correto de estoque disponível sem duplicar saldos, bypass do validador *"Não é uma consulta"*, tratamento de embalagens com `QTDEMBALAGEM = 1`, parametrização com `Var - F7` e **atualização segura de tabelas como Pontas de Gôndola e Pontos Extras via planilhas com MERGE INTO**).

A **Zona SQL** reúne em uma interface visual completa:
1. **Banco de Dados Realista de Varejo:** Pré-carregado com as tabelas centrais do Consinco (`MAP_PRODUTO`, `MRL_PRODUTOEMPRESA`, `MRL_PONTOEXTRA`, `MRL_PONTOEXTRAPRODUTO`, `MRL_PONTOEXTRAPRODUTOEMPRESA`, `MAP_CATEGORIA`, `MRL_CUSTODIA`, `FI_TITULO`, `MSU_PEDIDOSUPRIM`, `MAX_EMPRESA`, `MAX_COMPRADOR`, etc.) e dados reais de lojas (1 a 18), compradores e estoques.
2. **📦 Laboratório de Carga & Atualização de Tabelas:** Módulo dedicado que ensina a atualizar tabelas do Consinco a partir de planilhas Excel/CSV usando `SEQPRODUTO` como chave primária mestra, gerando scripts `MERGE INTO`, blocos transacionais `UPDATE + INSERT` e executando no banco com auditoria visual antes vs depois (Diff).
3. **🕵️ Simulador do SQL Monitor Consinco:** Reproduz e decodifica exatamente o rastreamento de chamadas do Delphi/SGI (`<ID-00001> SELECT INTO...`), ensinando o ciclo de vida de leitura das pontas de gôndola no ERP.
4. **Catálogo Oficial de 50.417 Colunas (4.515 Tabelas):** Dicionário completo de tabelas e colunas integrado para busca instantânea.
5. **Motor com Emulação Oracle:** Suporta funções como `NVL()`, `TO_CHAR()`, `TO_DATE()`, `TO_NUMBER()`, `TRUNC()`, `SYSDATE()`, `INSTR()`, `SUBSTR()`, `DECODE()`, `LPAD()`, `RPAD()`, `REGEXP_LIKE()` e comandos DML (`UPDATE`, `INSERT`, `MERGE INTO`).
6. **Guardião de Regras Consinco (Linter em Tempo Real):** Alerta imediatamente se você digitar código com risco de erro fatal no Totvs SGI (como comentários `--`, `UPDATE` sem `WHERE`, alias com aspas duplas causando `ORA-00923`, coluna `STATUSVENDA` inexistente em `MRL_PRODUTOEMPRESA`, ou joins cartesianos).
7. **Mentor Didático de IA:** Decompõe a query em português claro, explicando o que cada tabela e join está fazendo.
8. **Trilha de Missões Práticas:** Desafios progressivos de consultas e atualizações de tabelas com verificação automática do resultado.
9. **Simulador de Variáveis de Tela (`Var - F7`):** Teste suas consultas dinâmicas com `:NROEMPRESA`, `:NR1`, `:LS1`, `:DT1` e `:LT1`.

---

## 🚀 Como Iniciar

### Opção 1: Pelo arquivo `.bat` (1 Clique no Windows)
Dê um duplo clique no arquivo:
```
c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\zona_sql\iniciar_zona_sql.bat
```
Ele abrirá seu navegador padrão automaticamente em `http://127.0.0.1:8550`.

### Opção 2: Pelo Terminal
```bash
cd c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\zona_sql
python server.py
```
Acesse: `http://127.0.0.1:8550`

---

## 🧩 Principais Recursos da Interface

| Recurso | Descrição |
| :--- | :--- |
| **📦 Carga & Atualização de Tabelas** | Cole dados do Excel com `SEQPRODUTO`, valide no cadastro do Consinco, gere scripts `MERGE INTO` ou `UPDATE+INSERT` e aplique no banco simulador com diff visual. |
| **🕵️ Simulador do SQL Monitor** | Visualize a sequência exata de queries que o ERP dispara (`MRL_PONTOEXTRA` ➔ `MRL_PONTOEXTRAPRODUTO` ➔ `MRL_PONTOEXTRAPRODUTOEMPRESA`). |
| **📁 Explorador de Tabelas** | Lista todas as tabelas ativas com contagem de registros. Clique em `👁️` para ver colunas e 20 linhas de amostra, ou `📝` para gerar um `SELECT *` no editor. |
| **📚 Busca no Dicionário** | Pesquise instantaneamente por qualquer uma das 4.515 tabelas ou 50.417 colunas do schema oficial Consinco. |
| **💡 Modelos / Snippets** | Modelos homologados prontos: *MERGE INTO Pontas*, *UPDATE Estoque Mín/Máx*, *Bypass Consinco*, *Preço Vigente com NVL*, *Vendas MRL_CUSTODIA*, etc. |
| **⚡ Gaveta Var - F7** | Alterne lojas (1 a 18), fornecedores (:NR1) e períodos (:DT1 / :DT2) para testar queries parametrizadas. |
| **🛡️ Guardião Consinco** | Validação sintática e de boas práticas enquanto você digita no editor (incluindo alertas contra `UPDATE` sem `WHERE`). |
| **🎓 Mentor Didático** | Clique em *"✨ Explicar Query"* para entender a modelagem, grão e cálculos da consulta. |
| **📊 Grade de Dados** | Visualização tabular dos dados retornados, ordenação, tempo de execução (ms) e exportação para CSV ou Excel. |
| **🧹 Limpar p/ Consinco** | Remove todos os comentários do código para colar diretamente no painel Consulta Criação do SGI sem erros de quebra de linha. |

---

## 🏆 Trilha de Aprendizado Inclusa

1. **Missão 1 (Básico):** Conhecendo os Produtos Ativos da Loja 1 (`MAP_PRODUTO` + `MRL_PRODUTOEMPRESA`).
2. **Missão 2 (Joins):** Hierarquia Comercial e Departamentos Nível 1 (`MAP_CATEGORIA`).
3. **Missão 3 (Cálculos):** Cálculo do Estoque Disponível Real abatendo reservas de venda e recebimento.
4. **Missão 4 (Oracle):** Preço Vigente Promocional vs Normal com `NVL` e `NULLIF`.
5. **Missão 5 (Performance):** CTE Materializada com Hint `/*+ MATERIALIZE */` e Bypass do validador (`SELECT * FROM (...)`).
6. **Missão 6 (Parametrização):** Parametrização dinâmica com variáveis bind `Var - F7` (`:NROEMPRESA`, `:NR1`).
7. **Missão 7 (Atualização de Tabela):** Atualizar Estoque Mínimo e Máximo de Ponta de Gôndola (`MRL_PONTOEXTRAPRODUTOEMPRESA`) usando `UPDATE`.
8. **Missão 8 (Consultas de Pontas):** Consulta de Auditoria de Pontas Extras vs Estoque Real da Loja.
9. **Missão 9 (Atualização em Lote):** Atualização de Vigência Promocional de Pontas de Gôndola com filtros de ponta.

---

## 🛠️ Como Recarregar ou Re-gerar o Banco de Dados

Para re-popular o banco do simulador com dados atualizados do workspace:
```bash
cd c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\zona_sql
python database\seed_data.py
```
