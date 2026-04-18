# Modelo Visual do QRP - Grid ABC Comprador

## Uso correto
- Este arquivo nao e um QRP binario.
- Ele e um modelo textual para voce copiar como referencia visual dentro do Gupta Report Builder.
- O conteudo do arquivo .QRP aberto no Notepad++ confirma que o layout e serializado/binario e nao deve ser editado manualmente ali.

## Objetivo
Montar a impressao com o mesmo formato da grid: uma linha de titulos e uma linha de detalhe por produto.

## Cabecalho sugerido

Titulo:
RELATORIO ABC VENDAS POR COMPRADOR

Linha 1:
Comprador: [vsComprador]

Linha 2:
Periodo de Vendas: [vddtainicialvda] a [vddtafinalvda]

Linha 3:
Loja(s): [vsEmpresas]

Linha 4:
Emissao: [CurrentDate()]

## Modelo da linha de titulos

```text
SUBGRUPO | COD_PROD | PRODUTO                    | EMB | QTD_VDA | PERC_ACM | PRC_CST | PRC_VDA | MARG_ATU | MARG_OBJ | EST_MIN | EST_MAX | EST_LOJA | EST_CD | PEND_CD | DT_ULT_COMP | QTD_ULT_COMP
```

## Modelo da linha de detalhe

```text
[SUBGRUPO] | [COD_PROD] | [PRODUTO] | [EMB] | [QTD_VDA] | [PERC_ACM] | [PRC_CST] | [PRC_VDA] | [MARG_ATU] | [MARG_OBJ] | [EST_MIN] | [EST_MAX] | [EST_LOJA] | [EST_CD] | [PEND_CD] | [DT_ULT_COMP] | [QTD_ULT_COMP]
```

## Vinculos exatos da query
Usar exatamente estes aliases da query final:

```text
SUBGRUPO
COD_PROD
PRODUTO
EMB
QTD_VDA
PERC_ACM
PRC_CST
PRC_VDA
MARG_ATU
MARG_OBJ
EST_MIN
EST_MAX
EST_LOJA
EST_CD
PEND_CD
DT_ULT_COMP
QTD_ULT_COMP
```

## Largura inicial sugerida por coluna
Estas larguras sao uma referencia visual inicial para montar a linha da esquerda para a direita.

```text
SUBGRUPO      14
COD_PROD       8
PRODUTO       34
EMB            6
QTD_VDA        9
PERC_ACM       9
PRC_CST        9
PRC_VDA        9
MARG_ATU       9
MARG_OBJ       9
EST_MIN        8
EST_MAX        8
EST_LOJA       9
EST_CD         8
PEND_CD        8
DT_ULT_COMP   10
QTD_ULT_COMP  10
```

## Ordem de montagem no builder
1. Manter apenas o cabecalho geral do relatorio.
2. Apagar os blocos antigos de fornecedor, categoria, EAN, EmbVda e EmbCompra.
3. Criar uma faixa unica de titulos.
4. Criar uma faixa unica de detalhe.
5. Inserir cada campo na mesma ordem da grid.
6. Garantir que cada produto ocupe apenas uma linha visual.

## Formatos sugeridos
```text
DT_ULT_COMP   dd/MM/yyyy
PERC_ACM      0.0
PRC_CST       0.00
PRC_VDA       0.00
MARG_ATU      0.00
MARG_OBJ      0.00
QTD_VDA       0
EST_MIN       0
EST_MAX       0
EST_LOJA      0
EST_CD        0
PEND_CD       0
QTD_ULT_COMP  0
```

## Versao compacta, se faltar largura
Se nao couber na primeira tentativa, monte primeiro assim:

```text
SUBGRUPO | COD_PROD | PRODUTO | EMB | QTD_VDA | PRC_VDA | MARG_ATU | EST_LOJA | EST_CD | DT_ULT_COMP | QTD_ULT_COMP
```

Depois reintroduza:

```text
PERC_ACM
PRC_CST
MARG_OBJ
EST_MIN
EST_MAX
PEND_CD
```

## Regra final
- O corpo da impressao deve espelhar a grid.
- Nao usar blocos por fornecedor.
- Nao usar blocos por categoria.
- Nao quebrar um produto em duas linhas.
- Nao editar o .QRP bruto no Notepad++.