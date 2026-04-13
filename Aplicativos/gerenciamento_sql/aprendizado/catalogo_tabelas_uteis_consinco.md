# Catalogo de Tabelas Uteis do Consinco

## Objetivo
Este arquivo consolida o conhecimento util antes distribuido entre `dicionario_consinco.json`, `categorias.txt` e os inventarios `tabela_consico_1.txt` a `tabela_consico_5.txt`.

## Tabelas Nucleares Confirmadas no Projeto

### Cadastro e Hierarquia Comercial
- `MAP_PRODUTO`: cadastro principal do produto.
- `MAP_FAMILIA`: familia comercial e tributaria do produto.
- `MAP_CATEGORIA`: hierarquia de categorias e departamentos.
- `MAP_FAMDIVCATEG`: relacao familia x categoria por divisao.
- `MAP_FAMDIVISAO`: configuracoes comerciais da familia, embalagem e comprador.
- `MAP_FAMEMBALAGEM`: embalagens por familia; chave segura por `SEQFAMILIA` + `QTDEMBALAGEM`.
- `MAP_PRODCODIGO`: EAN, DUN e outros codigos do produto.

### Comprador, Fornecedor e Pessoa
- `MAX_COMPRADOR`: gestor/comprador.
- `GE_PESSOA`: cadastro de fornecedor e cliente.
- `MAP_FAMFORNEC`: fornecedor principal da familia.

### Estoque, Custo e Venda Operacional
- `MRL_PRODUTOEMPRESA`: estoque, custo, datas e status por empresa.
- `MRL_PRODEMPSEG`: preco por produto, empresa, segmento e embalagem.
- `MRL_PRODVENDADIA`: historico diario de venda por produto e empresa.
- `MRL_CUSTODIA`: custo diario por data para cenarios de lucratividade.
- `MRL_PRODEMPRESAWM`: metricas logisticas padrao por empresa.
- `MAD_PRODESPENDERECO`: metricas logisticas por especie de endereco.

### Tabelas BI / MBI Confirmadas
- `MBI_TABCESTOQUE` e `MBIX_TABCESTOQUE`: base de analises de estoque.
- `MBI_TABCVAREJO` e `MBIX_TABCVAREJO`: base de analises de vendas varejo.
- `MBI_TABCDISTRIB` e `MBIX_TABCDISTRIB`: base de distribuicao e curva ABC.
- `MBIX_TABCCONSULTA`: sessao de consulta das telas dinamicas.
- `MBIX_TABCATRIBCONSULTA`: atributos/filtros usados pelas telas Consinco.

## Regras Estruturais do Ambiente
- Banco local: Oracle no ecossistema Totvs Consinco.
- Cliente final: Consinco; evitar comentarios dentro do SQL.
- O dicionario local manda mais que conhecimento externo.
- Historico de venda deve ser agregado antes do join com estoque para nao multiplicar saldos.
- `MRL_PRODUTOEMPRESA` e a fonte principal de estoque operacional.
- `MRL_PRODVENDADIA` e a fonte principal de quantidade vendida por periodo.
- Em relatorios complexos, preferir `MBI_` / `MBIX_` quando o sistema ja tiver materializado os calculos.

## Colunas e Regras Criticas Ja Validadas
- `VLRVDA` nao existe em `MRL_PRODVENDADIA` neste ambiente.
- Custo confiavel para a ABC por subgrupo: `MRL_PRODUTOEMPRESA.CMULTCUSLIQUIDOEMP` na loja 3.
- Estoque disponivel correto: `ESTQLOJA + ESTQDEPOSITO - QTDRESERVADAVDA - QTDRESERVADARECEB - QTDRESERVADAFIXA`.
- `DTAHORAULTENTRADA` e a grafia correta da coluna de data/hora; `DTAHORAAULTENTRADA` e grafia incorreta.
- `QTDPENDPEDEXPED` foi identificado como campo util para pendente a expedir do CD.

## Familias de Tabelas Encontradas nos Inventarios do Schema

### Prefixo MAP
- Cadastro de produto, familia, categoria, embalagem e codigos.

### Prefixo MRL / MRLV / MRLX
- Operacao de loja, estoque, custodia, precos, armazenagem e views auxiliares.

### Prefixo MBI / MBIX
- Motor de BI e tabelas temporarias/materializadas para consultas Consinco.

### Prefixo MAD / MADV / MADX
- Pedido de venda, faturamento, roteirizacao, expedicao e integracoes de venda.

### Prefixo MAC / MACV / MACX
- Abastecimento, compra, transferencia, suprimento e itens a expedir/receber.

### Prefixo MLO / MLOV
- Logistica, expedicao, sorter e compra com foco operacional.

### Prefixo MSU / MSUV / MSUX
- Fluxos de expedicao, itens expedidos e itens a expedir.

### Prefixo WMSV
- Visoes de carga, expedicao, lotes, paletes e separacao no WMS.

### Prefixo FI / FIV / FLC / EDI
- Financeiro, titulos, comissao, integracoes e documentos eletronicos.

## Categorias Base Preservadas

### Nivel 1 relevantes na rede
- `BEBIDAS`
- `MERCEARIA`
- `NAO ALIMENTO`
- `PERECIVEIS`
- `PERFUMARIA E LIMPEZA`
- `PRODUTOS PET`
- `ALMOXARIFADO`
- `INATIVAR`
- `SERVICOS`

### Nivel 2 observados no inventario local
- `ACESSORIOS`
- `ACOUGUE`
- `AVES`
- `BAZAR`
- `BEBIDA`
- `CASA E JARDIM`
- `FIAMBRERIA`
- `FRUTAS E VERDURAS`
- `LIVRARIA`
- `MAT EXPEDIENTE`
- `MAT LIMPEZA`
- `MERCEARIA SECA`
- `PADARIA BAKLIZI`

## Como Usar Este Catalogo
- Para criar query: validar primeiro se a tabela ja esta descrita em `dicionario_consinco.json`.
- Para relatorio Consinco: verificar se ha equivalente pronto em `MBI_` / `MBIX_`.
- Para custo, margem e estoque: revisar tambem `regras_imutaveis_sql.md`, `arquitetura_monitor_consico_totvs.md` e `regras_consolidadas_abc_vendas_subgrupo.md`.

## Substituicao dos TXT
Os arquivos `categorias.txt` e `tabela_consico_1.txt` a `tabela_consico_5.txt` foram consolidados neste catalogo e podem ser removidos sem perda do conhecimento util do projeto.