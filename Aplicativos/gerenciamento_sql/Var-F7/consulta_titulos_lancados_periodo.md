# Var-F7 - Consulta de Títulos para Portal do Fornecedor (Foco em DEVREC e Acordos)

## Objetivo da Consulta
Fornecer os dados necessários para o **Portal do Fornecedor**, trazendo todos os títulos e créditos a receber de fornecedores decorrentes de **Devoluções (`DEVREC`)** e **Acordos Comerciais / Verbas (`ACRCIM`, `ACRCOM`, `ACRINT`, `ACRLOG`, `ACRMKT`, `ACRPRE`, `ACRTRO`, `ACORDO`, `VERBA`)**, com abrangência para **todas as empresas/lojas cadastradas com lançamentos**.

---

## Arquivo Oficial
- **Query Principal:** [`consulta_titulos_lancados_365d_venc_180d.sql`](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/gerenciamento_sql/querys/consulta_titulos_lancados_365d_venc_180d.sql)
- **Filtro de Período:** Lançados nos últimos 365 dias até vencimento em 180 dias à frente (`T.DTAINCLUSAO >= TRUNC(SYSDATE) - 365 AND T.DTAVENCIMENTO <= TRUNC(SYSDATE) + 180`).

---

## Diferença Conceitual: `DATA_LANCAMENTO` vs `DATA_EMISSAO`

| Campo | Nome no Banco | Significado | Exemplo Real |
|---|---|---|---|
| **`DATA_EMISSAO`** | `FI_TITULO.DTAEMISSAO` | **Data do Documento / Competência:** É a data impressa na Nota Fiscal de origem, a data base do contrato ou a competência da negociação comercial. | Parcelas de um acordo negociado com competência de abril têm emissão `01/04/2026`. |
| **`DATA_LANCAMENTO`** | `FI_TITULO.DTAINCLUSAO` | **Data de Entrada no Sistema:** É a data e hora exata em que o título foi gravado no banco de dados do Totvs Consinco pelo operador ou integração. | O acordo de abril só foi digitado/aprovado no ERP no dia `25/09/2026`. |

> [!IMPORTANT]
> **Por que filtramos por `DATA_LANCAMENTO` (`DTAINCLUSAO`)?**
> Porque garante capturar **tudo o que entrou recentemente no sistema**, inclusive acordos retroativos, notas de devolução emitidas no passado mas registradas agora e parcelas futuras geradas hoje.

---

## Como é resolvido o Comprador no ERP Consinco?
1. **No Título (`FI_TITCOMPRADOR`):** Títulos de compras normais possuem o comprador gravado.
2. **Em Devoluções (`DEVREC`) e Acordos Financeiros:** Por padrão no Consinco, o `FI_TITCOMPRADOR` fica vazio (`NULL`) ou como `1 - MODELO`, pois as devoluções nascem nas lojas/CDs e não pelo comprador.
3. **Resolução Inteligente (Fallback):** A query busca primeiro no título (`FI_TITCOMPRADOR`). Se estiver vazio ou for código `1`, busca automaticamente o **Comprador Principal Ativo do Fornecedor** (`MACV_PSITEMRECEBER`), garantindo que o portal exiba o comprador real daquela conta (ex: *WERTER*, *BATISTA*, *NICOLAS*) em vez de `'GERAL'`.

---

## Filtros de Período e Regras de Negócio

1. **Classificação Canônica de Direitos a Receber (`FI_TITULO`):**
   - `T.OBRIGDIREITO = 'D'` (Direito / Crédito a Receber contra o Fornecedor)
   - `T.CODESPECIE IN ('DEVREC', 'ACRCIM', 'ACRCOM', 'ACRINT', 'ACRLOG', 'ACRMKT', 'ACRPRE', 'ACRTRO', 'ACORDO', 'VERBA') OR T.CODESPECIE LIKE 'ACR%'`
   - `T.SITUACAO != 'C'` (Exclusão de cancelados)
   - `T.DTAINCLUSAO >= TRUNC(SYSDATE) - 365 AND T.DTAVENCIMENTO <= TRUNC(SYSDATE) + 180`

---

## Colunas Disponibilizadas para o Portal

| Coluna | Descrição | Fonte / Regra |
|---|---|---|
| `SEQ_TITULO` | Sequencial unívoco do título no Consinco | `FI_TITULO.SEQTITULO` |
| `EMPRESA` | Nome Reduzido da empresa | `MAX_EMPRESA.NOMEREDUZIDO` |
| `TITULO` | Número do Título / NF Devolução / Acordo | `FI_TITULO.NROTITULO` |
| `SERIE` | Série do documento | `FI_TITULO.SERIETITULO` |
| `PARCELA` | Parcela do título | `FI_TITULO.NROPARCELA` |
| `ESPECIE` | Sigla da Espécie | `FI_TITULO.CODESPECIE` |
| `TIPO_DOCUMENTO` | Classificação amigável | `DEVOLUCAO A RECEBER` / `ACORDO / VERBA` |
| `COD_FORNECEDOR` | Código da pessoa/fornecedor | `FI_TITULO.SEQPESSOA` |
| `FORNECEDOR` | Razão Social do fornecedor | `GE_PESSOA.NOMERAZAO` |
| `CNPJ_CPF` | CNPJ/CPF com formatação oficial | `FC5MASKCNPJCPF(...)` |
| `COMPRADOR` | Comprador responsável pela negociação | Resolução Inteligente (`Título -> Fornecedor Principal`) |
| `DATA_LANCAMENTO` | Data em que foi lançado no ERP | `TO_CHAR(FI_TITULO.DTAINCLUSAO, 'DD/MM/YYYY')` |
| `DATA_EMISSAO` | Data de emissão | `TO_CHAR(FI_TITULO.DTAEMISSAO, 'DD/MM/YYYY')` |
| `DATA_VENCIMENTO` | Data de vencimento/cobrança | `TO_CHAR(FI_TITULO.DTAVENCIMENTO, 'DD/MM/YYYY')` |
| `DATA_QUITACAO` | Data em que foi quitado/abatido | `TO_CHAR(FI_TITULO.DTAQUITACAO, 'DD/MM/YYYY')` |
| `VALOR_NOMINAL` | Valor original do crédito | `ROUND(FI_TITULO.VLRNOMINAL, 2)` |
| `VALOR_ABATIDO_PAGO`| Valor já quitado/abatido em duplicatas | `ROUND(FI_TITULO.VLRPAGO, 2)` |
| `SALDO_ABERTO` | Saldo pendente de abatimento | `ROUND(VLRNOMINAL - VLRPAGO, 2)` |
| `STATUS_PAGAMENTO` | Status do título no portal | `QUITADO / ABATIDO`, `ABATIDO PARCIAL`, `PENDENTE ABATIMENTO` |
| `SITUACAO_TITULO` | Situação no ERP | `FI_TITULO.SITUACAO` |
| `OBSERVACAO_TITULO`| Observação cadastrada | `FI_TITULO.OBSERVACAO` |

---

## Padrões de Performance
- **Materialização Prévia (`/*+ MATERIALIZE */`):** Isola e indexa em memória temporária do Oracle os títulos, compradores sugeridos e vínculos antes dos joins principais.
- **Zero Comentários no SQL:** Arquivos `.sql` sem linhas de comentário para compatibilidade estrita com o compilador Delphi do Consinco.
- **Envelopamento Obrigatório:** Compatibilidade com validador de telas do ERP.
