-- =========================================================
-- Exemplo de Pipeline de Relatório Consinco - Análise ABC de Vendas (Varejo)
-- =========================================================
-- Arquivo gerado via engenharia reversa dos logs do Monitor SQL (Aplicação: frmAnlABCVda)
-- Tabela Destino Final: MBIX_TABCVAREJO e MBI_TABCVAREJO

-- 1. Inserção Dinâmica Padrão Consinco (EAV Params)
-- O sistema insere os parâmetros de filtros em MBIX_TABCATRIBCONSULTA para a SEQCONSULTA corrente.
-- Parâmetros como PERIODO (ex: 'Inicio do Mês até hoje'), DATAINICIAL, DATAFINAL, TIPCATEGORIA ('M') etc.

-- 2. Parametrização em Memória (GEX_DADOSTEMPORARIOS)
-- Define chaves de métodos de precificação e apuração para as Procedures Dinâmicas
-- Ex: ':frmAnlABCVda.vsMetodoPrecificacao' = 'L'
--     ':frmAnlABCVda.vsTipoApuracao' = 'B'
--     ':frmAnlABCVda.vsIndDescTransf' = 'S'

-- 3. A estrutura magna final (MBI_TABCVAREJO)
-- O sistema gera um grid completo de análise de Vendas Varejo/PDV. 
-- Estes são os campos exatos já calculados disponíveis no select final que a visualização consome:

SELECT
    SEQLINHA, 
    NIVELHIERARQUIA, ACTFAMILIA, SEQCATEGORIAPAI, 
    QTDEMBALAGEM, EMBALAGEM, 
    CODEAN,
    STATUSCOMPRA, STATUSVENDA, 
    NOMEDETALHE1, CODDETALHE1, SEQDETALHE1, 
    NOMEDETALHE2, CODDETALHE2, SEQDETALHE2, 
    NOMEDETALHE, 
    INDPOSICAOCATEG, 
    LITROS, LITRAGEM, VOLUMEM3, 
    
    -- Métricas de Quantidade e Documentos
    QUANTIDADE, 
    QUANTIDADEUNIT, 
    NROITENS, 
    NRODOCTOS, 
    fc5_Divide( VLRVENDA, NRODOCTOS ) AS TICKET_MEDIO, 
    fc5_Divide( QUANTIDADE, NRODOCTOS ) AS ITENS_POR_CUPOM, 
    
    -- Métricas de Receita e Custo
    VLRUNITARIO, 
    VLRVENDA, 
    VLRVENDANORMAL, 
    VLRVENDAPROMOC, 
    VLRVENDA - VLRVENDAPROMOC AS DESCONTO_PROMOCIONAL, 
    VLRCBRUTOUNIT, 
    VLRCLIQUNIT, 
    VLRCTOLIQVDA,
    CTOBRUTOVDA, 
    CTOBRUTOMARKUPDOWN, 
    
    -- Métricas de Lucro e Margem
    VLRLUCRO, 
    fc5_Divide( VLRLUCRO, QUANTIDADE ) AS LUCRO_UNITARIO, 
    MARGEMLUCRO, 
    MARGEMLUCROSVMI, 
    VLRLUCROVERBAPDV, 
    MARGEMLUCROVERBAPDV, 
    MARGEMLUCROVERBAPDVSVMI, 
    MARGEMCADASTRO, 
    VARMARGEM, 
    MARKUP, 
    MARKDOWN, 
    VLRGMROI, 
    
    -- Despesas e Impostos
    VLRDESPESAVDA, 
    VLRCOMPRORVDA, 
    VLRCOMISSAOVDA, 
    VLRIMPOSTOVDA, 
    VLRIMPOSTOIBSMUN, VLRIMPOSTOIBSUF, VLRIMPOSTOCBS, VLRIMPOSTOIS, 
    
    -- Margem de Contribuição e Pesos
    VLRCONTRIB, 
    MARGEMCONTRIB, 
    MARGEMCONTRIBSVMI, 
    PESOBRUTO, PESOLIQUIDO, 
    VLRVENDAPORM3, 
    
    -- Verbas e Descontos Extras
    VLRVERBAPDV, 
    CUSTOFISCALUNIT, CUSTOFISCALTOTAL, CUSTOFISCALTOTALVDA, 
    VLRDESPFIXA, VLRDESCFIXO, 
    VLRDESCFORANFVDA, 
    NVL(CMDIAVLRDESCVERBATRANSF,0), 
    NVL(CMDIAVLRDESCLUCROTRANSF,0)
FROM MBIX_TABCVAREJO 
WHERE SEQCONSULTA = :SuaSequenciaConsulta
ORDER BY NOMEDETALHE1 ASC, NOMEDETALHE2 ASC;
