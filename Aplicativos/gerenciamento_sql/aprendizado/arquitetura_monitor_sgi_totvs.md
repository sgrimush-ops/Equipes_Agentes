# Arquitetura de Geração de Relatórios MBI (Análise ABC de Estoque e Vendas) no Totvs Consinco
**Origens:** Logs do Monitor SQL capturados pelo usuário em tela (`frmAnlABCEstq` e `frmAnlABCVda`).

Descobrimos como o Totvs SGI compila os famosos grids dinâmicos (como as Análises ABC de Estoque e de Vendas PDV) por debaixo dos panos. É um padrão baseado em Tabelas de Trabalho (Temporárias/Sessão) e Procedures Dinâmicas.

## O Passo a Passo Dinâmico:

### 1. Inicializa uma Sessão de Consulta
Ele captura um novo número único de consulta via sequence (`S_MBIX_TABCCONSULTA.nextval`), ex: `48160`.
Grava o registro mestre na `MBIX_TABCCONSULTA` (Usuário, DataHora, Tipo).

### 2. Parametrização Flexível (EAV - Entity Attribute Value)
Ao invés de processar o filtro de tela direto no "WHERE", o sistema grava cada filtro numa tabela mestre/detalhe de Atributos chamada `MBIX_TABCATRIBCONSULTA`.
Isso prova que as sub-consultas funcionam puxando parâmetros daqui em vez de variáveis na Query.
* Exemplos capturados:
  - `NRODIVISAO = 1`
  - `EMPRESAS = 15`
  - `CATEGORIAS = 2119`
  - `FILTROSTATUSCOMPRA = 'A'`
  - `DESCONSIDERANAOAVALIADOS = 0,000000`

### 3. Vínculo de Configuração Custo/Impostos
Ele grava os parâmetros macro do relatório na tabela genérica temporária do Consinco: `GEX_DADOSTEMPORARIOS` (STRING1, STRING2).
Ex: `:frmAnlABCEstq.vsMetodoPrecificacao = 'L'`, `:vsUtilICMSTare = 'N'`.

### 4. Execução do Cérebro (Stored Procedures)
Uma vez parametrizada a MBI, ele dispara dezenas de iterações chamando Views ou Procs encadeadas. A que comanda o grid gerencial capturado é a procedure plástica:
```sql
SP_MBI_COLDINAMICAABCESTQCUST( frmAnlABCEstq.dfnSeqConsultaTmp, pnProcesso, vsValorRetorno )
```

### 5. Customizações Client (Colunas Extras)
Para dar chance a campos client-side (ClnCustom1... ClsCustom12), ele tenta ler colunas customizadas configuradas via XML ou banco para as telas SGI (ex: `MAX0005` ou grid visual) usando a `MBI_TABCCUSTOM` ou `GE_COLUNASCUSTOMIZADAS`.

### 6. Popular o Grid Final e Renderizar
A base de colunas inteira da tela já povoada por um grande INSERT SELECT no background é gravada na tabela "mãe" dos resultados finais.
Para **Estoque** (frmAnlABCEstq), a tabela dimensional base é: `MBIX_TABCESTOQUE` e `MBI_TABCESTOQUE`.
Para **Vendas/Varejo** (frmAnlABCVda), a tabela dimensional base é: `MBIX_TABCVAREJO` e `MBI_TABCVAREJO`.
Para **Clientes/Distribuição** (frmAnlABCCliente), a tabela dimensional base é: `MBIX_TABCDISTRIB` e `MBI_TABCDISTRIB`.

Ambas amarradas a mesma `SEQCONSULTA`.
O aplicativo frontend do Totvs apenas lança um:
```sql
SELECT ... FROM MBIX_TABCVAREJO WHERE SEQCONSULTA = X ORDER BY ...
```
Para exibir na interface sem gargalos, depois executa um `DELETE` para limpar a tabela após exibição ao usuário!

## Importância para nós:
Sempre que o usuário informar um relatório complexo do BI SGI do Consinco Totvs pedindo para exportá-lo, sabemos que as tabelas de domínio direto se cruzam com o sufixo "TABC" (Ex: `MBI_TABCVAREJO` para relatórios de vendas, `MBI_TABCESTOQUE` para estoques, e `MBI_TABCDISTRIB` para performance de clientes). Se precisarmos recuperar as expressões brutas dos cálculos nativos, elas estão mascaradas nessas integrações dinâmicas de procedures como `SP_MBI_COLDINAMICAABCESTQCUST`.
