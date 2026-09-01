/**
 * ZONA SQL - Autocomplete & IntelliSense Profissional (Estilo VS Code)
 * Suporte a:
 * - Palavras-chave e cláusulas multi-palavras (INNER JOIN, GROUP BY, UNION ALL)
 * - Aliases com ponto (ex: p.seq -> sugere p.SEQPRODUTO)
 * - Tabelas e Colunas oficiais Consinco
 * - Funções nativas Oracle (NVL, TO_CHAR, TO_DATE, DECODE, etc.)
 * - Binds de tela Var-F7 (:NROEMPRESA, :NR1, etc.)
 * - Snippets de performance (Bypass CTE, etc.)
 */

class SqlAutocompleteManager {
    constructor(editorManager) {
        this.editorManager = editorManager;
        this.textarea = editorManager.textarea;

        this.dropdown = null;
        this.suggestions = [];
        this.selectedIndex = -1;
        this.currentQuery = '';
        this.prefixToKeep = '';
        this.wordStartPos = 0;
        this.wordEndPos = 0;
        this.isVisible = false;
        this.cachedCharWidth = null;

        this.dictionary = [];
        this.initDictionary();
        this.createDropdownElement();
        this.bindEvents();
    }

    initDictionary() {
        const keywords = [
            { text: 'SELECT', desc: 'Cláusula de projeção de colunas' },
            { text: 'FROM', desc: 'Cláusula de origem de dados / tabelas' },
            { text: 'WHERE', desc: 'Filtro de registros' },
            { text: 'INNER JOIN', desc: 'Junção interna estrita' },
            { text: 'LEFT JOIN', desc: 'Junção externa esquerda (traz nulos)' },
            { text: 'RIGHT JOIN', desc: 'Junção externa direita' },
            { text: 'FULL JOIN', desc: 'Junção externa completa' },
            { text: 'CROSS JOIN', desc: 'Produto cartesiano' },
            { text: 'ON', desc: 'Condição de ligação do JOIN' },
            { text: 'GROUP BY', desc: 'Agrupamento de agregações' },
            { text: 'ORDER BY', desc: 'Ordenação de resultados' },
            { text: 'HAVING', desc: 'Filtro sobre agregações' },
            { text: 'INSERT INTO', desc: 'Inserção de novos registros' },
            { text: 'UPDATE', desc: 'Atualização de registros existentes' },
            { text: 'DELETE FROM', desc: 'Remoção de registros' },
            { text: 'MERGE INTO', desc: 'Upsert (Update / Insert sincronizado)' },
            { text: 'UNION ALL', desc: 'União rápida sem remover duplicados' },
            { text: 'UNION', desc: 'União com remoção de duplicados' },
            { text: 'WITH', desc: 'Common Table Expression (CTE)' },
            { text: '/*+ MATERIALIZE */', desc: 'Hint Oracle obrigatório em CTEs Consinco' },
            { text: 'DISTINCT', desc: 'Elimina linhas duplicadas' },
            { text: 'AS', desc: 'Alias de coluna ou tabela' },
            { text: 'AND', desc: 'Operador lógico E' },
            { text: 'OR', desc: 'Operador lógico OU' },
            { text: 'NOT', desc: 'Negação lógica' },
            { text: 'IN', desc: 'Pertencimento a conjunto de valores' },
            { text: 'NOT IN', desc: 'Não pertencimento a conjunto' },
            { text: 'LIKE', desc: 'Busca por padrão com % ou _' },
            { text: 'IS NULL', desc: 'Verificação de valor nulo' },
            { text: 'IS NOT NULL', desc: 'Verificação de valor não nulo' },
            { text: 'BETWEEN', desc: 'Intervalo inclusivo' },
            { text: 'EXISTS', desc: 'Verificação de existência em subquery' },
            { text: 'NOT EXISTS', desc: 'Verificação de inexistência' },
            { text: 'CASE WHEN', desc: 'Estrutura condicional CASE' },
            { text: 'THEN', desc: 'Resultado da condição CASE' },
            { text: 'ELSE', desc: 'Fallback padrão da condição CASE' },
            { text: 'END', desc: 'Fechamento do bloco CASE' },
            { text: 'SET', desc: 'Atribuição de valores no UPDATE' },
            { text: 'VALUES', desc: 'Valores para o INSERT' },
            { text: 'USING', desc: 'Origem de dados do MERGE' },
            { text: 'WHEN MATCHED THEN', desc: 'Ramo de atualização do MERGE' },
            { text: 'WHEN NOT MATCHED THEN', desc: 'Ramo de inserção do MERGE' },
            { text: 'ROWNUM', desc: 'Pseudo-coluna de número da linha Oracle' },
            { text: 'DUAL', desc: 'Tabela virtual padrão do Oracle' },
            { text: 'DESC', desc: 'Ordenação decrescente' },
            { text: 'ASC', desc: 'Ordenação crescente' }
        ];

        const functions = [
            { text: 'NVL(', display: 'NVL(expr1, default_val)', desc: 'Substitui NULL por um valor padrão' },
            { text: 'NVL2(', display: 'NVL2(expr, val_se_nao_nulo, val_se_nulo)', desc: 'Condicional de nulo Oracle' },
            { text: 'TO_CHAR(', display: 'TO_CHAR(val, fmt)', desc: 'Converte número/data para texto formatado' },
            { text: 'TO_DATE(', display: "TO_DATE(str, 'YYYY-MM-DD')", desc: 'Converte texto em data Oracle' },
            { text: 'TO_NUMBER(', display: 'TO_NUMBER(str)', desc: 'Converte texto em número' },
            { text: 'TRUNC(', display: 'TRUNC(date_or_num)', desc: 'Trunca casas decimais ou horas de data' },
            { text: 'SUBSTR(', display: 'SUBSTR(str, pos, len)', desc: 'Extrai fatia de string' },
            { text: 'INSTR(', display: 'INSTR(str, substr)', desc: 'Localiza posição do texto' },
            { text: 'DECODE(', display: 'DECODE(val, s1, r1, default)', desc: 'Condicional inline decode Oracle' },
            { text: 'NULLIF(', display: 'NULLIF(v1, v2)', desc: 'Retorna NULL se v1 == v2' },
            { text: 'COALESCE(', display: 'COALESCE(v1, v2, ...)', desc: 'Retorna o primeiro valor não nulo' },
            { text: 'LPAD(', display: "LPAD(str, len, '0')", desc: 'Preenche à esquerda com zeros/espaços' },
            { text: 'RPAD(', display: "RPAD(str, len, ' ')", desc: 'Preenche à direita' },
            { text: 'ROUND(', display: 'ROUND(num, dec)', desc: 'Arredonda valor numérico' },
            { text: 'TRIM(', display: 'TRIM(str)', desc: 'Remove espaços extras das extremidades' },
            { text: 'UPPER(', display: 'UPPER(str)', desc: 'Converte texto para MAIÚSCULAS' },
            { text: 'LOWER(', display: 'LOWER(str)', desc: 'Converte texto para minúsculas' },
            { text: 'REPLACE(', display: 'REPLACE(str, search, repl)', desc: 'Substitui texto em string' },
            { text: 'SYSDATE', display: 'SYSDATE', desc: 'Data e hora atual do banco Oracle' },
            { text: 'SUM(', display: 'SUM(coluna)', desc: 'Soma agregada de valores' },
            { text: 'COUNT(', display: 'COUNT(*)', desc: 'Contagem de linhas' },
            { text: 'AVG(', display: 'AVG(coluna)', desc: 'Média aritmética' },
            { text: 'MIN(', display: 'MIN(coluna)', desc: 'Valor mínimo' },
            { text: 'MAX(', display: 'MAX(coluna)', desc: 'Valor máximo' },
            { text: 'ROW_NUMBER() OVER(', display: 'ROW_NUMBER() OVER(PARTITION BY ... ORDER BY ...)', desc: 'Numeração analítica de linhas' },
            { text: 'DENSE_RANK() OVER(', display: 'DENSE_RANK() OVER(ORDER BY ...)', desc: 'Ranking analítico sem saltos' }
        ];

        const tables = [
            { text: 'MAP_PRODUTO', desc: 'Cadastro Oficial Geral de Produtos Consinco' },
            { text: 'MRL_PRODUTOEMPRESA', desc: 'Estoque de Loja, Depósito e Custo Médio por Empresa' },
            { text: 'MRL_PONTOEXTRA', desc: 'Cadastro de Capa de Pontas de Gôndola e Ilhas' },
            { text: 'MRL_PONTOEXTRAPRODUTO', desc: 'Vínculo Produto x Ponto Extra' },
            { text: 'MRL_PONTOEXTRAPRODUTOEMPRESA', desc: 'Parâmetros Mín/Máx/Vigência de Pontas por Loja' },
            { text: 'MAX_EMPRESA', desc: 'Cadastro de Lojas e Centros de Distribuição (CD 16, CD 50)' },
            { text: 'MAX_COMPRADOR', desc: 'Cadastro de Compradores Comerciais' },
            { text: 'MAP_FAMILIA', desc: 'Famílias de Produtos e Tributação Base' },
            { text: 'MAP_CATEGORIA', desc: 'Departamentos, Seções e Categorias de Produtos' },
            { text: 'MAP_FAMDIVCATEG', desc: 'Vínculo de Família com Categoria Mercadológica' },
            { text: 'MAP_FAMFORNEC', desc: 'Fornecedor Principal e Secundários da Família' },
            { text: 'MAP_FAMEMBALAGEM', desc: 'Embalagens de Comercialização do Produto' },
            { text: 'MAP_PRODCODIGO', desc: 'Códigos de Barras EAN 13, DUN 14 e PLU' },
            { text: 'GE_PESSOA', desc: 'Cadastro Geral de Fornecedores, Clientes e Parceiros' },
            { text: 'MRL_PRODEMPSEG', desc: 'Preços de Venda Normal, Promocional e Status Venda' },
            { text: 'MRL_CUSTODIA', desc: 'Apuração Analítica de Vendas e Custos Fiscais Diários' },
            { text: 'MRL_PRODVENDADIA', desc: 'Resumo Diário de Vendas por Loja e Produto' },
            { text: 'FI_TITULO', desc: 'Contas a Pagar e Receber (Financeiro Consinco)' },
            { text: 'FI_TITCOMPRADOR', desc: 'Vínculo de Títulos com Comprador Comercial' },
            { text: 'MSU_PEDIDOSUPRIM', desc: 'Pedidos de Compra e Suprimento Comercial' },
            { text: 'MSU_PSITEMRECEBER', desc: 'Itens de Pedidos Pendentes de Recebimento' },
            { text: 'MSU_PSITEMEXPEDIDO', desc: 'Itens de Pedidos Expedidos' },
            { text: 'MBI_TABCDISTRIB', desc: 'Parâmetros de Curva ABC e Distribuição' }
        ];

        const columns = [
            { text: 'SEQPRODUTO', desc: 'ID Único do Produto (Chave Primária Consinco)' },
            { text: 'SEQPONTOEXTRA', desc: 'ID Único da Ponta de Gôndola / Ponto Extra' },
            { text: 'NROEMPRESA', desc: 'Número da Filial / Loja (1 a 18, 50)' },
            { text: 'DESCCOMPLETA', desc: 'Descrição Completa Oficial do Produto' },
            { text: 'DESCREDUZIDA', desc: 'Descrição Abreviada para Cupom / PDV' },
            { text: 'SEQFAMILIA', desc: 'Código Sequencial da Família do Produto' },
            { text: 'SEQCATEGORIA', desc: 'Código da Categoria Mercadológica' },
            { text: 'SEQPESSOA', desc: 'Código Sequencial do Fornecedor / Pessoa' },
            { text: 'NROCOMPRADOR', desc: 'Número do Comprador Responsável' },
            { text: 'ESTQMINIMO', desc: 'Estoque Mínimo Parametrizado' },
            { text: 'ESTQMAXIMO', desc: 'Estoque Máximo Parametrizado' },
            { text: 'DTAVIGENCIAINICIO', desc: 'Data Inicial de Vigência (YYYY-MM-DD)' },
            { text: 'DTAVIGENCIAFIM', desc: 'Data Final de Vigência (YYYY-MM-DD)' },
            { text: 'ESTQLOJA', desc: 'Saldo de Estoque Físico na Área de Venda' },
            { text: 'ESTQDEPOSITO', desc: 'Saldo de Estoque Físico no Depósito' },
            { text: 'PRCBASE', desc: 'Preço Base de Custo / Compra' },
            { text: 'CMULTCUSLIQUIDOEMP', desc: 'Custo Médio Líquido da Empresa' },
            { text: 'STATUSCOMPRA', desc: "Status de Compra do Item ('A'=Ativo, 'I'=Inativo)" },
            { text: 'STATUSVENDA', desc: "Status de Comercialização ('A'=Ativo, 'I'=Inativo)" },
            { text: 'PRECOVALIDNORMAL', desc: 'Preço de Venda Praticado Normal' },
            { text: 'PRECOVALIDPROMOC', desc: 'Preço de Venda Praticado Promocional' },
            { text: 'CODACESSO', desc: 'Código EAN / Barras / Acesso do Item' },
            { text: 'TIPCODIGO', desc: "Tipo do Código ('E'=EAN, 'D'=DUN, 'B'=Balança)" },
            { text: 'QTDEMBALAGEM', desc: 'Quantidade de Unidades na Embalagem' },
            { text: 'NOMERAZAO', desc: 'Razão Social / Nome Completo' },
            { text: 'FANTASIA', desc: 'Nome Fantasia da Empresa ou Parceiro' },
            { text: 'CGC', desc: 'CNPJ da Empresa ou Parceiro' },
            { text: 'CGCCPF', desc: 'CNPJ ou CPF do Fornecedor / Cliente' },
            { text: 'DTAENTRADASAIDA', desc: 'Data de Movimentação Fiscal' },
            { text: 'VLRTOTALVDA', desc: 'Valor Total Faturado de Venda' },
            { text: 'QTDVDA', desc: 'Quantidade Total Vendida' },
            { text: 'CODGERALOPER', desc: 'Código Geral de Operação (CGO Consinco)' },
            { text: 'STATUS', desc: "Status do Registro ('A'=Ativo, 'I'=Inativo)" },
            { text: 'SEQVIGENCIA', desc: 'Número Sequencial da Vigência (Padrão 1)' },
            { text: 'QTDDIASSUGESTAO', desc: 'Dias de Sugestão de Reposição' },
            { text: 'FAMILIA', desc: 'Nome da Família de Produtos' },
            { text: 'PESAVEL', desc: "Indicador de Produto Pesável ('S'/'N')" },
            { text: 'CATEGORIA', desc: 'Nome da Categoria' },
            { text: 'NIVELHIERARQUIA', desc: 'Nível Hierárquico da Categoria' },
            { text: 'PRINCIPAL', desc: "Indicador de Fornecedor Principal ('S'/'N')" },
            { text: 'SEQTITULO', desc: 'Sequencial do Título Financeiro' },
            { text: 'DTOVENCIMENTO', desc: 'Data de Vencimento do Título' },
            { text: 'VLRORIGINAL', desc: 'Valor Original do Documento' },
            { text: 'VLRLIQUIDO', desc: 'Valor Líquido a Pagar / Receber' },
            { text: 'NROPEDIDOSUPRIM', desc: 'Número do Pedido de Suprimento' },
            { text: 'DTAPEDIDO', desc: 'Data de Emissão do Pedido' }
        ];

        const binds = [
            { text: ':NROEMPRESA', desc: 'Variável Var-F7: Número da Filial Selecionada' },
            { text: ':NR1', desc: 'Variável Var-F7: Código do Fornecedor ou Produto' },
            { text: ':LS1', desc: 'Variável Var-F7: Lista de Seleção (Comprador/Segmento)' },
            { text: ':DT1', desc: 'Variável Var-F7: Data Inicial do Filtro' },
            { text: ':DT2', desc: 'Variável Var-F7: Data Final do Filtro' },
            { text: ':LT1', desc: 'Variável Var-F7: Lista de Texto (Ex: BEBIDAS)' },
            { text: ':LT2', desc: 'Variável Var-F7: Lista de Texto Secundária' },
            { text: ':LT3', desc: 'Variável Var-F7: Lista de Multi-Valores com INSTR' }
        ];

        const snippets = [
            {
                text: 'SELECT * FROM (\n    WITH CTE_DADOS AS (\n        SELECT /*+ MATERIALIZE */\n            A.SEQPRODUTO,\n            A.DESCCOMPLETA\n        FROM MAP_PRODUTO A\n    )\n    SELECT * FROM CTE_DADOS\n)',
                display: '⚡ CTE Materializada (Bypass Consinco)',
                desc: 'Estrutura oficial para CTE passar no validador do ERP'
            },
            {
                text: 'INNER JOIN MAP_PRODUTO PROD ON PROD.SEQPRODUTO = A.SEQPRODUTO',
                display: '🔗 JOIN MAP_PRODUTO',
                desc: 'Junção com o cadastro principal de produtos'
            },
            {
                text: 'INNER JOIN MRL_PRODUTOEMPRESA PE ON PE.SEQPRODUTO = A.SEQPRODUTO AND PE.NROEMPRESA = A.NROEMPRESA',
                display: '🔗 JOIN MRL_PRODUTOEMPRESA',
                desc: 'Junção por produto e filial para saldo de estoque'
            },
            {
                text: 'INNER JOIN MAX_EMPRESA EMP ON EMP.NROEMPRESA = A.NROEMPRESA',
                display: '🔗 JOIN MAX_EMPRESA',
                desc: 'Junção com a tabela de filiais'
            },
            {
                text: 'NVL(NULLIF(P.PRECOVALIDPROMOC, 0), P.PRECOVALIDNORMAL) AS PRECO_PRATICADO',
                display: '💲 Preço Praticado (Promo vs Normal)',
                desc: 'Fallback seguro de preço vigente'
            },
            {
                text: 'INSTR(\',\' || UPPER(REPLACE(:LT3, \' \', \'\')) || \',\', \',\' || UPPER(TRIM(COLUNA)) || \',\') > 0',
                display: '🔍 Multi-Valores Var-F7 via INSTR',
                desc: 'Filtro seguro para lista de strings separadas por vírgula'
            }
        ];

        this.dictionary = [
            ...keywords.map(k => ({ type: 'keyword', icon: '⚡', label: k.text, text: k.text, desc: k.desc })),
            ...functions.map(f => ({ type: 'function', icon: '🛠️', label: f.display, text: f.text, desc: f.desc })),
            ...tables.map(t => ({ type: 'table', icon: '📊', label: t.text, text: t.text, desc: t.desc })),
            ...columns.map(c => ({ type: 'column', icon: '🔹', label: c.text, text: c.text, desc: c.desc })),
            ...binds.map(b => ({ type: 'bind', icon: '⚙️', label: b.text, text: b.text, desc: b.desc })),
            ...snippets.map(s => ({ type: 'snippet', icon: '💡', label: s.display, text: s.text, desc: s.desc }))
        ];
    }

    addCustomTable(tableName, desc = 'Tabela Oficial Consinco') {
        if (!this.dictionary.some(d => d.text === tableName)) {
            this.dictionary.push({
                type: 'table',
                icon: '📊',
                label: tableName,
                text: tableName,
                desc: desc
            });
        }
    }

    createDropdownElement() {
        // Dropdown fixado no body para não ser cortado por overflow
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'sql-autocomplete-dropdown';
        this.dropdown.style.display = 'none';
        document.body.appendChild(this.dropdown);
    }

    bindEvents() {
        // Monitorar digitação
        this.textarea.addEventListener('input', () => {
            this.handleInput();
        });

        // Monitorar teclas especiais (Setas, Tab, Enter, Esc, Ctrl+Space)
        this.textarea.addEventListener('keydown', (e) => {
            if (this.isVisible) {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.navigateSuggestions(1);
                    return;
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    this.navigateSuggestions(-1);
                    return;
                } else if (e.key === 'Tab' || e.key === 'Enter') {
                    if (this.selectedIndex >= 0 && this.suggestions[this.selectedIndex]) {
                        e.preventDefault();
                        this.applySuggestion(this.suggestions[this.selectedIndex]);
                        return;
                    }
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    this.hide();
                    return;
                }
            } else if (e.ctrlKey && e.code === 'Space') {
                e.preventDefault();
                this.handleInput(true);
            }
        });

        // Fechar ao clicar fora
        document.addEventListener('mousedown', (e) => {
            if (this.dropdown && !this.dropdown.contains(e.target) && e.target !== this.textarea) {
                this.hide();
            }
        });

        // Reposicionar ao rolar
        this.textarea.addEventListener('scroll', () => {
            if (this.isVisible) {
                this.updateDropdownPosition();
            }
        });

        window.addEventListener('resize', () => {
            if (this.isVisible) {
                this.updateDropdownPosition();
            }
        });
    }

    handleInput(forceOpen = false) {
        const cursorPos = this.textarea.selectionStart;
        const text = this.textarea.value;

        // Texto antes do cursor
        const textBeforeCursor = text.substring(0, cursorPos);
        
        // Identificar termo antes do cursor, suportando prefixo com ponto (ex: p.seq, a.nro, cdia.qtd)
        const match = textBeforeCursor.match(/([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]*)|:[a-zA-Z0-9_]*|[a-zA-Z0-9_]+)$/);

        if (!match && !forceOpen) {
            this.hide();
            return;
        }

        const fullToken = match ? match[1] : '';
        let query = fullToken;
        let prefix = '';

        // Se houver alias com ponto (ex: p.seq ou a.)
        if (fullToken.includes('.')) {
            const parts = fullToken.split('.');
            prefix = parts[0] + '.';
            query = parts[1] || '';
        }

        this.currentQuery = query;
        this.prefixToKeep = prefix;
        this.wordStartPos = cursorPos - query.length;
        this.wordEndPos = cursorPos;

        // Regras de disparo:
        // - Se tiver ponto (ex: p.), abre com query >= 0
        // - Se começar com ':' (bind), abre com query >= 1
        // - Senão abre com query >= 2 letras ou forceOpen
        const shouldOpen = forceOpen ||
            (prefix && query.length >= 0) ||
            (fullToken.startsWith(':') && fullToken.length >= 1) ||
            (query.length >= 2);

        if (shouldOpen) {
            const filtered = this.filterSuggestions(query, fullToken);
            if (filtered.length > 0) {
                this.suggestions = filtered;
                this.selectedIndex = 0;
                this.renderDropdown();
                this.updateDropdownPosition();
                this.show();
            } else {
                this.hide();
            }
        } else {
            this.hide();
        }
    }

    filterSuggestions(query, fullToken) {
        const q = query.toUpperCase();
        const fullUpper = (fullToken || '').toUpperCase();

        const exactPrefix = [];
        const contains = [];

        // Se o usuário está digitando após um alias (ex: p.), priorizar colunas
        const isAfterDot = Boolean(this.prefixToKeep);

        for (const item of this.dictionary) {
            const itemKey = (item.text || item.label).toUpperCase();
            
            // Se for após ponto, filtrar apenas colunas ou funções
            if (isAfterDot && item.type !== 'column' && item.type !== 'function') {
                continue;
            }

            if (!q) {
                exactPrefix.push(item);
                continue;
            }

            if (itemKey.startsWith(q)) {
                exactPrefix.push(item);
            } else if (itemKey.includes(q) || item.label.toUpperCase().includes(q)) {
                contains.push(item);
            }
        }

        return [...exactPrefix, ...contains].slice(0, 9);
    }

    renderDropdown() {
        this.dropdown.innerHTML = '';
        this.suggestions.forEach((item, index) => {
            const itemEl = document.createElement('div');
            itemEl.className = `sql-ac-item ${index === this.selectedIndex ? 'selected' : ''}`;
            
            const highlightedLabel = this.highlightMatch(item.label, this.currentQuery);

            itemEl.innerHTML = `
                <div class="sql-ac-left">
                    <span class="sql-ac-icon">${item.icon}</span>
                    <span class="sql-ac-label">${highlightedLabel}</span>
                    <span class="sql-ac-badge badge-${item.type}">${item.type.toUpperCase()}</span>
                </div>
                <div class="sql-ac-desc">${item.desc || ''}</div>
            `;

            itemEl.addEventListener('mouseenter', () => {
                this.selectedIndex = index;
                this.updateSelectionVisuals();
            });

            itemEl.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this.applySuggestion(item);
            });

            this.dropdown.appendChild(itemEl);
        });
    }

    highlightMatch(text, query) {
        if (!query) return text;
        const qUpper = query.toUpperCase();
        const tUpper = text.toUpperCase();
        const idx = tUpper.indexOf(qUpper);
        if (idx === -1) return text;

        const start = text.substring(0, idx);
        const match = text.substring(idx, idx + query.length);
        const end = text.substring(idx + query.length);
        return `${start}<mark class="ac-highlight">${match}</mark>${end}`;
    }

    navigateSuggestions(direction) {
        if (!this.suggestions.length) return;
        this.selectedIndex = (this.selectedIndex + direction + this.suggestions.length) % this.suggestions.length;
        this.updateSelectionVisuals();
    }

    updateSelectionVisuals() {
        const items = this.dropdown.querySelectorAll('.sql-ac-item');
        items.forEach((it, idx) => {
            if (idx === this.selectedIndex) {
                it.classList.add('selected');
                it.scrollIntoView({ block: 'nearest' });
            } else {
                it.classList.remove('selected');
            }
        });
    }

    applySuggestion(item) {
        const text = this.textarea.value;
        const before = text.substring(0, this.wordStartPos);
        const after = text.substring(this.wordEndPos);
        
        let insertion = item.text;

        this.textarea.value = before + insertion + after;
        
        // Ajustar cursor
        let newCursorPos = this.wordStartPos + insertion.length;
        this.textarea.selectionStart = this.textarea.selectionEnd = newCursorPos;
        this.textarea.focus();

        this.editorManager.updateLineNumbers();
        this.editorManager.updateStats();
        this.textarea.dispatchEvent(new Event('input'));

        this.hide();
    }

    updateDropdownPosition() {
        const text = this.textarea.value;
        const selStart = this.textarea.selectionStart;
        const textBefore = text.substring(0, selStart);
        const lines = textBefore.split('\n');
        const lineIndex = lines.length - 1;
        const currentLineText = lines[lineIndex];
        const colIndex = currentLineText.length;

        const rect = this.textarea.getBoundingClientRect();
        const style = window.getComputedStyle(this.textarea);
        const paddingLeft = parseFloat(style.paddingLeft) || 12;
        const paddingTop = parseFloat(style.paddingTop) || 10;
        const lineHeight = parseFloat(style.lineHeight) || 23.2;

        if (!this.cachedCharWidth) {
            const testSpan = document.createElement('span');
            testSpan.style.font = style.font;
            testSpan.style.fontFamily = style.fontFamily;
            testSpan.style.fontSize = style.fontSize;
            testSpan.style.visibility = 'hidden';
            testSpan.style.position = 'absolute';
            testSpan.textContent = 'MMMMMMMMMM';
            document.body.appendChild(testSpan);
            this.cachedCharWidth = testSpan.getBoundingClientRect().width / 10;
            testSpan.remove();
        }
        const charWidth = this.cachedCharWidth || 8.5;

        let top = rect.top + paddingTop + (lineIndex * lineHeight) - this.textarea.scrollTop + lineHeight + 4;
        let left = rect.left + paddingLeft + (colIndex * charWidth) - this.textarea.scrollLeft;

        // Limites de tela para manter o popup sempre visível
        const maxLeft = window.innerWidth - 380;
        const maxTop = window.innerHeight - 260;
        left = Math.max(10, Math.min(left, maxLeft));

        if (top > maxTop || top > rect.bottom - 30) {
            top = Math.max(10, rect.top + paddingTop + (lineIndex * lineHeight) - this.textarea.scrollTop - 245);
        }

        this.dropdown.style.top = `${top}px`;
        this.dropdown.style.left = `${left}px`;
    }

    show() {
        this.dropdown.style.display = 'flex';
        this.isVisible = true;
    }

    hide() {
        if (this.dropdown) {
            this.dropdown.style.display = 'none';
        }
        this.isVisible = false;
        this.suggestions = [];
        this.selectedIndex = -1;
    }
}

window.SqlAutocompleteManager = SqlAutocompleteManager;
