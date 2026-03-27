# Aprendizado: Curva ABC de Distribuição e Lucratividade (TOTVS Consinco)

A partir da análise dos scripts nativos do sistema (`selecaoconuslta.txt` e `gridconsulta.txt`), extraímos os seguintes padrões consolidados de arquitetura e lógica de negócios do ERP TOTVS Consinco para elaboração de visões de lucratividade complexas:

## 1. Views e Tabelas Centrais
A geração de Curva ABC e lucratividade não é vista apenas baseada na `MRL_PRODUTOEMPRESA`. O sistema recorre a um cruzamento diário entre o Faturamento/Devolução x Custo do Dia:
- **`MAXV_ABCDISTRIBBASE` (Alias V)**: View principal que traz item a item as notas fiscais de venda, devolução e movimento em geral. Nela constam as colunas cruas como `QTDITEM`, `QTDDEVOLITEM`, `VLRITEM`, impostos retidos na fonte, ST e CGO do movimento.
- **`MRL_CUSTODIA` (Alias Y)**: Tabela contendo uma "fotografia" do custo do produto pro dia em que ocorreu a operação. As colunas cruciais sempre começam com `CMDIA...` (Custo Médio do Dia), como `CMDIAVLRNF`, `CMDIACREDICMS`, `CMDIACREDPIS`, `CMDIADESPNF`. O JOIN mais importante é `Y.NROEMPRESA = V.NROEMPRESA` (ou Emp Custo) e `Y.DTAENTRADASAIDA = V.DTAVDA`.
- **`MBI_TABCDISTRIB`** / **`MBIX_TABCDISTRIB`**: O Motor Consinco primeiro RODA a query super-pesada e faz um `INSERT INTO MBI_TABCDISTRIB` amarrada a uma `SEQCONSULTA`. Só depois, a tela de Aplicação / Grid faz um simples `SELECT` na View Base (`MBIX_TABCDISTRIB`) filtrando essa `SEQCONSULTA`. 

## 2. Abordagem de Conversão Logística e Frações
- **QTDITEM vs QTDEMBALAGEM**: O ERP lida com quantidades nominais no pedido. Para chegar à quantidade master coerente, o cálculo padrão usa a `(V.QTDITEM - V.QTDDEVOLITEM) / K.QTDEMBALAGEM`. Muitas vezes é aplicado um `ROUND(..., 6)` para evitar dízimas anômalas.
- **Peso e Volume**: Baseado na tabela `MAP_FAMEMBALAGEM` (Alias K), encontra-se o peso multiplicando a caixa/pacote pelas dimensões: `(K.ALTURA * K.LARGURA * K.PROFUNDIDADE) / 1000000`.

## 3. Lógica Financeira de Vendas vs Devoluções
Praticamente todo campo totalizador gerencial opera numa subtrativa de DEVOLUÇÕES:
- **Tributos base**: `V.ICMSITEM - V.ICMSDEVOLITEM` (o mesmo para PIS e Cofins).
- Sempre lidando com as strings limpas usando os campos `.VLRITEM - .VLRDEVOLITEM`.

## 4. O Coração da Lucratividade (Functions Oracles Específicas)
A "Verdadeira" margem de lucro e lucro bruto/contribuição não é calculada apenas subtraindo o VLRVENDA do CUSTO. O ERP tem dezenas de impostos cruzados e usa Functions gigantes (que recebem entre 30 a 50 parâmetros) para gerar o `VLRLUCRO` ou `VLRCONTRIB` ou `CTOBRUTOVDA`:
- `fC5_AbcDistribLucratividade( ... )`
- `FC5_ABCDISTRIBCUSTOBRUTO( ... )`
- `FC5_ABCDISTRIBCONTRIB( ... )`
- `FC5_AbcDistribCustoMarkUPDown( ... )`

**Aviso aos Programadores de Relatórios Customizados:** Sempre que o negócio solicitar *“Me de a Margem igual a Curva ABC”*, será impossível tentar fazer cálculos matemáticos diretos sem usar a function nativa ou tentar copiar a query inteira. O recomendado é acionar a `MBIX_TABCDISTRIB` se o relatório rodar em background, ou entender que qualquer matemática manual pode dar divergência de centavos contra a function nativa por causa de rateios de Frete (`V.VLRFRETEITEMRATEIO`), ST e Verbas de Acordo PDV.

## 5. Tratamento de Divisão (fC5_Divide)
O ERP traz nativamente uma function chamada `fC5_Divide(Numerador, Denominador)` que previne o erro `ORA-01476: divisor is equal to zero`, tratando a divisão limpa e retornando zero/null quando pertinente. Sempre utilize ela quando calcular `Quantidade Média`, `Variância` ou afins.
