/**
 * ZONA SQL - Controlador Principal da Aplicação
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Inicializar Módulos
    const editor = new SqlEditorManager('sql-editor', 'line-numbers', 'editor-cursor-pos', 'editor-char-count');
    const mentor = new ConsincoMentor(editor);
    const missions = new MissionsManager(editor);

    // 2. Estado Global
    let currentResults = null;
    let tablesData = [];

    // 3. Snippets Consinco Homologados
    const snippets = [
        {
            title: 'Bypass Consinco (SELECT * FROM WITH)',
            desc: 'Estrutura obrigatória para passar no validador da Consulta Criação',
            sql: `SELECT * FROM (
    WITH CTE_DADOS AS (
        SELECT /*+ MATERIALIZE */
            A.SEQPRODUTO,
            A.DESCCOMPLETA,
            B.ESTQLOJA
        FROM MAP_PRODUTO A
        INNER JOIN MRL_PRODUTOEMPRESA B ON A.SEQPRODUTO = B.SEQPRODUTO
        WHERE B.NROEMPRESA = :NROEMPRESA
          AND B.STATUSCOMPRA = 'A'
    )
    SELECT * FROM CTE_DADOS
)`
        },
        {
            title: 'Preço Vigente (Promocional vs Normal)',
            desc: 'Cálculo de preço oficial com NVL e NULLIF',
            sql: `SELECT
    A.SEQPRODUTO,
    A.DESCCOMPLETA,
    P.PRECOVALIDNORMAL,
    P.PRECOVALIDPROMOC,
    NVL(NULLIF(P.PRECOVALIDPROMOC, 0), P.PRECOVALIDNORMAL) AS PRECO_PRATICADO
FROM MAP_PRODUTO A
INNER JOIN MRL_PRODEMPSEG P ON A.SEQPRODUTO = P.SEQPRODUTO
WHERE P.NROEMPRESA = :NROEMPRESA
  AND P.STATUSVENDA = 'A'`
        },
        {
            title: 'Join Seguro de Embalagem (QTD=1)',
            desc: 'Evita multiplicação de linhas com MAP_FAMEMBALAGEM',
            sql: `SELECT
    A.SEQPRODUTO,
    A.DESCCOMPLETA,
    E.EMBALAGEM,
    E.QTDEMBALAGEM
FROM MAP_PRODUTO A
LEFT JOIN MAP_FAMEMBALAGEM E ON A.SEQFAMILIA = E.SEQFAMILIA AND E.QTDEMBALAGEM = 1`
        },
        {
            title: 'Vendas Oficiais (MRL_CUSTODIA)',
            desc: 'Agregação prévia de vendas sem multiplicar saldo de estoque',
            sql: `SELECT * FROM (
    WITH VENDAS_AGREGADAS AS (
        SELECT /*+ MATERIALIZE */
            SEQPRODUTO,
            NROEMPRESA,
            SUM(QTDVDA) AS TOTAL_QTD_VENDIDA
        FROM MRL_CUSTODIA
        WHERE NROEMPRESA = :NROEMPRESA
          AND DTAENTRADASAIDA BETWEEN :DT1 AND :DT2
        GROUP BY SEQPRODUTO, NROEMPRESA
    )
    SELECT
        P.SEQPRODUTO,
        P.DESCCOMPLETA,
        E.ESTQLOJA,
        NVL(V.TOTAL_QTD_VENDIDA, 0) AS QTD_VENDIDA_PERIODO
    FROM MAP_PRODUTO P
    INNER JOIN MRL_PRODUTOEMPRESA E ON P.SEQPRODUTO = E.SEQPRODUTO AND E.NROEMPRESA = :NROEMPRESA
    LEFT JOIN VENDAS_AGREGADAS V ON P.SEQPRODUTO = V.SEQPRODUTO AND E.NROEMPRESA = V.NROEMPRESA
    ORDER BY QTD_VENDIDA_PERIODO DESC
)`
        },
        {
            title: 'Filtro Dinâmico Var - F7 (Fornecedor)',
            desc: 'Parametrização opcional com :NR1 e TO_NUMBER',
            sql: `SELECT
    A.SEQPRODUTO,
    A.DESCCOMPLETA,
    F.NOMERAZAO AS FORNECEDOR,
    B.PRCBASE
FROM MAP_PRODUTO A
INNER JOIN MRL_PRODUTOEMPRESA B ON A.SEQPRODUTO = B.SEQPRODUTO
INNER JOIN MAP_FAMFORNEC FF ON A.SEQFAMILIA = FF.SEQFAMILIA AND FF.PRINCIPAL = 'S'
INNER JOIN GE_PESSOA F ON FF.SEQPESSOA = F.SEQPESSOA
WHERE B.NROEMPRESA = :NROEMPRESA
  AND (TO_NUMBER(NVL(:NR1, 0)) = 0 OR F.SEQPESSOA = TO_NUMBER(:NR1))`
        }
    ];

    function renderSnippets() {
        const container = document.getElementById('snippets-list');
        let html = '';
        snippets.forEach((s, idx) => {
            html += `
                <div class="snippet-card" data-idx="${idx}">
                    <div class="snippet-title">💡 ${s.title}</div>
                    <div class="snippet-desc">${s.desc}</div>
                </div>
            `;
        });
        container.innerHTML = html;

        container.querySelectorAll('.snippet-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const idx = parseInt(e.currentTarget.getAttribute('data-idx'));
                editor.setValue(snippets[idx].sql);
            });
        });
    }

    renderSnippets();

    // 4. Carregar Lista de Tabelas Ativas com Dados
    async function loadTables() {
        const container = document.getElementById('tables-list');
        try {
            const resp = await fetch('/api/tables');
            const data = await resp.json();
            tablesData = data.tables || [];
            renderTablesList(tablesData);
        } catch (err) {
            container.innerHTML = `<div class="log-entry log-error">Erro ao carregar tabelas: ${err.message}</div>`;
        }
    }

    function renderTablesList(tables) {
        const container = document.getElementById('tables-list');
        if (!tables.length) {
            container.innerHTML = '<p class="text-muted" style="padding: 10px;">Nenhuma tabela encontrada.</p>';
            return;
        }

        // Agrupar por prefixo (MAP, MRL, MAX, GE, MBI, MAD, FI, MSU, MLF)
        const groups = {};
        tables.forEach(t => {
            const prefix = t.name.split('_')[0] || 'OUTROS';
            if (!groups[prefix]) groups[prefix] = [];
            groups[prefix].push(t);
        });

        let html = '';
        for (const [prefix, tbls] of Object.entries(groups)) {
            html += `
                <div class="table-module-group">
                    <div class="module-title">
                        <span>${prefix} (${tbls.length})</span>
                    </div>
                    ${tbls.map(t => `
                        <div class="table-item-card" data-tbl="${t.name}">
                            <div class="table-info-left">
                                <span class="tbl-name">${t.name}</span>
                            </div>
                            <div class="tbl-actions">
                                <span class="tbl-count-badge">${t.row_count} lin</span>
                                <button class="btn-icon-mini btn-view-tbl" title="Ver estrutura e amostra" data-tbl="${t.name}">👁️</button>
                                <button class="btn-icon-mini btn-insert-tbl" title="Gerar SELECT * no editor" data-tbl="${t.name}">📝</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        container.innerHTML = html;
        initTableCardEvents();
    }

    function initTableCardEvents() {
        // Clique no card ou botão de gerar SELECT
        document.querySelectorAll('.btn-insert-tbl').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const tbl = e.currentTarget.getAttribute('data-tbl');
                editor.setValue(`SELECT *\nFROM ${tbl}\nLIMIT 50`);
                document.getElementById('btn-run-query').click();
            });
        });

        // Ver Estrutura
        document.querySelectorAll('.btn-view-tbl, .table-item-card').forEach(elem => {
            elem.addEventListener('click', (e) => {
                if (e.target.classList.contains('btn-insert-tbl')) return;
                const tbl = elem.getAttribute('data-tbl');
                openTableModal(tbl);
            });
        });
    }

    // Filtro de busca de tabelas
    document.getElementById('search-tables-input').addEventListener('input', (e) => {
        const query = e.target.value.trim().toUpperCase();
        if (!query) {
            renderTablesList(tablesData);
        } else {
            const filtered = tablesData.filter(t => t.name.includes(query));
            renderTablesList(filtered);
        }
    });

    // 5. Busca no Dicionário Completo (4.515 Tabelas)
    const dictInput = document.getElementById('search-dict-input');
    const dictResults = document.getElementById('dict-results');

    async function searchDictionary() {
        const query = dictInput.value.trim();
        if (!query) return;

        dictResults.innerHTML = '<div class="loading-spinner">🔍 Buscando no catálogo Consinco...</div>';

        try {
            const resp = await fetch(`/api/search_dictionary?q=${encodeURIComponent(query)}`);
            const data = await resp.json();
            const results = data.results || [];

            if (!results.length) {
                dictResults.innerHTML = '<div class="empty-state"><p>Nenhum resultado encontrado no dicionário.</p></div>';
                return;
            }

            let html = '';
            results.forEach(r => {
                html += `
                    <div class="dict-item">
                        <div class="dict-header">
                            <span class="dict-tab">${r.tabela}</span>
                            <span class="dict-col">${r.coluna}</span>
                            <span class="dict-type">${r.tipo || ''}</span>
                        </div>
                        <div class="dict-desc">${r.descricao || 'Sem descrição cadastrada'}</div>
                    </div>
                `;
            });

            dictResults.innerHTML = html;
        } catch (err) {
            dictResults.innerHTML = `<div class="log-entry log-error">Erro na busca: ${err.message}</div>`;
        }
    }

    document.getElementById('btn-search-dict').addEventListener('click', searchDictionary);
    dictInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') searchDictionary();
    });

    // 6. Var - F7 Drawer
    const varf7Drawer = document.getElementById('varf7-drawer');
    document.getElementById('btn-toggle-varf7').addEventListener('click', () => {
        varf7Drawer.classList.toggle('collapsed');
    });
    document.getElementById('btn-close-varf7').addEventListener('click', () => {
        varf7Drawer.classList.add('collapsed');
    });
    document.getElementById('btn-reset-varf7').addEventListener('click', () => {
        document.getElementById('bind-NROEMPRESA').value = '1';
        document.getElementById('bind-NR1').value = '';
        document.getElementById('bind-LS1').value = '0 - TODOS';
        document.getElementById('bind-DT1').value = '2026-08-01';
        document.getElementById('bind-DT2').value = '2026-08-21';
        document.getElementById('bind-LT1').value = '';
    });

    function getBindsFromDrawer() {
        return {
            'NROEMPRESA': parseInt(document.getElementById('bind-NROEMPRESA').value) || 1,
            'NR1': parseInt(document.getElementById('bind-NR1').value) || 0,
            'LS1': document.getElementById('bind-LS1').value || '0 - TODOS',
            'DT1': document.getElementById('bind-DT1').value || '2026-08-01',
            'DT2': document.getElementById('bind-DT2').value || '2026-08-21',
            'LT1': document.getElementById('bind-LT1').value || ''
        };
    }

    // 7. Execução de Consulta SQL
    document.getElementById('btn-run-query').addEventListener('click', async () => {
        const sql = editor.getValue().trim();
        if (!sql) {
            alert("Por favor, digite uma consulta SQL.");
            return;
        }

        const binds = getBindsFromDrawer();
        const gridContainer = document.getElementById('grid-table-container');
        gridContainer.innerHTML = '<div class="loading-spinner">⚡ Executando consulta no motor Oracle/Consinco...</div>';

        const timePill = document.getElementById('exec-time-pill');
        const timeVal = document.getElementById('exec-time-val');
        const countSpan = document.getElementById('res-count');
        const jsonViewer = document.getElementById('json-viewer');
        const logsContainer = document.getElementById('logs-container');

        try {
            const resp = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql, binds })
            });
            const data = await resp.json();
            currentResults = data;

            // Atualizar tempo de execução
            timePill.style.display = 'inline-flex';
            timeVal.textContent = data.execution_time_ms || 0;

            if (data.success) {
                countSpan.textContent = data.row_count;
                renderDataGrid(data.columns, data.rows);
                jsonViewer.textContent = JSON.stringify(data.rows, null, 2);

                // Adicionar log de sucesso
                const log = document.createElement('div');
                log.className = 'log-entry log-info';
                log.textContent = `[SUCCESS] ${data.row_count} registros retornados em ${data.execution_time_ms} ms.`;
                logsContainer.appendChild(log);
            } else {
                countSpan.textContent = 0;
                gridContainer.innerHTML = `
                    <div class="empty-grid-msg">
                        <div class="empty-icon" style="color: #ef4444;">⚠️</div>
                        <h3 style="color: #ef4444;">Falha na Execução</h3>
                        <p style="font-family: var(--font-mono); font-size: 0.82rem; margin-top: 6px; color: #fca5a5;">${data.error}</p>
                    </div>
                `;
                jsonViewer.textContent = JSON.stringify(data, null, 2);

                // Alternar para a aba de logs
                const log = document.createElement('div');
                log.className = 'log-entry log-error';
                log.textContent = `[ERRO] ${data.error}`;
                logsContainer.appendChild(log);
            }

            // Atualizar linter com os alertas retornados
            if (data.alerts) {
                mentor.renderAlerts(data.alerts);
            }
        } catch (err) {
            gridContainer.innerHTML = `<div class="log-entry log-error">Erro de comunicação com o servidor: ${err.message}</div>`;
        }
    });

    function renderDataGrid(columns, rows) {
        const container = document.getElementById('grid-table-container');
        if (!rows || !rows.length) {
            container.innerHTML = `
                <div class="empty-grid-msg">
                    <div class="empty-icon">🔍</div>
                    <h3>Nenhum registro encontrado</h3>
                    <p>A consulta foi executada com sucesso, mas a condição WHERE não encontrou registros correspondentes.</p>
                </div>
            `;
            return;
        }

        let html = '<table class="data-grid"><thead><tr>';
        columns.forEach(c => {
            html += `<th>${c}</th>`;
        });
        html += '</tr></thead><tbody>';

        rows.forEach(r => {
            html += '<tr>';
            r.forEach(cell => {
                let cellVal = cell === null ? '<span style="color:#6b7280; font-style:italic;">NULL</span>' : cell;
                // Se for float formatar com 2 casas
                if (typeof cell === 'number' && !Number.isInteger(cell)) {
                    cellVal = cell.toFixed(2);
                }
                html += `<td>${cellVal}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    // 8. Exportar CSV e Copiar Tabela
    document.getElementById('btn-export-csv').addEventListener('click', () => {
        if (!currentResults || !currentResults.rows || !currentResults.rows.length) {
            alert("Nenhum dado para exportar.");
            return;
        }

        const cols = currentResults.columns;
        const rows = currentResults.rows;
        let csvContent = "data:text/csv;charset=utf-8," + cols.join(';') + "\n";

        rows.forEach(r => {
            csvContent += r.map(c => (c === null ? '' : `"${c}"`)).join(';') + "\n";
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `consulta_consinco_${new Date().getTime()}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    document.getElementById('btn-copy-table').addEventListener('click', () => {
        if (!currentResults || !currentResults.rows || !currentResults.rows.length) {
            alert("Nenhum dado para copiar.");
            return;
        }

        const cols = currentResults.columns;
        const rows = currentResults.rows;
        let text = cols.join('\t') + '\n';
        rows.forEach(r => {
            text += r.map(c => (c === null ? '' : c)).join('\t') + '\n';
        });

        navigator.clipboard.writeText(text).then(() => {
            alert("Dados copiados para a área de transferência (formato TSV para Excel)!");
        });
    });

    // 9. Alternância de Abas
    // Sidebars Tabs
    document.querySelectorAll('.tab-pills').forEach(pillGroup => {
        pillGroup.querySelectorAll('.tab-pill').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetId = e.currentTarget.getAttribute('data-tab');
                const parent = e.currentTarget.closest('.sidebar-left, .sidebar-right');
                
                parent.querySelectorAll('.tab-pill').forEach(p => p.classList.remove('active'));
                parent.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

                e.currentTarget.classList.add('active');
                const targetContent = document.getElementById(targetId);
                if (targetContent) targetContent.classList.add('active');
            });
        });
    });

    // Results Tabs
    document.querySelectorAll('.res-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const targetId = e.currentTarget.getAttribute('data-res');
            document.querySelectorAll('.res-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.res-view').forEach(v => v.classList.remove('active'));

            e.currentTarget.classList.add('active');
            document.getElementById(targetId).classList.add('active');
        });
    });

    // 10. Modal de Detalhes da Tabela
    const modal = document.getElementById('table-modal');
    const modalClose = document.getElementById('modal-close');
    const modalColsTable = document.getElementById('modal-cols-table');
    const modalSampleTable = document.getElementById('modal-sample-table');
    let activeModalTable = '';

    modalClose.addEventListener('click', () => modal.classList.remove('active'));

    // Modal Tabs
    document.querySelectorAll('.modal-tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            const targetId = e.currentTarget.getAttribute('data-mtab');
            document.querySelectorAll('.modal-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.mtab-content').forEach(c => c.classList.remove('active'));

            e.currentTarget.classList.add('active');
            document.getElementById(targetId).classList.add('active');
        });
    });

    async function openTableModal(tableName) {
        activeModalTable = tableName;
        document.getElementById('modal-table-title').textContent = `Tabela: ${tableName}`;
        modal.classList.add('active');

        modalColsTable.innerHTML = '<div class="loading-spinner">Carregando estrutura...</div>';
        modalSampleTable.innerHTML = '<div class="loading-spinner">Carregando amostra...</div>';

        try {
            const resp = await fetch(`/api/table/${tableName}`);
            const data = await resp.json();

            // Renderizar Colunas
            let colsHtml = '<table class="data-grid"><thead><tr><th>#</th><th>Coluna</th><th>Tipo</th><th>PK</th></tr></thead><tbody>';
            data.columns.forEach(c => {
                colsHtml += `<tr><td>${c.cid}</td><td style="color:#93c5fd; font-weight:600;">${c.name}</td><td>${c.type}</td><td>${c.pk ? '🔑 SIM' : ''}</td></tr>`;
            });
            colsHtml += '</tbody></table>';
            modalColsTable.innerHTML = colsHtml;

            // Renderizar Amostra
            if (data.sample_rows && data.sample_rows.length) {
                let sampleHtml = '<table class="data-grid"><thead><tr>';
                data.sample_columns.forEach(col => sampleHtml += `<th>${col}</th>`);
                sampleHtml += '</tr></thead><tbody>';
                data.sample_rows.forEach(r => {
                    sampleHtml += '<tr>';
                    r.forEach(val => sampleHtml += `<td>${val === null ? 'NULL' : val}</td>`);
                    sampleHtml += '</tr>';
                });
                sampleHtml += '</tbody></table>';
                modalSampleTable.innerHTML = sampleHtml;
            } else {
                modalSampleTable.innerHTML = '<p class="text-muted" style="padding:10px;">Sem registros de amostra.</p>';
            }
        } catch (err) {
            modalColsTable.innerHTML = `<div class="log-entry log-error">Erro ao carregar dados: ${err.message}</div>`;
        }
    }

    document.getElementById('btn-modal-insert-select').addEventListener('click', () => {
        if (activeModalTable) {
            editor.setValue(`SELECT *\nFROM ${activeModalTable}\nLIMIT 50`);
            modal.classList.remove('active');
            document.getElementById('btn-run-query').click();
        }
    });

    // Carregar tabelas inicialmente
    loadTables();
});
