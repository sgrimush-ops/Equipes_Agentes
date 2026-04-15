Consulta: consulta_NF_inceneracao.sql

Objetivo
- Listar itens de NF de incineracao emitidas com CGO 831.
- Retornar departamento, codigo do fornecedor, fornecedor principal, codigo do produto, descricao, quantidade da NF e valor do produto na NF.
- Permitir filtro antes do Run por codigo do fornecedor, departamento e periodo inicial/final.

SQL principal
```sql
SELECT
	N.NROEMPRESA AS CODIGO_EMPRESA,
	E.NOMEREDUZIDO AS EMPRESA,
	N.DTAEMISSAO AS DATA_EMISSAO,
	CASE
		WHEN N.APPORIGEM = 26 THEN N.NUMERONFSE
		ELSE N.NUMERONF
	END AS NUMERO_NF,
	NVL(DEP.DEPARTAMENTO, 'SEM DEPARTAMENTO') AS DEPARTAMENTO,
	NVL(FORN.CODIGO_FORNECEDOR, 0) AS CODIGO_FORNECEDOR,
	NVL(FORN.FORNECEDOR, 'SEM FORNECEDOR') AS FORNECEDOR,
	I.SEQPRODUTO AS CODIGO_PRODUTO,
	P.DESCCOMPLETA AS DESCRICAO_PRODUTO,
	ROUND(NVL(I.QUANTIDADE, 0), 2) AS QUANTIDADE_NF,
	ROUND(NVL(I.VLRITEM, 0), 2) AS VALOR_PRODUTO_NF
FROM MLFV_BASENFE N
INNER JOIN MFLV_BASEDFITEM I
	ON I.NROEMPRESA = N.NROEMPRESA
   AND I.SEQNF = N.SEQNF
   AND I.TIPNOTAFISCAL = N.TIPNOTAFISCAL
   AND I.SERIEDF = N.SERIENF
   AND I.NUMERODF = N.NUMERONF
   AND I.SEQPESSOA = N.SEQPESSOA
INNER JOIN MAX_EMPRESA E
	ON E.NROEMPRESA = N.NROEMPRESA
INNER JOIN MAP_PRODUTO P
	ON P.SEQPRODUTO = I.SEQPRODUTO
LEFT JOIN (
	SELECT
		X.SEQFAMILIA,
		MAX(Y.CATEGORIA) AS DEPARTAMENTO
	FROM MAP_FAMDIVCATEG X
	INNER JOIN MAP_CATEGORIA Y
		ON Y.SEQCATEGORIA = X.SEQCATEGORIA
	WHERE X.NRODIVISAO = 1
	  AND Y.NRODIVISAO = 1
	  AND Y.NIVELHIERARQUIA = 1
	  AND UPPER(Y.CATEGORIA) NOT IN ('A CLASSIFICAR', 'ALMOXARIFADO', 'INATIVAR', 'SERVICOS')
	GROUP BY X.SEQFAMILIA
) DEP
	ON DEP.SEQFAMILIA = P.SEQFAMILIA
LEFT JOIN (
	SELECT
		F.SEQFAMILIA,
		MAX(F.SEQFORNECEDOR) AS CODIGO_FORNECEDOR,
		MAX(G.NOMERAZAO) AS FORNECEDOR
	FROM MAP_FAMFORNEC F
	INNER JOIN GE_PESSOA G
		ON G.SEQPESSOA = F.SEQFORNECEDOR
	WHERE F.PRINCIPAL = 'S'
	GROUP BY F.SEQFAMILIA
) FORN
	ON FORN.SEQFAMILIA = P.SEQFAMILIA
WHERE N.CODGERALOPER = 831
  AND N.TIPNOTAFISCAL = 'S'
  AND NVL(N.MODELO, '0') <> '65'
  AND N.NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18)
  AND N.DTAEMISSAO >= TRUNC(:DT1)
  AND N.DTAEMISSAO < TRUNC(:DT2) + 1
	AND (NVL(TRIM(:LT2), '0') = '0' OR TO_CHAR(NVL(FORN.CODIGO_FORNECEDOR, 0)) = TRIM(:LT2))
	AND (NVL(TRIM(:LT3), 'TODOS') = 'TODOS' OR UPPER(NVL(DEP.DEPARTAMENTO, 'SEM DEPARTAMENTO')) = UPPER(TRIM(:LT3)))
ORDER BY
	N.DTAEMISSAO,
	NUMERO_NF,
	I.SEQPRODUTO
```

Variaveis para cadastrar em Var - F7

DT1
- Tipo: Data
- Descricao: Data Inicial Emissao
- Valor padrao: definir conforme rotina
- Instrucao: informar a data inicial da emissao da NF

DT2
- Tipo: Data
- Descricao: Data Final Emissao
- Valor padrao: data atual
- Instrucao: informar a data final da emissao da NF

LT2
- Tipo: Literal
- Descricao: Codigo Fornecedor
- Valor padrao: 0
- Instrucao: informar o codigo do fornecedor ou usar 0 para considerar todos

LT3
- Tipo: Literal
- Descricao: Departamento
- Valor padrao: TODOS
- Instrucao: informar o nome do departamento exatamente como cadastrado ou usar TODOS

Passo a passo operacional
1. Abrir a consulta na tela Consulta Criacao.
2. Clicar em Var - F7.
3. Cadastrar DT1 na aba Data com descricao Data Inicial Emissao.
4. Cadastrar DT2 na aba Data com descricao Data Final Emissao.
5. Cadastrar LT2 na aba Literal com descricao Codigo Fornecedor.
6. Definir LT2 com valor padrao 0.
7. Cadastrar LT3 na aba Literal com descricao Departamento.
8. Definir LT3 com valor padrao TODOS.
9. Se quiser filtrar, informar o codigo do fornecedor em LT2 e o nome do departamento em LT3.
10. Salvar as variaveis.
11. Executar a consulta e informar os filtros antes do Run.

Observacao
- Os filtros visuais antes do Run nao nascem apenas do SQL; eles dependem do cadastro das variaveis em Var - F7.
- Como o parser da lista de departamento segue falhando nessa tela, foi aplicado o fallback estavel do workspace: departamento por Literal com sentinela TODOS.
- O codigo do fornecedor segue o mesmo padrao estavel do workspace: LT2 literal com sentinela 0 para considerar todos.
- O filtro foi alinhado ao mesmo padrao ja homologado nas consultas do workspace, usando LT3 em vez de LT1.
- Esse caminho elimina a dependencia de SQL dentro da LS1 e reduz o risco de erro de parser no Consinco.
- Como a consulta e de NF de descarte, a obtencao do departamento nao restringe cadastro ativo de familia/categoria.
- A coluna FORNECEDOR foi modelada como fornecedor principal da familia do produto via MAP_FAMFORNEC.
- Se voce quiser o participante da propria NF em vez do fornecedor principal do cadastro, a SQL deve trocar esse join pelo SEQPESSOA da nota.